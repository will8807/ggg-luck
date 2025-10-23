#!/usr/bin/env python3
"""
Local testing script for GitHub Actions workflow.
Use this to test your luck analysis locally before deploying to GitHub Actions.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def check_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        'YAHOO_CLIENT_ID',
        'YAHOO_CLIENT_SECRET',
        'YAHOO_REDIRECT_URI'
    ]
    
    optional_vars = [
        'YAHOO_ACCESS_TOKEN',
        'YAHOO_REFRESH_TOKEN'
    ]
    
    print("🔍 Checking environment variables...")
    
    missing_required = []
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
        else:
            print(f"✅ {var}: Set")
    
    for var in optional_vars:
        if os.getenv(var):
            print(f"✅ {var}: Set (optional)")
        else:
            print(f"⚠️  {var}: Not set (optional)")
    
    if missing_required:
        print(f"\n❌ Missing required environment variables:")
        for var in missing_required:
            print(f"   - {var}")
        print(f"\nPlease set these in your .env file or environment.")
        return False
    
    print(f"\n✅ All required environment variables are set!")
    return True

def check_uv_installation():
    """Check if uv is installed and available."""
    print("\n🔧 Checking uv installation...")
    
    import subprocess
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ uv: Installed ({result.stdout.strip()})")
            return True
        else:
            print("❌ uv: Not working properly")
            return False
    except FileNotFoundError:
        print("❌ uv: Not installed")
        print("   Install with: pip install uv")
        return False

def check_dependencies():
    """Check if all required packages are installed."""
    print("\n📦 Checking dependencies...")
    
    # First check if uv is available
    if not check_uv_installation():
        print("\n⚠️  uv not found, checking with pip...")
    
    try:
        import requests
        print("✅ requests: Installed")
    except ImportError:
        print("❌ requests: Missing")
        return False
    
    try:
        import yahoo_fantasy_api
        print("✅ yahoo-fantasy-api: Installed")
    except ImportError:
        print("❌ yahoo-fantasy-api: Missing")
        return False
    
    try:
        import matplotlib
        print("✅ matplotlib: Installed")
    except ImportError:
        print("❌ matplotlib: Missing")
        return False
    
    try:
        import seaborn
        print("✅ seaborn: Installed")
    except ImportError:
        print("❌ seaborn: Missing")
        return False
    
    print("✅ All dependencies installed!")
    return True

def create_directories():
    """Create required directories if they don't exist."""
    print("\n📁 Creating required directories...")
    
    dirs_to_create = ['charts', 'reports']
    
    for dir_name in dirs_to_create:
        path = Path(dir_name)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {dir_name}")
        else:
            print(f"✅ Directory exists: {dir_name}")

def run_analysis():
    """Run the main luck analysis."""
    print("\n🏈 Running luck analysis...")
    
    try:
        # Import and run main function
        from main import main
        main()
        print("✅ Analysis completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        return False

def main():
    """Main function to run all checks and analysis."""
    print("🚀 GitHub Actions Local Testing Script")
    print("=" * 50)
    
    # Load environment variables from .env file if it exists
    env_file = Path('.env')
    if env_file.exists():
        print("📄 Loading .env file...")
        load_dotenv()
    else:
        print("⚠️  No .env file found (using system environment)")
    
    # Run all checks
    checks_passed = 0
    total_checks = 3
    
    if check_environment():
        checks_passed += 1
    
    if check_dependencies():
        checks_passed += 1
    
    create_directories()  # This always succeeds
    checks_passed += 1
    
    print(f"\n📊 Checks Summary: {checks_passed}/{total_checks} passed")
    
    if checks_passed == total_checks:
        print("\n🎉 All checks passed! Running analysis...")
        if run_analysis():
            print("\n🏆 Success! Your setup is ready for GitHub Actions.")
            print("\n📋 Next steps:")
            print("1. Push your code to GitHub")
            print("2. Add repository secrets (see GITHUB_ACTIONS_SETUP.md)")
            print("3. Trigger the workflow manually or wait for Tuesday")
        else:
            print("\n❌ Analysis failed. Please check the error messages above.")
            print("\n💡 Common solutions:")
            print("   - Run: uv sync --dev")
            print("   - Check your .env file or environment variables")
            print("   - Verify Yahoo API credentials are correct")
            sys.exit(1)
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        print("\n💡 To fix dependencies, run:")
        print("   uv sync --dev")
        print("\n💡 To fix environment variables:")
        print("   - Create a .env file with your Yahoo API credentials")
        print("   - See GITHUB_ACTIONS_SETUP.md for required variables")
        sys.exit(1)

if __name__ == "__main__":
    main()