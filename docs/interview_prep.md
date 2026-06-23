# HoneyCloud-X Technical Interview Preparation Guide

This guide compiles advanced engineering and architectural answers to prepare you for cybersecurity and full-stack software engineering interviews, specifically highlighting the design patterns implemented in HoneyCloud-X.

---

## 1. Why Honeypots?

### Q: Why use honeypots instead of standard firewalls or intrusion detection systems (IDS)?
*   **Zero False Positives:** Firewalls and IDSes trigger thousands of alerts on legitimate traffic (noisy alerts). A honeypot has no operational purpose other than decoy. Therefore, **any** connection or request made to a honeypot is by definition unauthorized, suspicious, or malicious. This filters out 99.9% of operational noise.
*   **Threat Intelligence Gathering:** Rather than just blocking an attack, a honeypot observes the attacker. It logs brute-forced credentials, captures zero-day command payloads, and maps malicious tactics, giving security teams valuable indicators of compromise (IoCs) to defend their production network.
*   **Active Defense & Deception:** Honeypots divert attacker attention away from actual corporate production databases, wasting attacker resources and slowing down scan-and-exploit pipelines.

---

## 2. FastAPI Backend Architecture

### Q: Why did you choose FastAPI over Flask or Django?
*   **Asynchronous Processing:** FastAPI natively supports python `async/await` syntax and executes on `uvicorn` (an ASGI server built on `uvloop`). This makes it highly efficient at handling thousands of simultaneous TCP and HTTP decoy sensor pings concurrently without locking up threads.
*   **Automatic OpenAPI & Validation:** Through integration with `Pydantic`, FastAPI validates all incoming sensor ingestion payloads at the routing layer and generates instant, interactive OpenAPI documentation (`/docs`), speeding up decoy sensor configuration.
*   **Performance:** FastAPI is one of the fastest Python frameworks available, matching Go and NodeJS speeds in benchmark tests because of its lightweight ASGI core.

---

## 3. Threat Intelligence Pipeline

### Q: Explain the lifecycle of an attack event in your system.
1.  **Ingestion:** An edge decoy sensor intercepts an attack (e.g. SSH brute force login attempt) and makes a POST request to `/api/ingest` carrying metadata (timestamps, credentials, payloads).
2.  **Geo-Enrichment:** The backend intercepts the request and resolves the source IP geolocation coordinates, ISP, and country flag using a fast local fallback or external geo API.
3.  **AI Classification:** The event features are extracted and passed to the Random Forest model to compute threat level classifications (LOW, MEDIUM, HIGH, CRITICAL) and anomaly confidence percentages.
4.  **Database Storage:** The enriched record is committed to PostgreSQL using pooled connections and indexed parameters.
5.  **Telemetry Push:** An SSE (Server-Sent Events) thread instantly broadcasts the new event to all active SOC dashboard UI clients.
6.  **Incident Routing:** If the threat is classified as HIGH or CRITICAL, a SOAR (Security Orchestration, Automation, and Response) routine fires webhooks to active Telegram channels and queues alert emails to security operations.

---

## 4. Machine Learning & Threat Classification

### Q: How does the Random Forest model classify attacks, and how do you handle training?
*   **Feature Extraction:** Payload length, character entropy, password strength (length and complexity), command keywords (e.g. `rm -rf`, `wget`, `/etc/shadow`), and request frequency are vectorized into a pandas DataFrame.
*   **Classification Engine:** The Random Forest Classifier aggregates votes from multiple decision trees to decide if the payload is `benign`, `anomaly`, or `malicious`.
*   **Model Lifecycle:** The model weights are saved to disk. When new attack records are verified, they trigger incremental background model updates to adjust weights, keeping predictions aligned with emerging threat vectors.

---

## 5. Docker Deployment

### Q: How is your system containerized for production deployment?
*   **Decoupled Components:** We write a multi-container `docker-compose.yml` defining the FastAPI API service, the PostgreSQL database node, and Celery background workers.
*   **Multi-Stage Builds:** The Dockerfile for the web backend uses multi-stage builds. First, it installs build dependencies, then copies only runtime libraries and compiles the application, reducing the production image size to under 200MB and limiting the attack surface of the container.
*   **Security Hardening:** Containers run as non-root users (`USER appuser`) with read-only filesystems where possible, and strict volume mount permissions to prevent container breakout exploits.

---

## 6. Database Design & Pooling

### Q: How do you configure PostgreSQL to handle heavy write volume?
*   **Connection Pooling:** We configure SQLAlchemy's `QueuePool` with `pool_size=20` and `max_overflow=10` to recycle database connections, avoiding the expensive TCP overhead of establishing a new connection on every decoy ping.
*   **Database Schema Optimization:**
    *   **Compound Indices:** We created indexes on `(organization_id, timestamp desc)` and `(organization_id, severity)` to optimize dashboard timeline pagination and metric aggregations.
    *   **Data Partitioning (Concept):** Under heavy global telemetry, we can partition the `attack_events` table by month to keep query plan searches fast.
*   **Development Fallback:** We built a dynamic fallback that uses SQLite locally if `DATABASE_URL` starts with `sqlite` to simplify deployment validation for recruiters, while executing full connection pooling in PostgreSQL production environments.

---

## 7. Authentication Flow

### Q: How are sessions managed, and how does your "Remember Me" logic work?
*   **OAuth2 JWT Bearer Tokens:** The login endpoint verifies hashed credentials using `bcrypt` and returns a JSON Web Token (JWT) signed with a secure `HS256` key.
*   **Session Isolation:**
    *   **Normal Login (Unchecked "Remember Me"):** The JWT is stored in `sessionStorage`. When the browser tab is closed, the token is destroyed, preventing session hijacking on public workstations.
    *   **Remember Me Checked:** The JWT is stored in `localStorage` with a longer expiration cookie, persisting sessions across reloads.
*   **Role-Based Access Control (RBAC):** Endpoints are wrapped with dependencies like `get_current_user` (general access for Analysts) and `get_admin_user` (restricting settings modifications, API key regeneration, and db purges to Administrators).

---

## 8. MITRE ATT&CK Mapping

### Q: What is MITRE ATT&CK, and how does HoneyCloud-X map it?
*   **MITRE ATT&CK** is a globally-accessible database of adversary tactics and techniques based on real-world observations.
*   **Mapping Engine:** HoneyCloud-X maps incoming telemetry to standard MITRE techniques:
    *   SSH brute-force login attempts map to **T1110 (Brute Force)**.
    *   Shell code commands (e.g. `cat /etc/shadow` or `rm -rf`) map to **T1059 (Command and Scripting Interpreter)**.
    *   E-commerce administrative injections map to **T1190 (Exploit Public-Facing Application)**.
    This gives analysts standardized vocabulary for reporting and compliance audits.
