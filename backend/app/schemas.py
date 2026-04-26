"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# ========================
# ORGANIZATION SCHEMAS
# ========================

class OrganizationCreate(BaseModel):
    name: str
    email: EmailStr
    plan: str = "free"

class OrganizationResponse(BaseModel):
    id: int
    name: str
    slug: str
    email: str
    plan: str
    is_trial: bool
    trial_ends_at: Optional[datetime]
    max_services: int
    max_events_per_month: int
    is_active: bool
    
    class Config:
        from_attributes = True

# ========================
# USER SCHEMAS
# ========================

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    role: str
    is_active: bool
    organization_id: int
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

# ========================
# SERVICE SCHEMAS
# ========================

class ServiceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    service_type: str = "web"
    alert_threshold: str = "HIGH"

class ServiceResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]
    service_type: str
    api_key: str
    is_active: bool
    total_events: int
    critical_events: int
    created_at: datetime
    last_event_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# ========================
# ATTACK EVENT SCHEMAS
# ========================

class AttackEventCreate(BaseModel):
    service_name: str
    source_ip: str
    endpoint: Optional[str] = None
    method: str = "GET"
    severity: str = "MEDIUM"
    username: Optional[str] = None
    password: Optional[str] = None
    command: Optional[str] = None
    payload: Optional[str] = None
    user_agent: Optional[str] = None

class AttackEventResponse(BaseModel):
    id: int
    timestamp: datetime
    service_name: str
    source_ip: str
    endpoint: Optional[str]
    method: Optional[str]
    severity: str
    ai_label: Optional[str]
    threat_score: float
    location: Optional[dict]
    
    class Config:
        from_attributes = True

# ========================
# NOTIFICATION SCHEMAS
# ========================

class NotificationConfigUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    email_addresses: Optional[List[str]] = None
    telegram_enabled: Optional[bool] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    slack_enabled: Optional[bool] = None
    slack_webhook_url: Optional[str] = None
    alert_on_critical: Optional[bool] = None
    alert_on_high: Optional[bool] = None
    alert_on_medium: Optional[bool] = None
    alert_on_low: Optional[bool] = None

class NotificationConfigResponse(BaseModel):
    id: int
    email_enabled: bool
    email_addresses: List[str]
    telegram_enabled: bool
    slack_enabled: bool
    alert_on_critical: bool
    alert_on_high: bool
    alert_on_medium: bool
    alert_on_low: bool
    
    class Config:
        from_attributes = True

# ========================
# SUBSCRIPTION SCHEMAS
# ========================

class SubscriptionPlanResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str]
    price_monthly: float
    price_yearly: float
    currency: str
    max_services: int
    max_events_per_month: int
    max_users: int
    data_retention_days: int
    features: List[str]
    is_active: bool
    
    class Config:
        from_attributes = True

class SubscriptionUpgrade(BaseModel):
    plan: str
    billing_period: str = "monthly"  # monthly or yearly
    payment_method: str = "stripe"

# ========================
# STATISTICS SCHEMAS
# ========================

class DashboardStats(BaseModel):
    total_events: int
    critical_events: int
    high_events: int
    medium_events: int
    low_events: int
    events_today: int
    events_this_week: int
    events_this_month: int
    top_attacked_services: List[dict]
    top_attacker_ips: List[dict]
    recent_events: List[AttackEventResponse]

# ========================
# ORGANIZATION UPDATE
# ========================

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

# ========================
# SERVICE UPDATE
# ========================

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    webhook_url: Optional[str] = None
    alert_threshold: Optional[str] = None

# ========================
# USAGE STATS
# ========================

class UsageStatsResponse(BaseModel):
    services: dict
    events: dict
    users: dict
    plan: str
    is_trial: bool
    trial_ends_at: Optional[str]
    plan_expires_at: Optional[str]

# ========================
# BILLING HISTORY
# ========================

class BillingHistoryResponse(BaseModel):
    id: int
    amount: float
    currency: str
    plan: str
    billing_period: str
    status: str
    created_at: datetime
    paid_at: Optional[datetime]
    
    class Config:
        from_attributes = True
