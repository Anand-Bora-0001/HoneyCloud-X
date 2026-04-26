
# 🍯 HoneyCloud-X

### **AI-Powered Cloud Honeypot Platform for Next-Generation Cyber Threat Intelligence**

![Version](https://img.shields.io/badge/version-2.0.0-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)

> **Detect. Analyze. Respond.** — A smart, scalable honeypot platform that leverages Machine Learning, Deep Learning, and real-time Threat Intelligence to trap, monitor, and neutralize cyber attacks before they reach production systems.

---

[Features](#-key-features) · [Architecture](#-system-architecture) · [Quick Start](#-quick-start) · [Attack Simulations](#-attack-simulation-engine) · [Tech Stack](#-technology-stack) · [Deployment](#-deployment) · [Impact](#-real-world-impact) · [Contributing](#-contributing)

</div>

---

## 📖 What is HoneyCloud-X?

**HoneyCloud-X** is a full-stack, AI-driven honeypot-as-a-service platform designed to **proactively detect, classify, and respond to cyber threats** in cloud environments. Unlike traditional honeypots that simply log connection attempts, HoneyCloud-X deploys an intelligent detection pipeline that combines:

- **Deceptive honeypot services** (SSH, FTP, HTTP, Telnet, E-Commerce) to attract and engage attackers
- **AI/ML-powered threat classification** using Random Forest, Isolation Forest, LSTM, CNN, and Autoencoder models
- **Real-time threat intelligence** with IP reputation scoring, Tor/VPN detection, and abuse database integration
- **Predictive analytics** to forecast emerging attack patterns before they escalate
- **Automated incident response** that blocks malicious IPs and triggers multi-channel alerts (Telegram, Email)

The platform is built as a **multi-tenant SaaS** with role-based access control, subscription management, and a real-time monitoring dashboard — making it suitable for both individual researchers and enterprise security operations centers (SOCs).

---

## 🎯 Main Motive & Why This Project?

### The Problem

Cloud infrastructure faces an ever-growing landscape of cyber threats. Traditional security tools are **reactive** — they detect attacks only _after_ damage is done. Most organizations lack the resources to deploy sophisticated deception technology, and existing honeypot solutions are either too simplistic (basic logging) or too complex (require expert DevOps knowledge).

### The Solution

HoneyCloud-X bridges this gap by providing:

| Problem | HoneyCloud-X Solution |
|---|---|
| Reactive security posture | **Proactive** threat detection via deceptive honeypots |
| Manual threat analysis | **AI-automated** classification with 90%+ confidence |
| Siloed threat data | **Centralized** dashboard with real-time streaming |
| Delayed incident response | **Automated** response within seconds (IP blocking, alerting) |
| No predictive capability | **Predictive analytics** with 7-day attack forecasting |
| Expensive enterprise tools | **Open-source** and self-hostable with SaaS pricing tiers |
| Fragmented alert channels | **Multi-channel** notifications (Telegram, Email, Webhook, Slack) |

### Key Objectives

1. **Early Threat Detection** — Identify attacks in their reconnaissance phase, before they reach production assets
2. **AI-Driven Intelligence** — Replace manual log analysis with ML models that learn and adapt
3. **Actionable Insights** — Provide security teams with clear, prioritized threat intelligence
4. **Accessible Security** — Make enterprise-grade deception technology available to everyone
5. **Research & Education** — Enable cybersecurity students and researchers to study real attack patterns safely

---

## ✨ Key Features

### 🔬 Core Honeypot Services

| Service | Port | Attack Types Simulated | Detection Capability |
|---|---|---|---|
| **SSH Honeypot** | 22 | Brute force, credential stuffing, command injection | Full credential + command logging |
| **FTP Honeypot** | 21 | Anonymous login, file theft, malware upload | File operation tracking |
| **HTTP Honeypot** | 80 | Admin panel probes, web scanning, SQLi, XSS | Endpoint fingerprinting |
| **Telnet Honeypot** | 23 | Device exploitation, config theft, DoS | Network device emulation |
| **E-Commerce Honeypot** | 5000 | Login brute force, XSS, directory traversal | Full web app simulation |

### 🤖 AI & Machine Learning Engine

- **Random Forest Classifier** — Multi-class threat classification with TF-IDF feature extraction, SMOTE balancing, and GridSearchCV hyperparameter tuning
- **Isolation Forest** — Unsupervised anomaly detection for zero-day threat identification
- **LSTM Neural Network** — Sequence-based attack pattern recognition for predicting attack escalation
- **CNN Threat Detector** — Convolutional neural network for payload pattern recognition
- **Autoencoder Anomaly Detector** — Deep learning anomaly detection using reconstruction error analysis

### 🛡️ Advanced Threat Intelligence

- **IP Reputation Scoring** — Multi-source reputation analysis (AbuseIPDB, geolocation, ISP risk profiling)
- **Tor Exit Node Detection** — Real-time identification of anonymized traffic
- **VPN/Proxy Detection** — Flag traffic from known VPN and proxy providers
- **Attack Pattern Analyzer** — Regex-based detection for SQL injection, XSS, path traversal, and command injection patterns
- **MITRE ATT&CK Mapping** — Every detected attack is mapped to MITRE ATT&CK framework techniques

### 🔎 Threat Hunting & Automated Response

| Hunting Rule | MITRE ID | Detection Logic |
|---|---|---|
| Credential Stuffing | T1110.004 | >20 login attempts with >10 unique usernames from same IP |
| Living Off The Land (LOLBins) | T1059 | Detects PowerShell, cmd, certutil, bitsadmin, etc. in commands |
| Lateral Movement | T1021 | Single IP accessing 3+ different honeypot services |

- **Automated IP Blocking** — Critical-severity attackers are instantly blocked
- **Security Audit Logging** — Full audit trail with 90-day retention
- **Indicator of Compromise (IOC) Management** — Track and cross-reference IOCs

### 📊 Real-Time Dashboard & Analytics

- **Live Attack Map** — Real-time geographic visualization of attack origins
- **Attack Timeline** — Chronological event stream with severity filtering
- **Service Distribution Charts** — Breakdown of attacks by honeypot service
- **AI Prediction Confidence Visualizations** — ML model confidence scores for each event
- **Predictive Forecasting** — 7-day attack volume predictions with confidence intervals
- **Executive Summary Reports** — Business intelligence with risk scoring and actionable recommendations

### 📱 Multi-Channel Alerting

- **Telegram Bot** — Instant alerts with formatted attack details and PDF report attachments
- **Email (SMTP)** — Configurable email alerts with severity-based filtering
- **Webhook Support** — Custom webhook integrations for third-party SIEM/SOAR tools
- **Slack Integration** — Native Slack webhook notifications
- **Rate-Limited Alerts** — Configurable cooldown (5-min default) to prevent alert fatigue

### 📑 Export & Reporting

- **PDF Reports** — Professional threat assessment documents generated with ReportLab
- **CSV Export** — Raw event data export for offline analysis
- **Excel Reports** — Formatted spreadsheets with charts and summary sheets (OpenPyXL)
- **Executive Summaries** — Auto-generated BI reports with risk scoring and recommendations

### 🏢 Multi-Tenant SaaS Architecture

- **Organization Management** — Multi-tenant isolation with dedicated data partitioning
- **Role-Based Access Control (RBAC)** — Owner, Admin, Member, Viewer roles
- **Subscription Plans** — Free, Starter, Professional, Enterprise tiers
- **API Key Management** — Per-service API keys for secure honeypot integration
- **Billing & Stripe Integration** — Subscription lifecycle management

---

## 🏗️ System Architecture

```
                     ┌──────────────────────────────────────────────────┐
                     │              ATTACKER / SIMULATION                │
                     └────────┬──────────┬───────────┬──────────────────┘
                              │          │           │
                     SSH:22  FTP:21  HTTP:80  TELNET:23  DEMO:5000
                              │          │           │         │
                     ┌────────▼──────────▼───────────▼─────────▼────────┐
                     │               HoneyCloud-X Backend                │
                     │           FastAPI — Port 8000                     │
                     │                                                   │
                     │  ┌──────────────┐  ┌───────────────────────┐     │
                     │  │ /api/ingest  │  │  Threat Intelligence  │     │
                     │  │  (PUBLIC)    │──│  Engine                │     │
                     │  └──────────────┘  └───────────────────────┘     │
                     │         │                                         │
                     │  ┌──────▼────────────────────────────────┐       │
                     │  │  AI / ML Pipeline                     │       │
                     │  │  ├── Random Forest (scikit-learn)     │       │
                     │  │  ├── Isolation Forest (anomaly)       │       │
                     │  │  ├── LSTM (TensorFlow/Keras)          │       │
                     │  │  ├── CNN (pattern recognition)        │       │
                     │  │  └── Autoencoder (anomaly detection)  │       │
                     │  └───────────────────────────────────────┘       │
                     │         │                                         │
                     │  ┌──────▼──────────────┐                         │
                     │  │  Database Layer      │                         │
                     │  │  SQLite / PostgreSQL │                         │
                     │  └─────────────────────┘                         │
                     │         │                                         │
                     │  ┌──────▼──────────┐  ┌─────────────────┐       │
                     │  │  Alert System   │  │  Report Engine   │       │
                     │  │  • Telegram     │  │  • PDF / CSV     │       │
                     │  │  • Email        │  │  • Excel         │       │
                     │  │  • Webhook      │  │  • BI Summaries  │       │
                     │  └────────────────┘  └─────────────────┘        │
                     │         │                                         │
                     │  ┌──────▼────────────────────────────────┐       │
                     │  │  Advanced Modules                     │       │
                     │  │  ├── Threat Hunter (IOC matching)     │       │
                     │  │  ├── Automated Response (IP blocking) │       │
                     │  │  ├── Predictive Analytics             │       │
                     │  │  ├── Business Intelligence            │       │
                     │  │  ├── Risk Assessment Engine           │       │
                     │  │  ├── Stream Processor (real-time)     │       │
                     │  │  └── Security Audit Logger            │       │
                     │  └───────────────────────────────────────┘       │
                     └──────────────────────────────────────────────────┘
                                         │
                     ┌───────────────────▼─────────────────────────────┐
                     │              Frontend Dashboard                  │
                     │          http://localhost:5173                    │
                     │   Real-time monitoring • Charts • Attack Map     │
                     │   Login / Pricing / Telegram Setup                │
                     └─────────────────────────────────────────────────┘
```

### Event Processing Pipeline

Every attack event flows through a **10-stage detection pipeline**:

```
 1. EVENT ARRIVES    →  POST /api/ingest (public endpoint)
 2. IP ANALYSIS      →  Geolocation + Abuse DB + Tor/VPN check
 3. ML PREDICTION    →  Random Forest threat classification
 4. DEEP LEARNING    →  LSTM + CNN + Autoencoder ensemble
 5. ENRICHMENT       →  Combine all intelligence sources
 6. STREAM PROCESS   →  Real-time coordinated attack detection
 7. DATABASE SAVE    →  Persist to SQLite/PostgreSQL
 8. THREAT HUNTING   →  IOC matching + behavioral analysis
 9. AUTO RESPONSE    →  Block IP if severity is CRITICAL
10. ALERTING         →  Telegram + Email for HIGH/CRITICAL events
```

---

## 🛠️ Technology Stack

### Backend

| Technology | Purpose | Version |
|---|---|---|
| **Python** | Core language | 3.10+ |
| **FastAPI** | Async REST API framework | 0.115.0 |
| **Uvicorn** | ASGI server | 0.30.0 |
| **SQLAlchemy** | ORM & database toolkit | 2.0.31 |
| **Pydantic** | Data validation & settings | 2.8.0 |
| **SSE-Starlette** | Server-Sent Events for real-time streaming | 2.1.2 |

### AI / Machine Learning

| Technology | Purpose | Version |
|---|---|---|
| **scikit-learn** | Random Forest, Isolation Forest, TF-IDF, GridSearchCV | 1.4.0 |
| **TensorFlow** | LSTM, CNN, Autoencoder deep learning models | 2.15.0 |
| **PyTorch** | Alternative deep learning framework | 2.1.2 |
| **XGBoost** | Gradient boosted decision trees | 2.0.2 |
| **LightGBM** | Light gradient boosting | 4.1.0 |
| **CatBoost** | Categorical boosting | 1.2.2 |
| **imbalanced-learn** | SMOTE for class imbalance handling | 0.11.0 |
| **pandas / NumPy** | Data manipulation & numerical computation | 2.1.4 / 1.26.2 |

### Visualization & Reporting

| Technology | Purpose | Version |
|---|---|---|
| **Plotly** | Interactive charts and analytics | 5.17.0 |
| **matplotlib / seaborn** | ML visualization & model evaluation | 3.8.2 / 0.13.0 |
| **ReportLab** | PDF report generation | 4.0.4 |
| **OpenPyXL** | Excel report generation | 3.1.5 |

### Security & Networking

| Technology | Purpose | Version |
|---|---|---|
| **python-jose** | JWT authentication (HS256) | 3.3.0 |
| **bcrypt / passlib** | Password hashing | 4.0.1 / 1.7.4 |
| **cryptography** | Encryption & security primitives | 41.0.8 |
| **pyotp** | Two-factor authentication (TOTP) | 2.9.0 |
| **GeoIP2** | IP geolocation database | 4.7.0 |
| **Scapy** | Network packet analysis | 2.5.0 |

### Infrastructure & DevOps

| Technology | Purpose | Version |
|---|---|---|
| **Docker** | Containerization | latest |
| **Docker Compose** | Multi-service orchestration | 3.x |
| **Nginx** | Frontend reverse proxy | alpine |
| **Redis** | Caching & session management | 7-alpine |
| **PostgreSQL** | Production database (cloud) | 15+ |
| **SQLite** | Development database | built-in |
| **Kubernetes** | Container orchestration (k8s manifests included) | — |
| **Render** | Cloud PaaS deployment | — |

### Frontend

| Technology | Purpose |
|---|---|
| **HTML5 / CSS3 / JavaScript** | Core frontend technologies |
| **Server-Sent Events (SSE)** | Real-time event streaming |
| **Chart.js** | Dashboard visualizations |

### Async & Streaming

| Technology | Purpose | Version |
|---|---|---|
| **aiohttp** | Async HTTP for threat intelligence | 3.9.1 |
| **websockets** | Real-time WebSocket communication | 12.0 |
| **Celery** | Distributed task queue | 5.3.4 |
| **Kafka** | Event stream processing (optional) | confluent-kafka 2.3.0 |
| **Redis** | Message broker & caching | 5.0.1 |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** installed
- **pip** package manager
- **Git** for version control

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/HoneyCloud-X.git
cd HoneyCloud-X
```

### 2. Set Up Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 4. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
# At minimum, set a strong JWT_SECRET_KEY (minimum 32 characters)
```

### 5. Start the Backend

```bash
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Open the Dashboard

Open your browser and navigate to:

| Page | URL |
|---|---|
| **Landing Page** | `http://localhost:5173/` |
| **Dashboard** | `http://localhost:5173/dashboard.html` |
| **Login** | `http://localhost:5173/login.html` |
| **API Docs** | `http://localhost:8000/docs` |

> **Default Credentials:** `admin` / `admin123` (change immediately in production!)

---

## 💣 Attack Simulation Engine

HoneyCloud-X includes a comprehensive attack simulation suite for testing and demonstration. All simulations send events through the same pipeline as real attacks.

### Run All 38+ Attack Simulations

```bash
python run_all_manual_attacks.py
```

### Individual Simulation Scripts

```bash
# Comprehensive simulation (SSH + FTP + HTTP + Telnet + SQLi + traversal)
python backend/scripts/attack_simulation_comprehensive.py

# Honeypot service simulation (SSH + FTP + HTTP + Telnet)
python backend/scripts/honeypot_service_simulator.py

# Demo e-commerce attacks (brute force + XSS + recon + honeypot triggering)
cd demo-ecommerce
python advanced_attack_simulation.py
python monitored_attack_simulation.py
```

### API-Based Simulation

```bash
curl -X POST "http://localhost:8000/api/simulate-attacks?count=30" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Supported Attack Categories

| # | Category | Attacks | MITRE ATT&CK |
|---|---|---|---|
| 1 | SSH Brute Force | 6 credential + command pairs | T1110.001, T1110.004 |
| 2 | FTP Credential Stuffing | 5 anonymous + known creds | T1110.004, T1078 |
| 3 | HTTP Web Probes | 8 admin/config/backup scans | T1190, T1595.002 |
| 4 | Telnet Device Exploitation | 4 Cisco/router attacks | T1021.007, T1110.001 |
| 5 | SQL Injection | 5 UNION/boolean/DROP payloads | T1190, T1059.004 |
| 6 | Directory Traversal | 4 Linux + Windows traversal | T1083, T1005 |
| 7 | E-Commerce (Brute + XSS + Recon) | 10+ mixed web attacks | T1110, T1189, T1595.001 |

### Demo E-Commerce Live Honeypots

The included Flask e-commerce app (`demo-ecommerce/app.py`) deploys **real honeypot endpoints** that detect attacks in real-time:

| Endpoint | Severity | What it Detects |
|---|---|---|
| `/admin`, `/admin/*` | CRITICAL | Admin panel probe |
| `/wp-admin`, `/wp-login.php` | HIGH | WordPress scanning |
| `/.env`, `/.env.backup` | CRITICAL | Environment file exposure |
| `/phpmyadmin`, `/pma` | HIGH | Database management scan |
| `/.git/config`, `/.git/HEAD` | CRITICAL | Source code disclosure |
| `/backup.sql`, `/dump.sql` | CRITICAL | Database backup probe |
| `/api/debug`, `/api/v1/debug` | HIGH | Debug API probe |

---

## 📁 Project Structure

```
HoneyCloud-X/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI application (1900+ lines)
│   │   ├── config.py                  # Centralized configuration management
│   │   ├── models.py                  # SQLAlchemy ORM models (6 tables)
│   │   ├── database.py                # Database connection & initialization
│   │   ├── schemas.py                 # Pydantic schemas for validation
│   │   ├── auth.py                    # JWT authentication & RBAC
│   │   ├── security.py                # Security middleware & utilities
│   │   │
│   │   ├── ml_engine.py               # Random Forest + Isolation Forest ML
│   │   ├── ml_trainer.py              # Background ML training service
│   │   ├── ml_visualizer.py           # Model performance visualization
│   │   ├── deep_learning_engine.py    # LSTM + CNN + Autoencoder models
│   │   │
│   │   ├── threat_intelligence.py     # IP reputation & pattern analysis
│   │   ├── advanced_security.py       # Threat hunting & automated response
│   │   ├── advanced_analytics.py      # Predictive analytics & BI engine
│   │   ├── stream_processor.py        # Real-time event stream processing
│   │   │
│   │   ├── alert_system.py            # Telegram + Email alerting
│   │   ├── telegram_config.py         # Per-org Telegram configuration
│   │   ├── notification_manager.py    # Multi-channel notification routing
│   │   ├── email_service.py           # SMTP email service
│   │   │
│   │   ├── report_generator.py        # PDF / CSV report generation
│   │   ├── excel_export.py            # Excel report generation
│   │   │
│   │   ├── saas_api.py                # Multi-tenant SaaS API endpoints
│   │   ├── subscription_manager.py    # Subscription lifecycle management
│   │   ├── init_saas.py               # SaaS initialization scripts
│   │   │
│   │   ├── production_optimizer.py    # Caching, performance, DB optimization
│   │   ├── database_optimizer.py      # Query optimization & indexing
│   │   ├── metrics_collector.py       # System metrics & monitoring
│   │   └── websocket_manager.py       # WebSocket connection management
│   │
│   ├── scripts/
│   │   ├── attack_simulation_comprehensive.py  # Full attack suite
│   │   └── honeypot_service_simulator.py       # Service-level simulations
│   │
│   ├── tests/                         # Unit & integration tests
│   ├── Dockerfile                     # Backend container image
│   └── requirements.txt              # Python dependencies (80+ packages)
│
├── frontend/
│   ├── index.html                     # Landing page
│   ├── dashboard.html                 # Real-time monitoring dashboard
│   ├── login.html                     # Authentication page
│   ├── pricing.html                   # Subscription plans & pricing
│   ├── telegram-setup.html            # Telegram bot configuration wizard
│   ├── config.js                      # Frontend configuration
│   └── nginx.conf                     # Nginx reverse proxy config
│
├── demo-ecommerce/
│   ├── app.py                         # Flask e-commerce honeypot app
│   ├── honeycloud_client.py           # HoneyCloud integration client
│   ├── advanced_attack_simulation.py  # E-commerce attack simulations
│   └── monitored_attack_simulation.py # Monitored attack scenarios
│
├── k8s/                               # Kubernetes deployment manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   └── namespace.yaml
│
├── docs/                              # Documentation
│   ├── HONEYCLOUD_X_ATTACK_REFERENCE.md   # Complete attack reference guide
│   ├── MANUAL_ATTACKS_GUIDE.md            # Step-by-step attack guides
│   ├── ATTACK_SIMULATION_GUIDE.md         # Simulation instructions
│   ├── TELEGRAM_INTEGRATION.md            # Telegram setup guide
│   └── QUICK_DEMO_STEPS.md               # Quick demo walkthrough
│
├── docker-compose.yml                 # Docker Compose for full stack
├── render.yaml                        # Render.com deployment blueprint
├── run_all_manual_attacks.py          # Master attack simulation script
├── .env.example                       # Environment configuration template
└── setup.sh                           # Quick setup script
```

---

## 🐳 Deployment

### Option 1: Docker Compose (Recommended)

```bash
# Build and start all services
docker compose up --build -d

# Services:
# - Backend API:    http://localhost:8000
# - Frontend:       http://localhost:5173
# - Redis:          localhost:6379
```

### Option 2: Render.com (Cloud PaaS)

The project includes a `render.yaml` blueprint for one-click deployment:

```bash
# Deploys:
# - honeycloud-backend (Python web service)
# - honeycloud-frontend (Static site)
# - honeycloud-redis (Redis instance)
# - honeycloud-db (PostgreSQL database)
```

See [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md) for detailed instructions.

### Option 3: Kubernetes

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### Option 4: Local Development

```bash
# Terminal 1: Backend
python -m uvicorn backend.app.main:app --reload --port 8000

# Terminal 2: Frontend (simple HTTP server)
cd frontend
python -m http.server 5173

# Terminal 3 (optional): Demo E-Commerce
cd demo-ecommerce
pip install -r requirements.txt
python app.py
```

---

## 🔧 Configuration

All configuration is managed via environment variables. Copy `.env.example` to `.env` and customize:

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | Database connection string | `sqlite:///./honeycloud.db` |
| `JWT_SECRET_KEY` | JWT signing key (min 32 chars) | Must be changed! |
| `TELEGRAM_BOT_TOKEN` | Telegram bot API token | — |
| `TELEGRAM_CHAT_ID` | Telegram chat/group ID | — |
| `SMTP_SERVER` | SMTP server for email alerts | `smtp.gmail.com` |
| `ABUSEIPDB_KEY` | AbuseIPDB API key for IP reputation | — |
| `RATE_LIMIT_PER_MINUTE` | API rate limiting | `100` |
| `MAX_ALERTS_PER_HOUR` | Alert rate limiting | `20` |
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

---

## 🌍 Real-World Impact

### Why HoneyCloud-X Matters

| Impact Area | Description |
|---|---|
| **Proactive Defense** | Shifts security from reactive to proactive by detecting attacks during reconnaissance — before they reach production systems |
| **Threat Intelligence** | Generates real, actionable intelligence about attacker TTPs (Tactics, Techniques, Procedures) that can harden defenses |
| **Cost Reduction** | Reduces incident response costs by automating detection and initial response — catching threats in minutes instead of hours |
| **Compliance** | Supports compliance requirements (SOC 2, ISO 27001, NIST) with comprehensive audit logging and reporting |
| **Research** | Provides a safe, controlled environment for studying attack patterns and training ML models on real threat data |
| **Education** | Enables cybersecurity students to understand attack methodologies hands-on without risking real systems |

### By the Numbers

- **7** distinct attack categories with **38+** unique attack simulations
- **5** AI/ML models working in ensemble for threat classification
- **10-stage** detection pipeline processing events in real-time
- **4** notification channels (Telegram, Email, Webhook, Slack)
- **6** database tables supporting full multi-tenant SaaS architecture
- **30+** backend modules spanning intelligent security logic

---

## 📊 Database Schema

```
┌─────────────────┐     ┌───────────────┐     ┌────────────────────┐
│  organizations  │────│    users       │     │ notification_configs│
│                 │     │                │     │                    │
│  id             │     │  id            │     │  id                │
│  name           │     │  username      │     │  telegram_enabled  │
│  slug           │     │  email         │     │  email_enabled     │
│  plan           │     │  role (RBAC)   │     │  slack_enabled     │
│  max_services   │     │  org_id (FK)   │     │  org_id (FK)       │
│  stripe_id      │     │  is_first_login│     │  alert_on_critical │
└────────┬────────┘     └───────────────┘     └────────────────────┘
         │
         │  1:N
         ▼
┌─────────────────┐     ┌───────────────────┐
│    services     │     │  subscription_plans │
│                 │     │                     │
│  id             │     │  id                 │
│  name           │     │  name               │
│  api_key        │     │  price_monthly      │
│  org_id (FK)    │     │  max_services       │
│  total_events   │     │  features (JSON)    │
└────────┬────────┘     └───────────────────┘
         │
         │  1:N
         ▼
┌─────────────────────────┐
│     attack_events       │
│                         │
│  id                     │
│  timestamp              │
│  service_name           │
│  source_ip              │
│  endpoint / method      │
│  username / password    │
│  command / payload      │
│  severity               │
│  ai_label               │
│  threat_score           │
│  location (JSON)        │
│  event_metadata (JSON)  │
│  org_id (FK)            │
│  service_id (FK)        │
└─────────────────────────┘
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test suites
pytest backend/test_ml.py                   # ML engine tests
pytest backend/test_advanced_security.py    # Security module tests
pytest backend/test_risk_assessment.py      # Risk assessment tests

# Run with verbose output
pytest -v --tb=short

# Run performance benchmarks
pytest --benchmark-only
```

---

## 📚 Documentation

| Document | Description |
|---|---|
| [Attack Reference Guide](./docs/HONEYCLOUD_X_ATTACK_REFERENCE.md) | Complete documentation of all 7 attack categories with code walkthroughs |
| [Manual Attacks Guide](./docs/MANUAL_ATTACKS_GUIDE.md) | Step-by-step guide for running attack simulations |
| [Telegram Integration](./docs/TELEGRAM_INTEGRATION.md) | Setting up Telegram bot for alerts |
| [Quick Demo Steps](./docs/QUICK_DEMO_STEPS.md) | Quick demo walkthrough for presentations |
| [Render Deployment](./RENDER_DEPLOYMENT.md) | Cloud deployment on Render.com |
| [API Documentation](http://localhost:8000/docs) | Interactive Swagger UI (when running) |

---

## 🔐 Security Considerations

> ⚠️ **HoneyCloud-X is designed for controlled environments and authorized security testing only.**

- **Change all default credentials** before any deployment
- **Use strong JWT secrets** (minimum 32 characters, cryptographically random)
- **Enable TLS/SSL** in production environments
- **Configure firewall rules** to restrict management access
- **Rotate API keys** regularly
- **Review audit logs** for unauthorized access attempts
- The `/api/ingest` endpoint is **intentionally public** (it's how honeypots send data) — rate limiting is enforced

---

## 🗺️ Roadmap

- [ ] Real-time WebSocket dashboard (replace SSE)
- [ ] Kubernetes Helm charts for production deployment
- [ ] Federated threat intelligence sharing between instances
- [ ] Interactive MITRE ATT&CK Navigator integration
- [ ] Mobile companion app for alerts
- [ ] GraphQL API alongside REST
- [ ] Custom ML model training from the dashboard UI
- [ ] SIEM integration (Splunk, ELK, QRadar)

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

Please ensure your code follows the existing code style and includes appropriate tests.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](./LICENSE) file for details.

---

<div align="center">

**Built with ❤️ for the cybersecurity community**

_HoneyCloud-X — Making the cloud a more dangerous place for attackers._

⭐ Star this repo if you find it useful!

</div>