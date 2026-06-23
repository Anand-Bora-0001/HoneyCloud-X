from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
from datetime import datetime, timezone, timedelta

# ========================
# ORGANIZATION / TENANT
# ========================

class Organization(Base):
    """Multi-tenant organization model"""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Subscription details
    plan = Column(String(50), default="free")  # free, starter, professional, enterprise
    plan_started_at = Column(DateTime(timezone=True), server_default=func.now())
    plan_expires_at = Column(DateTime(timezone=True), nullable=True)
    is_trial = Column(Boolean, default=True)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    
    # Limits based on plan
    max_services = Column(Integer, default=1)  # free: 1, starter: 5, pro: 20, enterprise: unlimited
    max_events_per_month = Column(Integer, default=1000)
    max_users = Column(Integer, default=1)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_suspended = Column(Boolean, default=False)
    
    # Billing
    stripe_customer_id = Column(String(255), nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="organization")
    services = relationship("Service", back_populates="organization")
    events = relationship("AttackEvent", back_populates="organization")
    notifications = relationship("NotificationConfig", back_populates="organization")
    
    def __repr__(self):
        return f"<Organization {self.name} - {self.plan}>"
    
    def is_plan_active(self):
        """Check if subscription is active"""
        if self.is_suspended:
            return False
        if self.is_trial and self.trial_ends_at:
            return datetime.now(timezone.utc) < self.trial_ends_at
        if self.plan_expires_at:
            return datetime.now(timezone.utc) < self.plan_expires_at
        return True

# ========================
# USER MODEL (Enhanced)
# ========================

