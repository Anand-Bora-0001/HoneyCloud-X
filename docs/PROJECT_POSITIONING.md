# HoneyCloud-X: Project Positioning & Interview Guide

This document contains pre-written descriptions and talking points for resumes, LinkedIn profiles, GitHub, and technical interviews.

---

## 1. Resume Bullet Points (Software Engineering / Cybersecurity)

**Project: HoneyCloud-X (Threat Intelligence & Deception Platform)**
* **Role:** Principal Architect / Backend Engineer
* **Tech Stack:** Python, FastAPI, SQLAlchemy, JavaScript (Vanilla UI), HTML/CSS, Pytest.
* Architected an event-driven cybersecurity honeypot using FastAPI, processing simulated malicious payloads with sub-50ms latency.
* Engineered an asynchronous 'Investigation Workbench' that aggregates attacker behaviors across sessions to auto-generate Threat Narratives and MITRE ATT&CK framework mappings.
* Designed an adaptive 'Persona Engine' that classifies threats in real-time (e.g., Data Thief, Persistence Seeker) based on interactions with fake upload traps and decoy AWS credentials (honey tokens).
* Developed a responsive SOC Dashboard utilizing vanilla JavaScript and CSS to visualize attacker timelines, live threat intelligence feeds, and cross-session correlation clusters.
* Implemented strict database isolation and payload-hashing mechanisms, completely neutralizing lateral movement risks from captured malware uploads.

---

## 2. LinkedIn Project Summary

🚀 **Just shipped HoneyCloud-X: A Next-Generation Threat Intelligence Honeypot.**

I built HoneyCloud-X to bridge the gap between simple threat detection and automated threat intelligence. Instead of just logging an IP address, this platform dynamically traps attackers in an interactive Deception Environment and automatically investigates their behavior.

**Key Features:**
🛡️ **Adaptive Routing:** Uses an event-driven engine to seamlessly redirect malicious payloads into isolated fake-admin interfaces and databases.
🧠 **Behavioral Personas:** An algorithm classifies attackers in real-time as 'Credential Hunters', 'Persistence Seekers', or 'Data Thieves' based on their navigation paths.
🍯 **Honey Tokens & Upload Traps:** Securely tracks and hashes malware uploads while exposing fake AWS/DB credentials to monitor lateral movement.
📊 **Automated SOC Investigations:** Automatically reconstructs attack timelines, maps techniques to the MITRE ATT&CK framework, and correlates multiple IPs into unified Threat Campaigns.

Built from scratch using **FastAPI, SQLAlchemy, and a vanilla JS dashboard**—focusing heavily on async processing and strict security boundaries.

---

## 3. The 2-Minute Elevator Pitch

"HoneyCloud-X is an advanced deception technology platform designed to catch and profile sophisticated cyber attacks. Traditional honeypots just log an IP and a payload. I wanted to build something smarter. When an attacker hits HoneyCloud-X, the system transparently routes them into a fake environment—like a mock WordPress admin or database. As they navigate, my custom Persona Engine watches their behavior. If they try to brute-force a login, it labels them a Credential Hunter. If they upload a web shell, it tags them a Persistence Seeker. Behind the scenes, an asynchronous Investigation Engine reconstructs their entire attack path, maps their actions to the MITRE ATT&CK framework, and generates a human-readable threat report. It turns raw noise into immediate, actionable SOC intelligence."

---

## 4. Technical Interview Talking Points

**Q: How did you handle the security of the File Upload Trap?**
*A:* "Security isolation was my top priority. I didn't want the honeypot to become a launchpad for lateral movement. When an attacker submits a file to the `/fake-upload` endpoint, the system reads the stream into memory, hashes it using SHA-256 for metadata tracking, logs the size and MIME type to the database, and then immediately discards the binary payload. It is never written to disk, ensuring 100% isolation."

**Q: Why use FastAPI, and how did you handle performance?**
*A:* "I chose FastAPI for its native async support and high throughput. The initial payload ingestion (`/api/ingest`) is fully synchronous and blazingly fast because it needs to return a dynamic routing decision immediately. However, the heavy lifting—like evaluating the attacker's persona, cross-referencing previous sessions, and generating the Threat Investigation reports—is offloaded to FastAPI's `BackgroundTasks`. This keeps the critical ingestion path under 50ms latency."

**Q: Explain how the MITRE ATT&CK Mapping works.**
*A:* "As the attacker interacts with the deception environment, actions are logged as specific event types, like `WP_AUTH_ATTEMPT` or `HONEY_TOKEN_TRIGGERED`. In Phase 4, I built a mapper that translates these proprietary action types directly to official MITRE techniques. For instance, accessing a fake `.env` file maps to `T1552.001 - Credentials in Files`. This mapping is then attached to the auto-generated Investigation Report."

**Q: How do you identify coordinated attacks?**
*A:* "Through the Correlation Engine. It runs a heuristic analysis over the Attacker Profiles. If it detects multiple profiles originating from the same /24 subnet, exhibiting the exact same Persona, and utilizing identical payload signatures, it automatically merges them into a `ThreatCampaign`. This helps SOC analysts realize that 50 random IPs scanning their network are actually a single coordinated botnet."
