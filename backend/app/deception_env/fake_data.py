
import random
from datetime import datetime, timedelta

class FakeDataGenerator:
    def __init__(self):
        self.products = [
            {"id": "PROD-100", "name": "Enterprise Firewall Appliance", "price": 4999.99, "stock": 14},
            {"id": "PROD-101", "name": "Secure Gateway License", "price": 999.00, "stock": 999},
            {"id": "PROD-102", "name": "Data Center Switch 48-port", "price": 2499.50, "stock": 5},
            {"id": "PROD-103", "name": "VPN Aggregator", "price": 3150.00, "stock": 12},
        ]
        
        self.customers = [
            {"id": "CUST-001", "name": "Acme Corp", "email": "admin@acme.local", "status": "Active", "spend": 15000},
            {"id": "CUST-002", "name": "Global Tech", "email": "it@globaltech.local", "status": "Active", "spend": 45000},
            {"id": "CUST-003", "name": "Synergy Inc", "email": "billing@synergy.local", "status": "Suspended", "spend": 250},
        ]

    def get_products(self):
        return self.products

    def get_customers(self):
        return self.customers

    def get_sales_stats(self):
        return {
            "monthly_revenue": "$145,230.00",
            "active_subscriptions": 1243,
            "churn_rate": "1.2%"
        }
        
fake_db = FakeDataGenerator()