class User(Base):
    """User model with organization relationship"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Organization relationship
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    organization = relationship("Organization", back_populates="users")
    
    # Role within organization
    role = Column(String(50), default="member")  # owner, admin, member, viewer
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # First-time login tracking
    is_first_login = Column(Boolean, default=True)
    telegram_configured = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<User {self.username} - {self.organization.name}>"

# ========================
# SERVICE MODEL
# ========================

class Service(Base):
    """Individual service/application being monitored"""
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    organization = relationship("Organization", back_populates="services")
    
    # Service details
    name = Column(String(255), nullable=False)
    slug = Column(String(100), index=True, nullable=False)
    description = Column(Text, nullable=True)
    service_type = Column(String(50), default="web")  # web, api, mobile, iot
    
    # API Key for this service
    api_key = Column(String(255), unique=True, index=True, nullable=False)
    
    # Configuration
    webhook_url = Column(String(500), nullable=True)
    alert_threshold = Column(String(20), default="HIGH")  # Only alert on HIGH/CRITICAL
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_event_at = Column(DateTime(timezone=True), nullable=True)
    
    # Stats
    total_events = Column(Integer, default=0)
    critical_events = Column(Integer, default=0)
    
    # Relationships
    events = relationship("AttackEvent", back_populates="service")
    
    def __repr__(self):
        return f"<Service {self.name} - {self.organization.name}>"

# ========================
# ATTACK EVENT (Enhanced)
# ========================

class AttackEvent(Base):
    __tablename__ = "attack_events"
    __table_args__ = (
        Index('ix_events_org_timestamp', 'organization_id', 'timestamp'),
        Index('ix_events_org_severity', 'organization_id', 'severity'),
        Index('ix_events_ip_timestamp', 'source_ip', 'timestamp'),
        Index('ix_events_org_service', 'organization_id', 'service_name'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Multi-tenant relationships
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    organization = relationship("Organization", back_populates="events")
    
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    service = relationship("Service", back_populates="events")
    
    # Attack details
    service_name = Column(String(100), index=True)  # For backward compatibility
    source_ip = Column(String(45), index=True)
    source_port = Column(Integer)
    endpoint = Column(String(500), nullable=True)
    method = Column(String(10), nullable=True)
    username = Column(String(255), nullable=True)
    password = Column(String(255), nullable=True)
    payload = Column(Text, nullable=True)
    command = Column(String(500), nullable=True)
    
    # Severity classification
    severity = Column(String(20), index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    
    # AI/ML predictions
    ai_label = Column(String(20), nullable=True)  # benign, anomaly, malicious
    threat_score = Column(Float, default=0.0)
    
    # Additional metadata
    location = Column(JSON, nullable=True)
    user_agent = Column(String(500), nullable=True)
    event_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' to avoid SQLAlchemy conflict
    
    # Notification tracking
    notification_sent = Column(Boolean, default=False)
    
    # Soft Deletes
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<AttackEvent {self.id} - {self.service_name} from {self.source_ip}>"

# ========================
# NOTIFICATION CONFIG
# ========================

class NotificationConfig(Base):
    """Notification settings per organization"""
    __tablename__ = "notification_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    organization = relationship("Organization", back_populates="notifications")
    
    # Notification channels
    email_enabled = Column(Boolean, default=True)
    email_addresses = Column(JSON, default=list)  # List of emails
    
    telegram_enabled = Column(Boolean, default=False)
    telegram_bot_token = Column(String(255), nullable=True)
    telegram_chat_id = Column(String(255), nullable=True)
    
    slack_enabled = Column(Boolean, default=False)
    slack_webhook_url = Column(String(500), nullable=True)
    
    webhook_enabled = Column(Boolean, default=False)
    webhook_url = Column(String(500), nullable=True)
    
    # Alert settings
    alert_on_critical = Column(Boolean, default=True)
    alert_on_high = Column(Boolean, default=True)
    alert_on_medium = Column(Boolean, default=False)
    alert_on_low = Column(Boolean, default=False)
    
    # Rate limiting
    max_alerts_per_hour = Column(Integer, default=10)
    
    # Report preferences
    daily_summary_enabled = Column(Boolean, default=False)
    weekly_report_enabled = Column(Boolean, default=False)
    
    # Notification stats
    email_alerts_sent = Column(Integer, default=0)
    telegram_alerts_sent = Column(Integer, default=0)
    failed_deliveries = Column(Integer, default=0)
    last_email_sent_at = Column(DateTime(timezone=True), nullable=True)
    last_telegram_sent_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<NotificationConfig for {self.organization.name}>"

# ========================
# SUBSCRIPTION PLANS
# ========================

class SubscriptionPlan(Base):
    """Available subscription plans"""
    __tablename__ = "subscription_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # free, starter, professional, enterprise
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Pricing
    price_monthly = Column(Float, default=0.0)
    price_yearly = Column(Float, default=0.0)
    currency = Column(String(3), default="USD")
    
    # Limits
    max_services = Column(Integer, default=1)
    max_events_per_month = Column(Integer, default=1000)
    max_users = Column(Integer, default=1)
    data_retention_days = Column(Integer, default=30)
    
    # Features
    features = Column(JSON, default=list)
    
    # Stripe integration
    stripe_price_id_monthly = Column(String(255), nullable=True)
    stripe_price_id_yearly = Column(String(255), nullable=True)
    
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<SubscriptionPlan {self.display_name}>"

# ========================
# BILLING HISTORY
# ========================

class BillingHistory(Base):
    """Track billing transactions"""
    __tablename__ = "billing_history"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Transaction details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    plan = Column(String(50), nullable=False)
    billing_period = Column(String(20), nullable=False)  # monthly, yearly
    
    # Payment details
    payment_method = Column(String(50), nullable=True)  # stripe, paypal, etc.
    transaction_id = Column(String(255), nullable=True)
    stripe_invoice_id = Column(String(255), nullable=True)
    
    # Status
    status = Column(String(50), default="pending")  # pending, completed, failed, refunded
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<BillingHistory {self.transaction_id} - {self.amount} {self.currency}>"


# ========================
# PHASE 1: DECEPTION ENGINE MODELS
# ========================

class AttackerProfile(Base):
    __tablename__ = "attacker_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    source_ip = Column(String(45), unique=True, index=True, nullable=False)
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Intelligence Stats
    total_attacks = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)
    average_threat_score = Column(Float, default=0.0)
    risk_category = Column(String(20), default="UNKNOWN")  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Top targets/payloads (Stored as JSON for simplicity: e.g. {"/admin": 50, "/.env": 20})
    most_targeted_endpoints = Column(JSON, default=dict)
    most_common_payloads = Column(JSON, default=dict)
    
    # Phase 3: Advanced Intelligence
    persona = Column(String(50), default="Scanner")
    confidence_score = Column(Float, default=0.0)
    behavior_summary = Column(Text, nullable=True)
    
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Soft Deletes
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<AttackerProfile {self.source_ip} - {self.risk_category}>"


class DeceptionSession(Base):
    __tablename__ = "deception_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    source_ip = Column(String(45), index=True, nullable=False)
    user_agent = Column(String(500), nullable=True)
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    
    threat_score = Column(Float, default=0.0)
    risk_level = Column(String(20), default="LOW")
    status = Column(String(20), default="ACTIVE")  # ACTIVE, CLOSED, ESCALATED
    recommended_route = Column(String(20), default="CONTINUE")  # CONTINUE, DECEPTION, BLOCK
    
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    actions = relationship("DeceptionAction", back_populates="session", cascade="all, delete-orphan")

    # Soft Deletes
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<DeceptionSession {self.session_id}>"


class DeceptionAction(Base):
    __tablename__ = "deception_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("deception_sessions.session_id"), index=True, nullable=False)
    
    action_type = Column(String(50), index=True, nullable=False)  # VISIT, SQLI_ATTEMPT, etc.
    endpoint = Column(String(500), nullable=True)
    method = Column(String(10), nullable=True)
    payload = Column(Text, nullable=True)
    
    threat_score = Column(Float, default=0.0)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    session = relationship("DeceptionSession", back_populates="actions")

    def __repr__(self):
        return f"<DeceptionAction {self.action_type} on {self.endpoint}>"


# ========================
# PHASE 3: ADAPTIVE DECEPTION MODELS
# ========================

class DeceptionScenario(Base):
    __tablename__ = "deception_scenarios"
    
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    trigger_patterns = Column(JSON, default=list)  # e.g. ["wp-admin", "phpmyadmin"]
    risk_level = Column(String(20), default="HIGH")
    priority = Column(Integer, default=10)
    enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<DeceptionScenario {self.name}>"


class FakeAsset(Base):
    """Represents a fake file or honey token exposed in a scenario"""
    __tablename__ = "fake_assets"
    
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(String(100), ForeignKey("deception_scenarios.scenario_id"))
    
    asset_type = Column(String(50))  # FILE, CREDENTIAL, URL
    name = Column(String(255))
    content = Column(Text, nullable=True)
    is_honey_token = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FileUploadAttempt(Base):
    """Metadata for files attackers attempt to upload to the trap"""
    __tablename__ = "file_upload_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("deception_sessions.session_id"))
    
    filename = Column(String(500))
    file_hash = Column(String(255))  # SHA-256
    size = Column(Integer)
    mime_type = Column(String(100))
    attacker_ip = Column(String(45))
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

# ========================
# PHASE 4: THREAT INTELLIGENCE & INVESTIGATION
# ========================

class ThreatCampaign(Base):
    """Correlates multiple attacker profiles into a single organized campaign"""
    __tablename__ = "threat_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    name = Column(String(255), nullable=False)  # e.g., "Automated WordPress Scanner Group"
    description = Column(Text, nullable=True)
    confidence_score = Column(Float, default=0.0)
    
    # Common Indicators
    common_personas = Column(JSON, default=list)
    common_endpoints = Column(JSON, default=list)
    common_payloads = Column(JSON, default=list)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Soft Deletes
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class InvestigationReport(Base):
    """Contains the generated Threat Narrative, MITRE mapping, and attack path analysis"""
    __tablename__ = "investigation_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    attacker_profile_id = Column(Integer, ForeignKey("attacker_profiles.id"), unique=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Generated Narratives
    summary_narrative = Column(Text, nullable=True)
    executive_summary = Column(Text, nullable=True)
    technical_summary = Column(Text, nullable=True)
    
    # Analysis Artifacts
    mitre_mapping = Column(JSON, default=dict)  # {"T1110": "Brute Force", ...}
    attack_paths = Column(JSON, default=list)   # [{"from": "/admin", "to": "/fake-admin", "time": ...}]
    risk_evolution_trend = Column(JSON, default=dict) # {"trend": "Escalating", "sessions": [...]}
    
    # Aggregated Evidence
    evidence_summary = Column(JSON, default=dict) # {"total_sessions": 14, "honey_tokens": 8}
    
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Soft Deletes
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

# ========================
# AUDIT LOGGING
# ========================

class AuditLog(Base):
    """Tracks cleanup, reset, and critical administrative actions"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # User who performed the action
    
    action = Column(String(255), nullable=False)  # e.g., "Clear Demo Data", "Empty Recycle Bin"
    records_removed = Column(Integer, default=0)
    details = Column(JSON, nullable=True)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AuditLog {self.action} at {self.timestamp}>"
