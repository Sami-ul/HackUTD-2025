#!/usr/bin/env python3
"""
Quick setup verification script
Run this to check if everything is configured correctly
"""

import os
import sys

def check_env_var(name, required=True):
    """Check if environment variable is set"""
    value = os.getenv(name)
    if value:
        # Mask sensitive data
        if 'KEY' in name or 'TOKEN' in name:
            display_value = value[:10] + "..." if len(value) > 10 else "***"
        else:
            display_value = value
        print(f"✅ {name}: {display_value}")
        return True
    else:
        if required:
            print(f"❌ {name}: NOT SET")
        else:
            print(f"⚠️  {name}: NOT SET (optional)")
        return not required

def check_module(name):
    """Check if Python module is installed"""
    try:
        __import__(name)
        print(f"✅ {name}: installed")
        return True
    except ImportError:
        print(f"❌ {name}: NOT INSTALLED")
        return False

def main():
    print("=" * 60)
    print("🔍 Conversational Voice AI - Setup Verification")
    print("=" * 60)
    
    all_good = True
    
    # Check environment variables
    print("\n📋 Environment Variables:")
    all_good &= check_env_var("TWILIO_ACCOUNT_SID")
    all_good &= check_env_var("TWILIO_AUTH_TOKEN")
    all_good &= check_env_var("TWILIO_PHONE_NUMBER", required=False)
    all_good &= check_env_var("OPENROUTER_API_KEY")
    all_good &= check_env_var("ELEVENLABS_API_KEY")
    
    # Check Python modules
    print("\n📦 Python Packages:")
    all_good &= check_module("flask")
    all_good &= check_module("flask_sock")
    all_good &= check_module("twilio")
    all_good &= check_module("nemo")
    all_good &= check_module("torch")
    all_good &= check_module("elevenlabs")
    all_good &= check_module("openai")
    all_good &= check_module("numpy")
    
    # Check files
    print("\n📁 Required Files:")
    required_files = [
        "voice_conversational.py",
        "nemotron_agent.py",
        "nemo_intent_model.py",
        "audio_processor.py",
        "tts_handler.py",
        "tools.py",
        "mock_database.py",
        "config.py"
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}: exists")
        else:
            print(f"❌ {file}: MISSING")
            all_good = False
    
    # Final status
    print("\n" + "=" * 60)
    if all_good:
        print("✅ All checks passed! You're ready to run:")
        print("   python3 voice_conversational.py")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\nQuick fixes:")
        print("  • Set env vars: export VARNAME=value")
        print("  • Install packages: pip3 install -r requirements.txt")
    print("=" * 60)
    
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())

