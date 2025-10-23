"""Debug Yahoo API setup and URLs."""

import urllib.parse
from ggg_luck.api import YahooFantasyAPI


def analyze_url_components():
    """Analyze and display URL components for debugging."""
    try:
        api = YahooFantasyAPI()
        
        print("🔍 Yahoo API Configuration Analysis")
        print("=" * 50)
        
        print(f"✅ Client ID: {api.client_id[:20]}... (length: {len(api.client_id)})")
        print(f"✅ Client Secret: {'*' * 10}... (length: {len(api.client_secret)})")
        print(f"📍 Redirect URI: {api.redirect_uri}")
        if api.app_id:
            print(f"🆔 App ID: {api.app_id}")
        else:
            print("ℹ️  App ID: Not set (optional for Fantasy Sports API)")
        
        print("\n🔗 Authorization URL Breakdown:")
        print("-" * 30)
        
        auth_url = api.get_auth_url()
        parsed = urllib.parse.urlparse(auth_url)
        params = urllib.parse.parse_qs(parsed.query)
        
        print(f"Base URL: {parsed.scheme}://{parsed.netloc}{parsed.path}")
        print("\nParameters:")
        for key, value in params.items():
            print(f"  {key}: {value[0]}")
        
        print(f"\n🌐 Full URL:")
        print(auth_url)
        
        print(f"\n📋 URL Length: {len(auth_url)} characters")
        
        # Check for common issues
        print(f"\n🔧 Troubleshooting Checklist:")
        print("-" * 25)
        
        issues = []
        
        if len(api.client_id) < 50:
            issues.append("⚠️  Client ID seems short - make sure it's the full OAuth Client ID")
        else:
            print("✅ Client ID length looks correct")
            
        if 'localhost' not in api.redirect_uri:
            issues.append("⚠️  Redirect URI should contain 'localhost' for development")
        else:
            print("✅ Redirect URI contains localhost")
            
        if api.redirect_uri.startswith('https://localhost'):
            issues.append("⚠️  Consider using 'http://localhost' instead of 'https://localhost'")
            
        if len(auth_url) > 2000:
            issues.append("⚠️  URL is very long - some browsers may truncate it")
        else:
            print("✅ URL length is acceptable")
        
        if issues:
            print("\nPotential Issues:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print("\n🎉 Configuration looks good!")
            
        print(f"\n💡 Next Steps:")
        print("1. Copy the URL above")
        print("2. Paste it in your browser")
        print("3. If it doesn't work, check your Yahoo Developer Console:")
        print("   - App settings match your redirect URI")
        print("   - App has Fantasy Sports permissions")
        print("   - Client ID matches exactly")
        
    except Exception as e:
        print(f"❌ Error analyzing configuration: {e}")


def test_redirect_variations():
    """Test different redirect URI formats."""
    print(f"\n🔄 Testing Redirect URI Variations:")
    print("-" * 40)
    
    variations = [
        "http://localhost",
        "http://localhost:8080",
        "http://localhost:8080/callback", 
        "https://localhost",
        "https://localhost:8080",
        "https://localhost:8080/callback"
    ]
    
    for uri in variations:
        print(f"📍 {uri}")
        encoded = urllib.parse.quote(uri, safe=':/?#[]@!$&\'()*+,;=')
        print(f"   Encoded: {encoded}")


if __name__ == "__main__":
    analyze_url_components()
    test_redirect_variations()