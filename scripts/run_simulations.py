import requests
import time
import sys

BASE_URL = "http://localhost:8000"
API_KEY = "hc_live_fsj-onia9stXSc2HgIuUDqfwR_f5Oe0Q4sTZTMhBku0"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

print("Starting HoneyCloud-X System Verification...")

# Helper to ingest attack and get redirect URL
def trigger_attack(endpoint, payload_data, source_ip):
    data = {
        "endpoint": endpoint,
        "method": "POST",
        "severity": "HIGH",
        "source_ip": source_ip,
        "payload": payload_data,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    resp = requests.post(f"{BASE_URL}/api/ingest", json=data, headers=HEADERS)
    if resp.status_code == 200:
        j = resp.json()
        return j.get("redirect_url"), j.get("session_id")
    return None, None

results = []

def log_result(name, expected, actual, success):
    print(f"[{'PASS' if success else 'FAIL'}] {name}")
    results.append({
        "attack": name,
        "expected": expected,
        "actual": actual,
        "success": success
    })

# 1. Directory Scanning
print("\n--- 1. Directory Scanning ---")
redir_scan, sid = trigger_attack("/.git/config", "", "10.0.0.1")
if redir_scan:
    log_result("Directory Scanning", "Redirects to generic deception trap", f"Redirected to {redir_scan}", True)
else:
    log_result("Directory Scanning", "Redirects to generic deception trap", "No redirect", False)

# 2. SQL Injection
print("\n--- 2. SQL Injection ---")
redir_sql, sid = trigger_attack("/login.php", "' OR 1=1 --", "10.0.0.2")
if redir_sql:
    log_result("SQL Injection", "Redirects to Fake DB or Admin", f"Redirected to {redir_sql}", True)
else:
    log_result("SQL Injection", "Redirects to Fake DB or Admin", "No redirect", False)

# 3. XSS
print("\n--- 3. XSS ---")
redir_xss, sid = trigger_attack("/search", "<script>alert(1)</script>", "10.0.0.3")
if redir_xss:
    log_result("XSS", "Redirects to generic deception trap", f"Redirected to {redir_xss}", True)
else:
    log_result("XSS", "Redirects to generic deception trap", "No redirect", False)

# 4. Brute Force (WP Admin)
print("\n--- 4. Brute Force (WP Admin) ---")
redir_wp, sid = trigger_attack("/wp-login.php", "admin:password123", "10.0.0.4")
if redir_wp and "wp-admin" in redir_wp:
    log_result("Brute Force", "Redirects to Fake WP Admin", f"Redirected to {redir_wp}", True)
    # Follow redirect to register trap action
    requests.get(f"{BASE_URL}{redir_wp}?sid={sid}")
else:
    log_result("Brute Force", "Redirects to Fake WP Admin", "No redirect", False)

# 5. Honey Token Access
print("\n--- 5. Honey Token Access ---")
redir_token, sid = trigger_attack("/.env", "", "10.0.0.5")
if redir_token and ("leak" in redir_token or ".env" in redir_token):
    log_result("Honey Token Access", "Redirects to Fake .env file", f"Redirected to {redir_token}", True)
    # Follow redirect to register token hit
    requests.get(f"{BASE_URL}{redir_token}?sid={sid}")
else:
    log_result("Honey Token Access", "Redirects to Fake .env file", "No redirect", False)

# 6. File Upload Attempt
print("\n--- 6. File Upload Attempt ---")
redir_upload, sid = trigger_attack("/upload.php", "multipart/form-data", "10.0.0.6")
print(f"DEBUG: redir_upload is {redir_upload}")
if redir_upload and "fake-upload" in redir_upload:
    log_result("File Upload Attempt", "Redirects to Fake Upload Sink", f"Redirected to {redir_upload}", True)
    # Upload payload
    files = {"file": ("webshell.php", b"<?php system($_GET['cmd']); ?>", "application/x-httpd-php")}
    up_resp = requests.post(f"{BASE_URL}{redir_upload}?sid={sid}", files=files)
    if up_resp.status_code == 200:
        log_result("File Upload Post", "Payload hashed and dropped", "Successfully intercepted", True)
else:
    log_result("File Upload Attempt", "Redirects to Fake Upload Sink", "No redirect", False)

# Give Async background tasks time to process Personas and Investigations
print("\nWaiting 4 seconds for async BackgroundTasks to complete...")
time.sleep(4)

# Login to get JWT for Dashboard endpoints
login_data = {"username": "admin", "password": "admin123"}
login_resp = requests.post(f"{BASE_URL}/auth/login", data=login_data)
JWT_TOKEN = None
if login_resp.status_code == 200:
    JWT_TOKEN = login_resp.json().get("access_token")

# Verify Investigations Generation
print("\n--- Validating Investigations ---")
if JWT_TOKEN:
    dash_headers = {"Authorization": f"Bearer {JWT_TOKEN}"}
    inv_resp = requests.get(f"{BASE_URL}/api/investigations/", headers=dash_headers)
    print(f"DEBUG: inv_resp status {inv_resp.status_code}")
    print(f"DEBUG: inv_resp json {inv_resp.json()}")
    if inv_resp.status_code == 200:
        invs = inv_resp.json()
        log_result("Investigation Engine", "Generates reports for attacks", f"Generated {len(invs)} reports", len(invs) > 0)
        for inv in invs:
            print(f"Report for Attacker {inv['attacker_id']}: {inv['summary']}")
    else:
        log_result("Investigation Engine", "Generates reports for attacks", "API Failed", False)
else:
    log_result("Investigation Engine", "Generates reports for attacks", "Login Failed", False)

# Write results to a JSON file for the report generator
import json
with open("verification_results.json", "w") as f:
    json.dump(results, f, indent=4)

print("\nVerification Complete.")
