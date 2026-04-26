#!/usr/bin/env python3
"""
HoneyCloud Honeypot Service Simulator
Simulates actual honeypot services (SSH, FTP, HTTP) and sends attack data to HoneyCloud
"""

import requests
import time
import random
from datetime import datetime, timezone
import json

# Configuration
HONEYCLOUD_API_URL = "http://localhost:8000"

def print_banner():
    """Print honeypot simulator banner"""
    print("\n" + "="*70)
    print("🍯 HoneyCloud Honeypot Service Simulator")
    print("   Simulates real honeypot services sending attack data")
    print("="*70)
    print(f"HoneyCloud API: {HONEYCLOUD_API_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")

def simulate_ssh_honeypot_attacks():
    """Simulate SSH honeypot receiving attacks"""
    print("🔐 Simulating SSH Honeypot Attacks...")
    
    ssh_attacks = [
        {"username": "root", "password": "123456", "severity": "CRITICAL"},
        {"username": "admin", "password": "admin", "severity": "HIGH"},
        {"username": "root", "password": "password", "severity": "CRITICAL"},
        {"username": "user", "password": "user", "severity": "MEDIUM"},
        {"username": "guest", "password": "guest", "severity": "LOW"},
        {"username": "root", "password": "toor", "severity": "HIGH"},
        {"username": "admin", "password": "password123", "severity": "HIGH"},
        {"username": "oracle", "password": "oracle", "severity": "MEDIUM"},
    ]
    
    for i, attack in enumerate(ssh_attacks):
        attack_data = {
            "service": "SSH",
            "source_ip": f"192.168.{random.randint(1,254)}.{random.randint(1,254)}",
            "source_port": random.randint(1024, 65535),
            "destination_port": 22,
            "username": attack["username"],
            "password": attack["password"],
            "command": random.choice(["ls", "whoami", "cat /etc/passwd", "sudo su", "rm -rf /"]),
            "severity": attack["severity"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attack_type": "brute_force",
            "session_id": f"ssh_{random.randint(1000, 9999)}",
            "user_agent": "OpenSSH_7.4",
            "endpoint": "/ssh",
            "method": "SSH_AUTH",
            "payload": f"{attack['username']}:{attack['password']}"
        }
        
        try:
            response = requests.post(
                f"{HONEYCLOUD_API_URL}/api/ingest",
                json=attack_data,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"   ✅ SSH Attack {i+1}: {attack['username']}@{attack_data['source_ip']} -> {attack['severity']}")
            else:
                print(f"   ❌ SSH Attack {i+1}: Failed ({response.status_code})")
                
        except Exception as e:
            print(f"   ❌ SSH Attack {i+1}: Error - {e}")
        
        time.sleep(0.5)

def simulate_ftp_honeypot_attacks():
    """Simulate FTP honeypot receiving attacks"""
    print("\n📁 Simulating FTP Honeypot Attacks...")
    
    ftp_attacks = [
        {"username": "anonymous", "password": "guest@example.com", "severity": "MEDIUM"},
        {"username": "ftp", "password": "ftp", "severity": "MEDIUM"},
        {"username": "admin", "password": "admin", "severity": "HIGH"},
        {"username": "root", "password": "123456", "severity": "CRITICAL"},
        {"username": "user", "password": "password", "severity": "MEDIUM"},
    ]
    
    for i, attack in enumerate(ftp_attacks):
        attack_data = {
            "service": "FTP",
            "source_ip": f"10.0.{random.randint(1,254)}.{random.randint(1,254)}",
            "source_port": random.randint(1024, 65535),
            "destination_port": 21,
            "username": attack["username"],
            "password": attack["password"],
            "command": random.choice(["LIST", "RETR /etc/passwd", "STOR malware.exe", "CWD /root"]),
            "severity": attack["severity"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attack_type": "credential_stuffing",
            "session_id": f"ftp_{random.randint(1000, 9999)}",
            "user_agent": "FileZilla/3.46.0",
            "endpoint": "/ftp",
            "method": "FTP_AUTH",
            "payload": f"{attack['username']}:{attack['password']}"
        }
        
        try:
            response = requests.post(
                f"{HONEYCLOUD_API_URL}/api/ingest",
                json=attack_data,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"   ✅ FTP Attack {i+1}: {attack['username']}@{attack_data['source_ip']} -> {attack['severity']}")
            else:
                print(f"   ❌ FTP Attack {i+1}: Failed ({response.status_code})")
                
        except Exception as e:
            print(f"   ❌ FTP Attack {i+1}: Error - {e}")
        
        time.sleep(0.5)

def simulate_http_honeypot_attacks():
    """Simulate HTTP honeypot receiving attacks"""
    print("\n🌐 Simulating HTTP Honeypot Attacks...")
    
    http_attacks = [
        {"endpoint": "/admin", "method": "GET", "severity": "HIGH"},
        {"endpoint": "/wp-admin", "method": "POST", "severity": "HIGH"},
        {"endpoint": "/phpmyadmin", "method": "GET", "severity": "CRITICAL"},
        {"endpoint": "/.env", "method": "GET", "severity": "MEDIUM"},
        {"endpoint": "/config.php", "method": "GET", "severity": "MEDIUM"},
        {"endpoint": "/login.php", "method": "POST", "severity": "MEDIUM"},
        {"endpoint": "/backup.sql", "method": "GET", "severity": "HIGH"},
    ]
    
    for i, attack in enumerate(http_attacks):
        attack_data = {
            "service": "HTTP",
            "source_ip": f"172.16.{random.randint(1,254)}.{random.randint(1,254)}",
            "source_port": random.randint(1024, 65535),
            "destination_port": 80,
            "username": random.choice(["admin", "root", "user", None]),
            "password": random.choice(["admin123", "password", "123456", None]),
            "command": f"{attack['method']} {attack['endpoint']}",
            "severity": attack["severity"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attack_type": "web_probe",
            "session_id": f"http_{random.randint(1000, 9999)}",
            "user_agent": random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "curl/7.68.0",
                "python-requests/2.25.1",
                "Nmap NSE"
            ]),
            "endpoint": attack["endpoint"],
            "method": attack["method"],
            "payload": f"{attack['method']} {attack['endpoint']}"
        }
        
        try:
            response = requests.post(
                f"{HONEYCLOUD_API_URL}/api/ingest",
                json=attack_data,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"   ✅ HTTP Attack {i+1}: {attack['method']} {attack['endpoint']} from {attack_data['source_ip']} -> {attack['severity']}")
            else:
                print(f"   ❌ HTTP Attack {i+1}: Failed ({response.status_code})")
                
        except Exception as e:
            print(f"   ❌ HTTP Attack {i+1}: Error - {e}")
        
        time.sleep(0.5)

def simulate_telnet_honeypot_attacks():
    """Simulate TELNET honeypot receiving attacks"""
    print("\n📟 Simulating TELNET Honeypot Attacks...")
    
    telnet_attacks = [
        {"username": "admin", "password": "admin", "severity": "HIGH"},
        {"username": "root", "password": "root", "severity": "CRITICAL"},
        {"username": "cisco", "password": "cisco", "severity": "HIGH"},
        {"username": "admin", "password": "password", "severity": "HIGH"},
    ]
    
    for i, attack in enumerate(telnet_attacks):
        attack_data = {
            "service": "TELNET",
            "source_ip": f"203.0.113.{random.randint(1,254)}",
            "source_port": random.randint(1024, 65535),
            "destination_port": 23,
            "username": attack["username"],
            "password": attack["password"],
            "command": random.choice(["enable", "show config", "copy running-config", "reload"]),
            "severity": attack["severity"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attack_type": "brute_force",
            "session_id": f"telnet_{random.randint(1000, 9999)}",
            "user_agent": "Telnet Client",
            "endpoint": "/telnet",
            "method": "TELNET_AUTH",
            "payload": f"{attack['username']}:{attack['password']}"
        }
        
        try:
            response = requests.post(
                f"{HONEYCLOUD_API_URL}/api/ingest",
                json=attack_data,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"   ✅ TELNET Attack {i+1}: {attack['username']}@{attack_data['source_ip']} -> {attack['severity']}")
            else:
                print(f"   ❌ TELNET Attack {i+1}: Failed ({response.status_code})")
                
        except Exception as e:
            print(f"   ❌ TELNET Attack {i+1}: Error - {e}")
        
        time.sleep(0.5)

def check_results():
    """Check the attack results in HoneyCloud"""
    print("\n📊 Checking Honeypot Attack Results...")
    
    try:
        # Login first
        login_response = requests.post(
            f"{HONEYCLOUD_API_URL}/auth/login",
            data={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Get stats
            stats_response = requests.get(f"{HONEYCLOUD_API_URL}/api/stats", headers=headers, timeout=5)
            events_response = requests.get(f"{HONEYCLOUD_API_URL}/api/events?limit=30", headers=headers, timeout=5)
            
            if stats_response.status_code == 200 and events_response.status_code == 200:
                stats = stats_response.json()
                events = events_response.json()
                
                print(f"   ✅ Total Events: {stats.get('total_events', 0)}")
                print(f"   ✅ Recent Events: {len(events)}")
                
                # Count by service
                service_counts = {}
                severity_counts = {}
                
                for event in events:
                    service = event.get('service', 'Unknown')
                    severity = event.get('severity', 'Unknown')
                    service_counts[service] = service_counts.get(service, 0) + 1
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                print(f"   📊 By Service: {dict(service_counts)}")
                print(f"   📊 By Severity: {dict(severity_counts)}")
                
            else:
                print(f"   ❌ Failed to fetch results")
                
        else:
            print(f"   ❌ Authentication failed")
            
    except Exception as e:
        print(f"   ❌ Error checking results: {e}")

def main():
    """Run honeypot service simulation"""
    print_banner()
    
    # Simulate different honeypot services
    simulate_ssh_honeypot_attacks()
    simulate_ftp_honeypot_attacks()
    simulate_http_honeypot_attacks()
    simulate_telnet_honeypot_attacks()
    
    # Check results
    check_results()
    
    # Final instructions
    print("\n" + "="*70)
    print("🎉 Honeypot Service Simulation Complete!")
    print("="*70)
    print("📊 View results at:")
    print(f"   → Dashboard: http://localhost:5173/dashboard.html")
    print("   → Login: admin / admin123")
    print()
    print("🔄 You should now see attacks from:")
    print("   → SSH Honeypot (port 22)")
    print("   → FTP Honeypot (port 21)")
    print("   → HTTP Honeypot (port 80)")
    print("   → TELNET Honeypot (port 23)")
    print("="*70)

if __name__ == "__main__":
    main()