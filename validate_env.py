#!/usr/bin/env python3
"""
Environment Variables Validation Script
Run this to check if all required environment variables are properly set
"""

import os
import sys
from typing import Dict, List, Tuple

def validate_environment() -> Tuple[bool, List[str]]:
    """Validate all required environment variables are set"""
    
    required_vars = {
        'MAIL_USERNAME': 'Email address for sending contact form emails',
        'MAIL_PASSWORD': 'App password for email account',
        'RECAPTCHA_SITE_KEY': 'Google reCAPTCHA site key',
        'RECAPTCHA_SECRET_KEY': 'Google reCAPTCHA secret key',
    }

    
    issues = []
    all_good = True
    
    print("🔍 Validating Environment Variables...\n")
    
    print("📋 Required Variables:")
    for var, description in required_vars.items():
        value = os.environ.get(var)
        if not value:
            print(f"❌ {var}: MISSING")
            issues.append(f"Missing required variable: {var} ({description})")
            all_good = False
        else:
            display_value = value[:10] + "..." if len(value) > 10 else value
            if 'PASSWORD' in var or 'SECRET' in var or 'KEY' in var:
                display_value = "*" * min(len(value), 20)
            print(f"✅ {var}: {display_value}")
    
    print("\n📋 Optional Variables:")
    for var, description in optional_vars.items():
        value = os.environ.get(var)
        if value:
            display_value = value
            if 'PASSWORD' in var or 'SECRET' in var or 'KEY' in var:
                display_value = "*" * min(len(value), 20)
            print(f"✅ {var}: {display_value}")
        else:
            print(f"⚠️  {var}: Not set (optional)")
    
    print("\n🔧 Validating Formats:")
    
    email = os.environ.get('MAIL_USERNAME')
    if email and '@' not in email:
        issues.append("MAIL_USERNAME should be a valid email address")
        print(f"❌ MAIL_USERNAME: Invalid email format")
    elif email:
        print(f"✅ MAIL_USERNAME: Valid email format")
    
    secret_key = os.environ.get('SECRET_KEY')
    if secret_key and len(secret_key) < 32:
        issues.append("SECRET_KEY should be at least 32 characters long")
        print(f"❌ SECRET_KEY: Too short (should be 32+ chars)")
    elif secret_key:
        print(f"✅ SECRET_KEY: Good length ({len(secret_key)} chars)")
    
    site_key = os.environ.get('RECAPTCHA_SITE_KEY')
    if site_key and not site_key.startswith('6L'):
        issues.append("RECAPTCHA_SITE_KEY should start with '6L'")
        print(f"❌ RECAPTCHA_SITE_KEY: Invalid format")
    elif site_key:
        print(f"✅ RECAPTCHA_SITE_KEY: Valid format")
    
    secret_key_recaptcha = os.environ.get('RECAPTCHA_SECRET_KEY')
    if secret_key_recaptcha and not secret_key_recaptcha.startswith('6L'):
        issues.append("RECAPTCHA_SECRET_KEY should start with '6L'")
        print(f"❌ RECAPTCHA_SECRET_KEY: Invalid format")
    elif secret_key_recaptcha:
        print(f"✅ RECAPTCHA_SECRET_KEY: Valid format")
    
    return all_good, issues


def main():
    print("🚀 Portfolio Environment Variables Checker\n")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--generate-sample':
        generate_sample_env()
        return
    
    env_files = ['.env', '.env.local']
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"📁 Loading {env_file}")
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
            break
    
    all_good, issues = validate_environment()
    
    print(f"\n📊 Validation Results:")
    if all_good:
        print("✅ All environment variables are properly configured!")
        print("🚀 Your contact form should work correctly.")
    else:
        print("❌ Some issues found:")
        for issue in issues:
            print(f"   • {issue}")
        print(f"\n🔧 Please fix these issues before deploying.")
        sys.exit(1)

if __name__ == "__main__":
    main()