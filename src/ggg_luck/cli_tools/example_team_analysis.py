"""
Example usage of the Team Analysis functionality.

This script demonstrates how to use the new team analysis features
to generate LLM prompts for fantasy football strategic advice.
"""

from ggg_luck.api import YahooFantasyAPI
from ggg_luck.team_analyzer import TeamAnalyzer


def example_team_analysis():
    """Example of how to use the team analysis functionality."""
    
    # Initialize the Yahoo API (assumes you're already authenticated)
    api = YahooFantasyAPI()
    
    # Check if we have an access token
    if not api.access_token:
        print("❌ No access token found.")
        print("💡 Please run the authentication flow first using the existing example.py script")
        return
    
    # Initialize the team analyzer
    analyzer = TeamAnalyzer(api)
    
    # Example league key (replace with your actual league key)
    league_key = "423.l.XXXXXX"  # Replace with your league key
    team_name = "My Team Name"  # Replace with target team name or ID
    
    try:
        print("🔍 Step 1: Fetching all teams in the league...")
        teams = analyzer.get_league_teams(league_key)
        
        print(f"\n📋 Found {len(teams)} teams:")
        for team in teams:
            print(f"  • {team['name']} (ID: {team['team_id']}) - {team.get('wins', 0)}-{team.get('losses', 0)}")
        
        print(f"\n🔍 Step 2: Finding target team '{team_name}'...")
        target_team = analyzer.find_team_by_name_or_id(league_key, team_name)
        
        if not target_team:
            print(f"❌ Could not find team '{team_name}' in league")
            print("📋 Available teams:")
            for team in teams:
                print(f"  • {team['name']} (ID: {team['team_id']})")
            return
        
        team_id = target_team['team_id']
        team_display_name = target_team['name']
        print(f"✅ Found team: {team_display_name} (ID: {team_id})")
        
        print(f"\n🔍 Step 3: Getting complete league data...")
        league_data = analyzer.get_complete_league_data(league_key)
        
        print(f"✅ League: {league_data.league_name}")
        print(f"✅ Teams: {len(league_data.team_rosters)}")
        print(f"✅ Free Agents: {len(league_data.free_agents)}")
        
        print(f"\n🔍 Step 4: Generating analysis prompt for {team_display_name}...")
        prompt = analyzer.generate_team_analysis_prompt(team_id, league_data, league_key)
        
        print(f"\n📄 Step 5: Saving prompt to file...")
        filename = analyzer.save_analysis_prompt(prompt)
        
        print(f"\n✅ Success! Team analysis prompt generated.")
        print(f"📁 File: {filename}")
        print(f"\n💡 Next steps:")
        print(f"   1. Open {filename}")
        print(f"   2. Copy the content")
        print(f"   3. Paste it into ChatGPT, Claude, or your preferred LLM")
        print(f"   4. Get strategic fantasy football advice!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"\n💡 Make sure to:")
        print(f"   1. Replace 'league_key' with your actual Yahoo league key")
        print(f"   2. Replace 'team_name' with the target team's name or ID")
        print(f"   3. Ensure you're authenticated with the Yahoo API")


if __name__ == "__main__":
    example_team_analysis()