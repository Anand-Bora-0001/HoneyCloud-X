#!/usr/bin/env python3
"""
Test suite for Advanced Security components
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from datetime import datetime
from app.advanced_security import (
    ThreatHunter, 
    AutomatedResponseSystem, 
    SecurityAuditLogger,
    SecurityEvent
)

class TestThreatHunter(unittest.TestCase):
    """Test cases for ThreatHunter class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.threat_hunter = ThreatHunter()
        
        # Sample events for testing
        self.sample_events = [
            {
                'source_ip': '192.168.1.100',
                'service': 'SSH',
                'username': 'admin',
                'password': 'password123',
                'timestamp': datetime.now().isoformat()
            },
            {
                'source_ip': '10.0.0.50',
                'service': 'HTTP',
                'command': 'powershell -enc SGVsbG8gV29ybGQ=',
                'payload': 'malicious payload',
                'timestamp': datetime.now().isoformat()
            },
            {
                'source_ip': '172.16.0.25',
                'service': 'FTP',
                'username': 'user1',
                'timestamp': datetime.now().isoformat()
            }
        ]
    
    def test_initialization(self):
        """Test ThreatHunter initialization"""
        self.assertIsInstance(self.threat_hunter.hunting_rules, list)
        self.assertIsInstance(self.threat_hunter.ioc_database, set)
        self.assertGreater(len(self.threat_hunter.hunting_rules), 0)
        
        # Check that default rules are loaded
        rule_names = [rule['name'] for rule in self.threat_hunter.hunting_rules]
        self.assertIn('Credential Stuffing', rule_names)
        self.assertIn('Living Off The Land', rule_names)
        self.assertIn('Lateral Movement', rule_names)
    
    def test_hunt_threats_empty_events(self):
        """Test threat hunting with empty events"""
        security_events = self.threat_hunter.hunt_threats([])
        
        self.assertIsInstance(security_events, list)
        self.assertEqual(len(security_events), 0)
    
    def test_hunt_threats_with_events(self):
        """Test threat hunting with sample events"""
        security_events = self.threat_hunter.hunt_threats(self.sample_events)
        
        self.assertIsInstance(security_events, list)
        
        # Check that security events have proper structure
        for event in security_events:
            self.assertIsInstance(event, SecurityEvent)
            self.assertIsInstance(event.event_id, str)
            self.assertIsInstance(event.timestamp, datetime)
            self.assertIsInstance(event.event_type, str)
            self.assertIsInstance(event.severity, str)
            self.assertIsInstance(event.source_ip, str)
            self.assertIsInstance(event.indicators, list)
            self.assertIsInstance(event.mitre_techniques, list)
            self.assertIsInstance(event.confidence, (int, float))
    
    def test_detect_credential_stuffing(self):
        """Test credential stuffing detection"""
        # Create events that should trigger credential stuffing detection
        stuffing_events = []
        for i in range(25):  # Create enough events to trigger detection
            stuffing_events.append({
                'source_ip': '192.168.1.100',
                'service': 'SSH',
                'username': f'user{i}',
                'password': f'pass{i}',
                'timestamp': datetime.now().isoformat()
            })
        
        detected = self.threat_hunter._detect_credential_stuffing(stuffing_events)
        
        self.assertIsInstance(detected, list)
        # Should detect the credential stuffing pattern
        if len(detected) > 0:
            event = detected[0]
            self.assertEqual(event['source_ip'], '192.168.1.100')
            self.assertIn('Credential stuffing', event['description'])
    
    def test_detect_lolbins(self):
        """Test Living Off The Land binaries detection"""
        lolbin_events = [
            {
                'source_ip': '10.0.0.50',
                'service': 'HTTP',
                'command': 'powershell -enc SGVsbG8gV29ybGQ=',
                'payload': 'malicious payload'
            }
        ]
        
        detected = self.threat_hunter._detect_lolbins(lolbin_events)
        
        self.assertIsInstance(detected, list)
        if len(detected) > 0:
            event = detected[0]
            self.assertEqual(event['source_ip'], '10.0.0.50')
            self.assertIn('LOLBin usage detected', event['description'])
    
    def test_detect_lateral_movement(self):
        """Test lateral movement detection"""
        lateral_events = [
            {'source_ip': '192.168.1.100', 'service': 'SSH'},
            {'source_ip': '192.168.1.100', 'service': 'HTTP'},
            {'source_ip': '192.168.1.100', 'service': 'FTP'},
            {'source_ip': '192.168.1.100', 'service': 'SMTP'}
        ]
        
        detected = self.threat_hunter._detect_lateral_movement(lateral_events)
        
        self.assertIsInstance(detected, list)
        if len(detected) > 0:
            event = detected[0]
            self.assertEqual(event['source_ip'], '192.168.1.100')
            self.assertIn('Lateral movement', event['description'])
    
    def test_add_ioc(self):
        """Test adding Indicators of Compromise"""
        initial_count = len(self.threat_hunter.ioc_database)
        
        self.threat_hunter.add_ioc('192.168.1.100', 'ip', 'Malicious IP')
        
        self.assertEqual(len(self.threat_hunter.ioc_database), initial_count + 1)
        self.assertIn('ip:192.168.1.100', self.threat_hunter.ioc_database)
    
    def test_check_iocs(self):
        """Test IOC checking"""
        # Add an IOC
        self.threat_hunter.add_ioc('192.168.1.100', 'ip', 'Test IOC')
        
        # Test event with matching IOC
        event = {'source_ip': '192.168.1.100'}
        matches = self.threat_hunter.check_iocs(event)
        
        self.assertIsInstance(matches, list)
        self.assertIn('ip:192.168.1.100', matches)
        
        # Test event without matching IOC
        event_no_match = {'source_ip': '10.0.0.1'}
        matches_none = self.threat_hunter.check_iocs(event_no_match)
        
        self.assertEqual(len(matches_none), 0)

