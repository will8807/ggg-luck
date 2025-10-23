"""Example usage of Yahoo Fantasy API with HTTPS OAuth flow."""

from ggg_luck.yahoo_api import YahooFantasyAPI
from ggg_luck.oauth_server import get_authorization_code_interactive


def main():
    """Example of how to use the Yahoo Fantasy API with automatic OAuth flow."""
    try:
        # Initialize the API client
        api = YahooFantasyAPI()
        
        print("🏈 Yahoo Fantasy API Example")
        print("=" * 40)
        
        # Check if we already have tokens
        if api.access_token:
            print("✅ Using existing access token")
        else:
            # Step 1: Start interactive OAuth flow
            print("🔐 Starting OAuth authorization flow...")
            auth_url = api.get_auth_url()
            
            try:
                # Step 2: Get authorization code automatically via HTTPS server
                auth_code = get_authorization_code_interactive(auth_url, api.redirect_uri)
                
                # Step 3: Exchange code for tokens
                print("🔄 Exchanging authorization code for access token...")
                token_data = api.exchange_code_for_token(auth_code)
                print("✅ Access token obtained successfully!")
                
                # Optionally save tokens to .env for future use
                print(f"💾 Access Token: {api.access_token[:20]}...")
                print(f"💾 Refresh Token: {api.refresh_token[:20]}...")
                print("   (You can save these to your .env file)")
                
            except Exception as oauth_error:
                print(f"❌ OAuth failed: {oauth_error}")
                print("\n🔧 Manual fallback:")
                print(f"1. Visit: {auth_url}")
                print("2. Authorize the app")
                print("3. Copy the 'code' parameter from the callback URL")
                auth_code = input("4. Paste the authorization code here: ")
                
                token_data = api.exchange_code_for_token(auth_code)
                print("✅ Access token obtained successfully!")
        
        print("\n📊 Testing API calls...")
        
        # Step 4: Get user's leagues
        print("🔍 Fetching your fantasy leagues...")
        try:
            leagues = api.get_user_leagues("nfl")
            print("✅ Leagues fetched successfully!")
            
            # Display league information
            display_leagues_info(leagues)
            
            # If we have leagues, get more detailed info
            if leagues and 'fantasy_content' in leagues:
                league_key = extract_first_league_key(leagues)
                if league_key:
                    print(f"\n📈 Getting detailed info for league: {league_key}")
                    
                    # Get standings
                    try:
                        standings = api.get_league_standings(league_key)
                        display_standings(standings)
                    except Exception as e:
                        print(f"⚠️  Could not fetch standings: {e}")
                    
        except Exception as api_error:
            print(f"❌ API call failed: {api_error}")
            if "401" in str(api_error):
                print("🔄 Token might be expired. Try running the example again.")
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\n🔧 Setup checklist:")
        print("1. Create a .env file with your Yahoo API credentials")
        print("2. Set up your app at https://developer.yahoo.com/apps/")
        print("3. Make sure redirect URI matches: https://localhost:8443/callback")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def display_leagues_info(leagues_data):
    """Display formatted league information."""
    print("🔍 Raw leagues data structure:")
    print(f"   Keys: {list(leagues_data.keys()) if isinstance(leagues_data, dict) else 'Not a dict'}")
    
    if not leagues_data:
        print("⚠️  No league data found")
        return
    
    # Handle XML parsed data structure
    if 'fantasy_content' in leagues_data:
        fantasy_content = leagues_data['fantasy_content']
        print(f"🔍 Fantasy content keys: {list(fantasy_content.keys()) if isinstance(fantasy_content, dict) else 'Not a dict'}")
        
        # Try to navigate the XML structure
        try:
            # The structure might be different for XML vs JSON
            if 'users' in fantasy_content:
                users = fantasy_content['users']
                print(f"🔍 Users structure: {users}")
                
                # XML might have different structure
                if isinstance(users, dict) and 'user' in users:
                    user_data = users['user']
                elif isinstance(users, list) and len(users) > 0:
                    user_data = users[0]
                else:
                    print(f"⚠️  Unexpected users structure: {users}")
                    return
                
                print(f"� User data: {user_data}")
                
                # Extract user info
                if isinstance(user_data, dict):
                    if 'nickname' in user_data:
                        print(f"👤 User: {user_data['nickname']}")
                    
                    # Look for games/leagues
                    if 'games' in user_data:
                        games = user_data['games']
                        print(f"🔍 Games structure: {games}")
                        
                        # Parse games structure
                        game_data = None
                        if isinstance(games, dict) and 'game' in games:
                            game_data = games['game']
                        elif isinstance(games, list):
                            game_data = games[0] if games else None
                        
                        if game_data and 'leagues' in game_data:
                            leagues = game_data['leagues']
                            print(f"🔍 Leagues structure: {leagues}")
                            
                            # Parse leagues
                            if isinstance(leagues, dict) and 'league' in leagues:
                                league_list = leagues['league']
                                if isinstance(league_list, list):
                                    print(f"🏆 Found {len(league_list)} league(s):")
                                    for league in league_list:
                                        display_single_league(league)
                                else:
                                    print("🏆 Found 1 league:")
                                    display_single_league(league_list)
                            else:
                                print(f"⚠️  Unexpected leagues structure: {leagues}")
                        else:
                            print("⚠️  No leagues found in games data")
                    else:
                        print("⚠️  No games data found")
                else:
                    print(f"⚠️  Unexpected user data structure: {type(user_data)}")
            else:
                print("⚠️  No users data found")
                
        except Exception as e:
            print(f"❌ Error parsing league data: {e}")
            print(f"🔍 Full data dump: {leagues_data}")
    else:
        print("⚠️  No fantasy_content found")
        print(f"🔍 Available keys: {list(leagues_data.keys()) if isinstance(leagues_data, dict) else 'Not a dict'}")


