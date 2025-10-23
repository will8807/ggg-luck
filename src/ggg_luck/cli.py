"""Simple CLI script to test Yahoo Fantasy API connection."""

import sys
from ggg_luck.yahoo_api import YahooFantasyAPI


def test_credentials():
    """Test if Yahoo API credentials are properly configured."""
    try:
        api = YahooFantasyAPI()
        print("✅ Yahoo API credentials found!")
        print(f"   Client ID: {api.client_id[:10]}...")
        print(f"   Redirect URI: {api.redirect_uri}")
        return True
    except ValueError as e:
        print(f"❌ {e}")
        return False


def show_auth_instructions():
    """Show instructions for setting up Yahoo API authentication."""
    print("\n📋 Setup Instructions:")
    print("=" * 50)
    print("1. Go to https://developer.yahoo.com/apps/")
    print("2. Create a new app with these settings:")
    print("   - Application Type: Web Application")
    print("   - Callback Domain: localhost")
    print("   - API Permissions: Fantasy Sports (Read)")
    print("3. Copy .env.example to .env")
    print("4. Fill in your Client ID and Client Secret in .env")
    print("5. Run this script again to test the connection")


def main():
    """Main CLI function."""
    print("Yahoo Fantasy API Connection Test")
    print("=" * 40)
    
    if test_credentials():
        try:
            api = YahooFantasyAPI()
            auth_url = api.get_auth_url()
            
            print("\n🔗 Ready to authenticate!")
            print(f"   Authorization URL: {auth_url}")
            print("\n💡 Next steps:")
            print("   1. Visit the URL above")
            print("   2. Authorize the app")
            print("   3. Use the example.py script to complete authentication")
            
        except Exception as e:
            print(f"❌ Error generating auth URL: {e}")
    else:
        show_auth_instructions()


if __name__ == "__main__":
    main()