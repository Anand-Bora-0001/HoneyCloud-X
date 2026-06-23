# HoneyCloud-X: 5-Minute Technical Demo Script

**Objective:** Showcase the entire pipeline from Threat Ingestion, to Deception Routing, Persona Profiling, and finally Automated Investigation via the SOC Dashboard.

## Setup
1. Have the HoneyCloud-X backend running (`uvicorn backend.app.main:app`).
2. Open the SOC Dashboard in a browser (`http://localhost:8000/dashboard.html`).
3. Have a terminal open to send `curl` commands, or use the "Simulate Attacks" button in the UI.

---

## Script

### 1. The Introduction (0:00 - 1:00)
**Action:** Show the SOC Dashboard empty or with baseline data.
**Dialogue:**
"Hi, I'd like to show you HoneyCloud-X. This is a platform I built to solve a specific problem: standard honeypots capture payloads, but they don't give you intelligence. They give you noise. I wanted to build a system that automatically investigates the attackers it catches. 

Right now, we are looking at the SOC Dashboard. It's connected to our FastAPI backend via real-time Server-Sent Events. Let's see what happens when an attacker targets our infrastructure."

### 2. The Ingestion & Routing (1:00 - 2:00)
**Action:** Click "Simulate Attacks" in the UI (or run a curl command simulating a `wp-login.php` brute force).
**Dialogue:**
"An attacker just initiated a scan against our WordPress endpoint. Normally, this would hit a 404 or a block page. 

Instead, HoneyCloud-X’s Threat Routing Engine intercepts the payload. Because the payload matches a known attack signature, the engine transparently issues a redirect routing the attacker directly into an isolated Deception Environment—our fake WordPress admin page—without breaking their session state."

### 3. Active Deception & Upload Traps (2:00 - 3:00)
**Action:** Navigate to the "Attacker Journey" panel and the "File Upload Trap" panel on the dashboard.
**Dialogue:**
"Now the attacker is trapped. As they interact with the fake environment, every action is logged. Here in the Attacker Journey, we can see them trying to bypass authentication. 

But it gets better. If the attacker attempts to upload a web shell, our File Upload Trap intercepts it. For strict security isolation, the system reads the stream, hashes the file for our intelligence tracking, and immediately drops the binary from memory. The malware never touches our disk."

### 4. The Persona Engine (3:00 - 4:00)
**Action:** Highlight the "Top Persona" and "Honey Tokens" cards.
**Dialogue:**
"Because the attacker attempted to upload a file, our asynchronous Persona Engine immediately upgrades their classification from a basic 'Scanner' to a 'Persistence Seeker'. 

If they had stumbled into our fake `.env` file and tried to steal the decoy AWS credentials, they would be immediately flagged as a 'Data Thief'."

### 5. The Investigation Workbench (4:00 - 5:00)
**Action:** Scroll down to the "SOC Investigations" panel. Click to download a JSON/CSV report if configured, or just show the narrative summary in the UI.
**Dialogue:**
"Finally, the best part: The Investigation Engine. 

Instead of forcing a human analyst to parse through logs, the system automatically aggregates the attacker's entire session history, calculates their 'dwell time' inside the trap, and reconstructs their attack path. 

It generates this human-readable Threat Narrative explaining exactly what the attacker intended to do. Furthermore, it maps every action to the MITRE ATT&CK framework automatically. 

HoneyCloud-X takes raw noise, safely traps the threat, and outputs actionable, interview-ready Threat Intelligence."
