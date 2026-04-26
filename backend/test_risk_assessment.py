#!/usr/bin/env python3
"""
Test suite for RiskAssessment class in advanced_analytics module
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import unittest
from datetime import datetime, timedelta
from app.advanced_analytics import RiskAssessment

class TestRiskAssessment(unittest.TestCase):
    """Test cases for RiskAssessment class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.risk_assessment = RiskAssessment()
        
        # Sample events for testing
        self.sample_events = [
            {
                'timestamp': datetime.now().isoformat(),
                'source_ip': '192.168.1.100',
                'service': 'ssh',
                'severity': 'HIGH',
                'attack_type': 'brute_force',
                'username': 'admin',
                'password': 'password123'
            },
            {
                'timestamp': datetime.now().isoformat(),
                'source_ip': '10.0.0.50',
                'service': 'http',
                'severity': 'MEDIUM',
                'attack_type': 'sql_injection',
                'payload': 'SELECT * FROM users'
            },
            {
                'timestamp': datetime.now().isoformat(),
                'source_ip': '172.16.0.25',
                'service': 'ftp',
                'severity': 'CRITICAL',
                'attack_type': 'privilege_escalation',
                'command': 'sudo su -'
            }
        ]
        
        self.sample_assets = [
            {'name': 'web_server', 'criticality': 'HIGH'},
            {'name': 'database', 'criticality': 'CRITICAL'},
            {'name': 'backup_server', 'criticality': 'MEDIUM'}
        ]
    
    def test_initialization(self):
        """Test RiskAssessment initialization"""
        self.assertIsInstance(self.risk_assessment.risk_models, dict)
        self.assertIsInstance(self.risk_assessment.threat_weights, dict)
        self.assertIsInstance(self.risk_assessment.service_risk_multipliers, dict)
        
        # Check threat weights
        self.assertEqual(self.risk_assessment.threat_weights['CRITICAL'], 1.0)
        self.assertEqual(self.risk_assessment.threat_weights['HIGH'], 0.7)
        self.assertEqual(self.risk_assessment.threat_weights['MEDIUM'], 0.4)
        self.assertEqual(self.risk_assessment.threat_weights['LOW'], 0.1)
        
        # Check service multipliers
        self.assertIn('ssh', self.risk_assessment.service_risk_multipliers)
        self.assertIn('http', self.risk_assessment.service_risk_multipliers)
    
    def test_calculate_overall_risk_score_empty_events(self):
        """Test risk calculation with empty events"""
        result = self.risk_assessment.calculate_overall_risk_score([])
        
        self.assertEqual(result['overall_risk_score'], 0.0)
        self.assertEqual(result['risk_level'], 'MINIMAL')
        self.assertEqual(result['confidence'], 1.0)
        self.assertIn('recommendations', result)
    
    def test_calculate_overall_risk_score_with_events(self):
        """Test risk calculation with sample events"""
        result = self.risk_assessment.calculate_overall_risk_score(self.sample_events)
        
        self.assertIsInstance(result, dict)
        self.assertIn('overall_risk_score', result)
        self.assertIn('risk_level', result)
        self.assertIn('confidence', result)
        self.assertIn('factors', result)
        self.assertIn('breakdown', result)
        self.assertIn('recommendations', result)
        
        # Check that risk score is a valid number
        self.assertIsInstance(result['overall_risk_score'], (int, float))
        self.assertGreaterEqual(result['overall_risk_score'], 0)
        self.assertLessEqual(result['overall_risk_score'], 100)
        
        # Check risk level is valid
        valid_levels = ['MINIMAL', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        self.assertIn(result['risk_level'], valid_levels)
        
        # Check confidence is between 0 and 1
        self.assertGreaterEqual(result['confidence'], 0)
        self.assertLessEqual(result['confidence'], 1)
    
    def test_calculate_overall_risk_score_with_assets(self):
        """Test risk calculation with assets"""
        result = self.risk_assessment.calculate_overall_risk_score(
            self.sample_events, 
            self.sample_assets
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('overall_risk_score', result)
        # Risk score should be affected by asset criticality
        self.assertGreater(result['overall_risk_score'], 0)
    
    def test_assess_service_risk_empty_events(self):
        """Test service risk assessment with no events"""
        result = self.risk_assessment.assess_service_risk('ssh', [])
        
        self.assertEqual(result['service'], 'ssh')
        self.assertEqual(result['risk_score'], 0.0)
        self.assertEqual(result['risk_level'], 'MINIMAL')
        self.assertEqual(result['event_count'], 0)
        self.assertIn('recommendations', result)
    
    def test_assess_service_risk_with_events(self):
        """Test service risk assessment with events"""
        result = self.risk_assessment.assess_service_risk('ssh', self.sample_events)
        
        self.assertEqual(result['service'], 'ssh')
        self.assertIsInstance(result['risk_score'], (int, float))
        self.assertGreaterEqual(result['risk_score'], 0)
        self.assertIn('risk_level', result)
        self.assertIn('event_count', result)
        self.assertIn('recommendations', result)
        self.assertIn('timestamp', result)
    
    def test_determine_risk_level(self):
        """Test risk level determination"""
        self.assertEqual(self.risk_assessment._determine_risk_level(90), 'CRITICAL')
        self.assertEqual(self.risk_assessment._determine_risk_level(70), 'HIGH')
        self.assertEqual(self.risk_assessment._determine_risk_level(50), 'MEDIUM')
        self.assertEqual(self.risk_assessment._determine_risk_level(30), 'LOW')
        self.assertEqual(self.risk_assessment._determine_risk_level(10), 'MINIMAL')
    
    def test_calculate_threat_score(self):
        """Test threat score calculation"""
        import pandas as pd
        df = pd.DataFrame(self.sample_events)
        
        score = self.risk_assessment._calculate_threat_score(df)
        
        self.assertIsInstance(score, (int, float))
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_calculate_vulnerability_score(self):
        """Test vulnerability score calculation"""
        import pandas as pd
        df = pd.DataFrame(self.sample_events)
        
        score = self.risk_assessment._calculate_vulnerability_score(df)
        
        self.assertIsInstance(score, (int, float))
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_calculate_frequency_score(self):
        """Test frequency score calculation"""
        import pandas as pd
        df = pd.DataFrame(self.sample_events)
        
        score = self.risk_assessment._calculate_frequency_score(df)
        
        self.assertIsInstance(score, (int, float))
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_calculate_confidence(self):
        """Test confidence calculation"""
        import pandas as pd
        df = pd.DataFrame(self.sample_events)
        
        confidence = self.risk_assessment._calculate_confidence(df)
        
        self.assertIsInstance(confidence, (int, float))
        self.assertGreaterEqual(confidence, 0)
        self.assertLessEqual(confidence, 1)
    
    def test_generate_risk_breakdown(self):
        """Test risk breakdown generation"""
        import pandas as pd
        df = pd.DataFrame(self.sample_events)
        
        breakdown = self.risk_assessment._generate_risk_breakdown(df)
        
        self.assertIsInstance(breakdown, dict)
        self.assertIn('by_severity', breakdown)
        self.assertIn('by_service', breakdown)
        self.assertIn('by_source', breakdown)
        self.assertIn('timeline', breakdown)
    
    def test_generate_risk_recommendations(self):
        """Test risk recommendations generation"""
        recommendations = self.risk_assessment._generate_risk_recommendations(85, 'CRITICAL')
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        self.assertIn('Immediate incident response activation required', recommendations)
        
        # Test different risk levels
        low_recs = self.risk_assessment._generate_risk_recommendations(25, 'LOW')
        self.assertIsInstance(low_recs, list)
        self.assertGreater(len(low_recs), 0)
    
    def test_generate_service_recommendations(self):
        """Test service-specific recommendations"""
        ssh_recs = self.risk_assessment._generate_service_recommendations('ssh', 'HIGH')
        
        self.assertIsInstance(ssh_recs, list)
        self.assertGreater(len(ssh_recs), 0)
        
        # Should include SSH-specific recommendations
        ssh_specific = any('ssh' in rec.lower() or 'key-based' in rec.lower() for rec in ssh_recs)
        self.assertTrue(ssh_specific)
    
    def test_error_handling(self):
        """Test error handling in risk assessment"""
        # Test with malformed events
        malformed_events = [{'invalid': 'data'}]
        
        result = self.risk_assessment.calculate_overall_risk_score(malformed_events)
        
        # Should handle gracefully and return valid result
        self.assertIsInstance(result, dict)
        self.assertIn('overall_risk_score', result)

def run_risk_assessment_tests():
    """Run all risk assessment tests"""
    print("🧪 Testing RiskAssessment Class")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRiskAssessment)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All RiskAssessment tests passed!")
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
    run_risk_assessment_tests()