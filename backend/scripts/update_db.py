#!/usr/bin/env python3
"""
Database Schema Update for HoneyCloud-X
Applies migrations to add new notification preference and statistics columns.
"""
import sys
import os
from sqlalchemy import text

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, init_db

def apply_migrations():
    print("⏳ Running database schema migrations...")
    
    # Ensure tables are created
    init_db()
    
    columns_to_add = [
        ("daily_summary_enabled", "BOOLEAN DEFAULT 0"),
        ("weekly_report_enabled", "BOOLEAN DEFAULT 0"),
        ("email_alerts_sent", "INTEGER DEFAULT 0"),
        ("telegram_alerts_sent", "INTEGER DEFAULT 0"),
        ("failed_deliveries", "INTEGER DEFAULT 0"),
        ("last_email_sent_at", "TIMESTAMP"),
        ("last_telegram_sent_at", "TIMESTAMP")
    ]
    
    with engine.connect() as conn:
        for col_name, col_type in columns_to_add:
            try:
                # SQLite syntax for adding column
                conn.execute(text(f"ALTER TABLE notification_configs ADD COLUMN {col_name} {col_type}"))
                print(f"✅ Added column: {col_name}")
            except Exception as e:
                # If column already exists, it will throw an error
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"ℹ️ Column already exists: {col_name} (skipped)")
                else:
                    print(f"⚠️ Failed to add column {col_name}: {e}")
        
        conn.commit()
    print("🎉 Migrations complete!")

if __name__ == "__main__":
    apply_migrations()
