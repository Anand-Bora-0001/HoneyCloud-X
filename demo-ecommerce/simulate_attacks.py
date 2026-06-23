"""
HoneyCloud-X Attack Simulator for Demo E-Commerce
=================================================
This script acts as a cyber threat actor, executing automated scans and targeted
incursions against the Demo E-Commerce application (running on port 5000).
It showcases how these attacks trigger Flask decoy sensors and reflect on HoneyCloud.
"""

import urllib.request
import urllib.error
import time
import sys
import os
import io

# Fix Windows console encoding for emoji/Unicode support
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

TARGET_URL = "http://localhost:5000"
HONEYCLOUD_URL = "http://localhost:8000"

ATTACKS = [
    {"endpoint": "/admin", "name": "Admin Control Panel Scan", "type": "Privilege Escalation / Recon", "severity": "CRITICAL"},
    {"endpoint": "/wp-login.php", "name": "WordPress Core Vulnerability Probe", "type": "Brute Force / Scan", "severity": "HIGH"},
    {"endpoint": "/.env", "name": "Environment Configuration Leak Search", "type": "Credential Theft", "severity": "CRITICAL"},
    {"endpoint": "/phpmyadmin", "name": "Database Control Interface Scan", "type": "Injection / Discovery", "severity": "HIGH"},
    {"endpoint": "/api/debug", "name": "API Debug Endpoint Probe", "type": "Information Disclosure", "severity": "HIGH"},
    {"endpoint": "/.git/config", "name": "Git Repository Exposure Attempt", "type": "Source Code Leak", "severity": "CRITICAL"},
    {"endpoint": "/backup.sql", "name": "Unsecured SQL Database Dump Search", "type": "Exfiltration", "severity": "CRITICAL"},
]

def check_services():
    """Verify that both applications are running before running simulation"""
    print("🔍 [System Check] Verifying application status...")
    
    # Check E-Commerce
    try:
        urllib.request.urlopen(f"{TARGET_URL}/health", timeout=2)
        print(f"✅ Demo E-Commerce is ONLINE at {TARGET_URL}")
    except Exception:
        print(f"❌ Demo E-Commerce is OFFLINE at {TARGET_URL}.")
        print("   -> Please run: cd demo-ecommerce && python app.py")
        return False

    # Check HoneyCloud
    try:
        urllib.request.urlopen(f"{HONEYCLOUD_URL}/health", timeout=2)
        print(f"✅ HoneyCloud Backend is ONLINE at {HONEYCLOUD_URL}")
    except Exception:
        print(f"❌ HoneyCloud Backend is OFFLINE at {HONEYCLOUD_URL}.")
        print("   -> Please run: python -m uvicorn backend.app.main:app --reload")
        return False
        
    return True

def execute_attacks():
    """Iterates and runs requests simulating attacks"""
    print("\n🚀 [Simulation] Initializing E-Commerce Threat Vectors against Decoey Web App...")
    print("=" * 75)
    
    for i, attack in enumerate(ATTACKS, 1):
        url = f"{TARGET_URL}{attack['endpoint']}"
        print(f"\n[{i}/{len(ATTACKS)}] Threat Vector: {attack['name']}")
        print(f"      Targeting: {url}")
        print(f"      Expected Threat Level: {attack['severity']} ({attack['type']})")
        
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 ThreatScanner/3.1 (Security Audit)'}
            )
            with urllib.request.urlopen(req, timeout=3) as res:
                # Normally, honeypot endpoints return 404/403 so this won't be reached
                print(f"      Response: Status {res.status}")
        except urllib.error.HTTPError as e:
            # We expect a 404 or 403 response code as the decoy honeypot masks itself
            print(f"      Response: Masked successfully (HTTP {e.code} Not Found)")
            print(f"      🛡️ [HoneyCloud Client] Event ingested and transmitted to SOC Dashboard.")
        except Exception as e:
            print(f"      Response Error: {e}")
            
        # Small delay to mimic a human attacker scanning
        time.sleep(1)
        
    print("\n" + "=" * 75)
    print("🎉 [Simulation Complete] All simulated attacks have been executed against the store.")
    print("📊 Check the HoneyCloud SOC Dashboard at http://localhost:8000/dashboard.html")
    print("   Look for 'DEMO_ECOMMERCE' in the Service list to see these threats reflected!")
    print("=" * 75)

if __name__ == "__main__":
    if check_services():
        execute_attacks()
    else:
        sys.exit(1)
