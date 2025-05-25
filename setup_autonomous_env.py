#!/usr/bin/env python3
"""
Setup script for Autonomous Bitcoin Prediction Agent
Prepares the environment for local autonomous operation with git integration.
"""

import os
import subprocess
import sys
from pathlib import Path

def setup_environment():
    """Setup the environment for autonomous operation."""
    print("🔧 Setting up Autonomous Bitcoin Prediction Environment")
    print("=" * 55)
    
    # Check if we're in a git repository
    if not Path(".git").exists():
        print("📁 Initializing git repository...")
        try:
            subprocess.run(["git", "init"], check=True)
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run([
                "git", "commit", "-m", 
                "Initial commit - Autonomous Bitcoin Prediction Agent"
            ], check=True)
            print("✅ Git repository initialized")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to initialize git repository: {e}")
            return False
    else:
        print("✅ Git repository already exists")
    
    # Check if .env file exists
    if not Path(".env").exists():
        if Path("env.example").exists():
            print("📝 Creating .env file from template...")
            import shutil
            shutil.copy("env.example", ".env")
            print("✅ .env file created")
            print("⚠️  Please edit .env file with your API keys:")
            print("   - OPENAI_API_KEY (required for autonomous improvements)")
            print("   - GITHUB_TOKEN (optional, for production mode)")
            print("   - COINGECKO_API_KEY (optional, for real-time data)")
        else:
            print("❌ env.example not found - cannot create .env file")
            return False
    else:
        print("✅ .env file already exists")
    
    # Create necessary directories
    directories = ["logs", "backups/predictor_code"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Check Python dependencies
    print("\n📦 Checking Python dependencies...")
    try:
        import openai
        print("✅ OpenAI library available")
    except ImportError:
        print("❌ OpenAI library missing - autonomous improvements will fail")
    
    try:
        import github
        print("✅ PyGithub library available")
    except ImportError:
        print("⚠️  PyGithub library missing - production mode unavailable")
    
    try:
        import apscheduler
        print("✅ APScheduler library available")
    except ImportError:
        print("❌ APScheduler library missing - scheduling will fail")
    
    print("\n🎯 Environment setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your API keys")
    print("2. Test the system: python3 main.py agent test")
    print("3. Run autonomous operation: python3 main.py agent autonomous --mode local --continuous")
    print("   (Now defaults to 5-minute intervals, aligned with API data granularity)")
    print("4. Or try demo mode: python3 main.py agent demo")
    
    return True

if __name__ == "__main__":
    success = setup_environment()
    sys.exit(0 if success else 1) 