def display_single_league(league):
    """Display information for a single league."""
    try:
        name = league.get('name', 'Unknown League')
        league_id = league.get('league_id', 'Unknown')
        league_key = league.get('league_key', 'Unknown')
        num_teams = league.get('num_teams', 'Unknown')
        
        print(f"   📋 {name}")
        print(f"      ID: {league_id}")
        print(f"      Key: {league_key}")
        print(f"      Teams: {num_teams}")
    except Exception as e:
        print(f"   ❌ Error displaying league: {e}")
        print(f"   🔍 League data: {league}")


def extract_first_league_key(leagues_data):
    """Extract the first league key for detailed queries."""
    try:
        fantasy_content = leagues_data['fantasy_content']
        user_data = fantasy_content['users']['0']['user'][1]['user']
        games = user_data['games']['0']['game'][1]['leagues']
        
        if games and games.get('count', 0) > 0 and '0' in games:
            return games['0']['league'][0].get('league_key')
    except (KeyError, IndexError):
        pass
    return None


def display_standings(standings_data):
    """Display formatted standings information."""
    try:
        if 'fantasy_content' in standings_data:
            league = standings_data['fantasy_content']['league'][1]['league']
            standings = league.get('standings')
            
            if standings and standings.get('count', 0) > 0:
                print(f"🏆 League Standings:")
                
                for i in range(standings['count']):
                    if str(i) in standings:
                        team = standings[str(i)]['team']
                        team_info = team[0][2]['team']
                        team_stats = team[1]['team_standings']
                        
                        rank = team_stats.get('rank', 'N/A')
                        name = team_info.get('name', 'Unknown Team')
                        wins = team_stats.get('outcome_totals', {}).get('wins', 0)
                        losses = team_stats.get('outcome_totals', {}).get('losses', 0)
                        
                        print(f"   {rank}. {name} ({wins}-{losses})")
            else:
                print("⚠️  No standings data available")
    except (KeyError, IndexError) as e:
        print(f"⚠️  Could not parse standings data: {e}")


if __name__ == "__main__":
    main()