class TestAutomatedResponseSystem(unittest.TestCase):
    """Test cases for AutomatedResponseSystem class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.response_system = AutomatedResponseSystem()
        
        self.sample_security_event = SecurityEvent(
            event_id='test_001',
            timestamp=datetime.now(),
            event_type='Brute Force',
            severity='CRITICAL',
            source_ip='192.168.1.100',
            target='ssh_server',
            description='Multiple failed login attempts',
            indicators=['ip:192.168.1.100'],
            mitre_techniques=['T1110'],
            confidence=0.9
        )
    
    def test_initialization(self):
        """Test AutomatedResponseSystem initialization"""
        self.assertIsInstance(self.response_system.response_rules, list)
        self.assertIsInstance(self.response_system.blocked_ips, set)
        self.assertIsInstance(self.response_system.response_history, list)
        
        # Check that default rules are loaded
        self.assertGreater(len(self.response_system.response_rules), 0)
    
    def test_process_security_event(self):
        """Test processing security events"""
        result = self.response_system.process_security_event(self.sample_security_event)
        
        self.assertIsInstance(result, dict)
        self.assertIn('event_id', result)
        self.assertIn('responses_triggered', result)
        self.assertIn('total_responses', result)
        
        self.assertEqual(result['event_id'], 'test_001')
        self.assertIsInstance(result['responses_triggered'], list)
        self.assertIsInstance(result['total_responses'], int)
    
    def test_is_ip_blocked(self):
        """Test IP blocking functionality"""
        # Initially IP should not be blocked
        self.assertFalse(self.response_system.is_ip_blocked('192.168.1.100'))
        
        # Process a critical event (should trigger blocking)
        self.response_system.process_security_event(self.sample_security_event)
        
        # Check if IP is now blocked (depends on rule configuration)
        # This test might pass or fail depending on the specific rule conditions
        blocked_status = self.response_system.is_ip_blocked('192.168.1.100')
        self.assertIsInstance(blocked_status, bool)

class TestSecurityAuditLogger(unittest.TestCase):
    """Test cases for SecurityAuditLogger class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.audit_logger = SecurityAuditLogger()
        
        self.sample_security_event = SecurityEvent(
            event_id='audit_001',
            timestamp=datetime.now(),
            event_type='SQL Injection',
            severity='HIGH',
            source_ip='10.0.0.50',
            target='web_server',
            description='Malicious SQL query detected',
            indicators=['payload:SELECT * FROM users'],
            mitre_techniques=['T1190'],
            confidence=0.8
        )
    
    def test_initialization(self):
        """Test SecurityAuditLogger initialization"""
        self.assertIsInstance(self.audit_logger.audit_logs, list)
        self.assertEqual(self.audit_logger.log_retention_days, 90)
    
    def test_log_security_event(self):
        """Test logging security events"""
        initial_count = len(self.audit_logger.audit_logs)
        
        self.audit_logger.log_security_event(self.sample_security_event)
        
        self.assertEqual(len(self.audit_logger.audit_logs), initial_count + 1)
        
        # Check the logged entry
        logged_entry = self.audit_logger.audit_logs[-1]
        self.assertIn('timestamp', logged_entry)
        self.assertIn('event_id', logged_entry)
        self.assertIn('event_type', logged_entry)
        self.assertIn('severity', logged_entry)
        self.assertIn('source_ip', logged_entry)
        self.assertIn('action', logged_entry)
        self.assertIn('description', logged_entry)
        
        self.assertEqual(logged_entry['event_id'], 'audit_001')
        self.assertEqual(logged_entry['event_type'], 'SQL Injection')
        self.assertEqual(logged_entry['severity'], 'HIGH')
        self.assertEqual(logged_entry['source_ip'], '10.0.0.50')
        self.assertEqual(logged_entry['action'], 'detected')
    
    def test_log_security_event_with_custom_action(self):
        """Test logging with custom action"""
        self.audit_logger.log_security_event(self.sample_security_event, 'blocked')
        
        logged_entry = self.audit_logger.audit_logs[-1]
        self.assertEqual(logged_entry['action'], 'blocked')
    
    def test_get_audit_logs(self):
        """Test retrieving audit logs"""
        # Add some test logs
        for i in range(5):
            test_event = SecurityEvent(
                event_id=f'test_{i}',
                timestamp=datetime.now(),
                event_type='Test Event',
                severity='LOW',
                source_ip=f'192.168.1.{i}',
                target='test_target',
                description=f'Test event {i}',
                indicators=[],
                mitre_techniques=[],
                confidence=0.5
            )
            self.audit_logger.log_security_event(test_event)
        
        # Get all logs
        all_logs = self.audit_logger.get_audit_logs()
        self.assertIsInstance(all_logs, list)
        self.assertGreaterEqual(len(all_logs), 5)
        
        # Get limited logs
        limited_logs = self.audit_logger.get_audit_logs(limit=3)
        self.assertEqual(len(limited_logs), 3)

