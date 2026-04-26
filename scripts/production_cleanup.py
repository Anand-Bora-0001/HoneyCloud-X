import os
import shutil
import sys
import io
from pathlib import Path

def cleanup():
    """
    Cleans up local files that should not be included in a production deployment.
    Safely removes SQLite databases, logs, and temporary reports.
    """
    # Fix Windows console encoding for emoji support
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    project_root = Path(__file__).resolve().parent.parent
    
    # 1. Files to delete
    files_to_remove = [
        "honeycloud.db",
        "honeycloud.db-shm",
        "honeycloud.db-wal",
        "backend/honeycloud.db",
        ".pytest_cache",
        ".coverage",
        "ATTACK_GUIDE.md",
        "Dockerfile",
        "docker-compose.yml",
        "INFO.readme",
        "audit.py",
        "diagnostic.py",
        "run_all_manual_attacks.py",
        "simulate_attacks.py",
        "RENDER_DEPLOYMENT.md",
        ".env.example",
        ".env.production.example",
        "demo-ecommerce/advanced_attack_simulation.py",
        "demo-ecommerce/full_e2e_test.py",
        "demo-ecommerce/monitored_attack_simulation.py",
        "demo-ecommerce/test_honeypots.py",
    ]
    
    # 2. Directories to empty or delete
    dirs_to_remove = [
        "k8s",
        "docs",
        "tests",
        "scratch",
    ]

    dirs_to_empty = [
        "logs",
        "reports",
        "backend/logs",
        "backend/reports",
        "demo-ecommerce/__pycache__",
        "backend/app/__pycache__",
        "models",
    ]

    print(f"🚀 Starting Production Cleanup in: {project_root}")
    print("-" * 50)

    # Remove files
    for file_path in files_to_remove:
        full_path = project_root / file_path
        if full_path.exists():
            try:
                if full_path.is_file():
                    os.remove(full_path)
                    print(f"✅ Removed file: {file_path}")
                else:
                    shutil.rmtree(full_path)
                    print(f"✅ Removed directory: {file_path}")
            except Exception as e:
                print(f"❌ Failed to remove {file_path}: {e}")

    # Remove directories
    for dir_path in dirs_to_remove:
        full_path = project_root / dir_path
        if full_path.exists():
            try:
                shutil.rmtree(full_path)
                print(f"✅ Deleted directory: {dir_path}")
            except Exception as e:
                print(f"❌ Failed to delete {dir_path}: {e}")

    # Empty directories
    for dir_path in dirs_to_empty:
        full_path = project_root / dir_path
        if full_path.exists():
            try:
                # Instead of deleting the dir, we delete its contents
                for item in full_path.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                print(f"✅ Emptied directory: {dir_path}")
            except Exception as e:
                print(f"❌ Failed to empty {dir_path}: {e}")

    print("-" * 50)
    print("✨ Cleanup complete! Your repository is ready for production push.")
    print("💡 Remember: Environment variables like DATABASE_URL should be set in Render, not in .env files.")

if __name__ == "__main__":
    cleanup()