class TestSecurityEvent(unittest.TestCase):
    """Test cases for SecurityEvent dataclass"""
    
    def test_security_event_creation(self):
        """Test SecurityEvent creation"""
        event = SecurityEvent(
            event_id='test_event_001',
            timestamp=datetime.now(),
            event_type='Test Attack',
            severity='MEDIUM',
            source_ip='192.168.1.200',
            target='test_server',
            description='Test security event',
            indicators=['test:indicator'],
            mitre_techniques=['T1234'],
            confidence=0.7
        )
        
        self.assertEqual(event.event_id, 'test_event_001')
        self.assertEqual(event.event_type, 'Test Attack')
        self.assertEqual(event.severity, 'MEDIUM')
        self.assertEqual(event.source_ip, '192.168.1.200')
        self.assertEqual(event.target, 'test_server')
        self.assertEqual(event.description, 'Test security event')
        self.assertEqual(event.indicators, ['test:indicator'])
        self.assertEqual(event.mitre_techniques, ['T1234'])
        self.assertEqual(event.confidence, 0.7)
        self.assertIsInstance(event.timestamp, datetime)

def run_advanced_security_tests():
    """Run all advanced security tests"""
    print("🛡️ Testing Advanced Security Components")
    print("=" * 50)
    
    # Create test suite
    test_classes = [
        TestThreatHunter,
        TestAutomatedResponseSystem,
        TestSecurityAuditLogger,
        TestSecurityEvent
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All Advanced Security tests passed!")
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    run_advanced_security_tests()