"""CLI tool for generating team analysis prompts."""

import argparse
import sys
import os
from typing import Optional
from ggg_luck.api import YahooFantasyAPI
from ggg_luck.team_analyzer import TeamAnalyzer


def analyze_team(league_key: str, team_identifier: str, week: Optional[int] = None, 
                output_file: Optional[str] = None, include_trades: bool = True) -> None:
    """Analyze a team and generate LLM prompt."""
    try:
        # Initialize API
        api = YahooFantasyAPI()
        if not api.access_token:
            print("❌ No access token found.")
            print("🔧 Please authenticate first by running:")
            print("   uv run python -m ggg_luck.cli_tools.example")
            print("   This will save your authentication tokens for future use.")
            return
        
        # Initialize team analyzer
        analyzer = TeamAnalyzer(api)
        
        print(f"🔍 Finding team '{team_identifier}' in league {league_key}...")
        
        # Get all teams to find the target team
        teams = analyzer.get_league_teams(league_key)
        
        if not teams:
            print("❌ No teams found in league")
            return
            
        # Find team by ID or name
        target_team = None
        
        # First try exact ID match
        for team in teams:
            if team['team_id'] == team_identifier:
                target_team = team
                break
        
        # If no ID match, try name matching (case-insensitive)
        if not target_team:
            for team in teams:
                if team['name'].lower() == team_identifier.lower():
                    target_team = team
                    break
        
        # If still no match, try partial name matching
        if not target_team:
            matching_teams = []
            for team in teams:
                if team_identifier.lower() in team['name'].lower():
                    matching_teams.append(team)
            
            if len(matching_teams) == 1:
                target_team = matching_teams[0]
            elif len(matching_teams) > 1:
                print(f"❌ Multiple teams match '{team_identifier}':")
                for team in matching_teams:
                    print(f"  - {team['name']} (ID: {team['team_id']})")
                print("💡 Please be more specific or use the exact team name")
                return
        
        if not target_team:
            print(f"❌ Team '{team_identifier}' not found in league")
            print("📋 Available teams:")
            for team in teams:
                print(f"  - {team['name']} (ID: {team['team_id']})")
            return
        
        team_id = target_team['team_id']
        team_name = target_team['name']
        
        print(f"✅ Found team: {team_name} (ID: {team_id})")
        print(f"🔍 Analyzing team '{team_name}' in league {league_key}...")
        
        # Get complete league data
        league_data = analyzer.get_complete_league_data(league_key, week)
        
        # Generate analysis prompt
        prompt = analyzer.generate_team_analysis_prompt(team_id, league_data, league_key, include_trades)
        
        # Save or print the prompt
        if output_file:
            analyzer.save_analysis_prompt(prompt, output_file)
        else:
            # Generate default filename with team name
            safe_team_name = "".join(c for c in team_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_team_name = safe_team_name.replace(' ', '_')
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"team_analysis_{safe_team_name}_{timestamp}.txt"
            analyzer.save_analysis_prompt(prompt, default_filename)
            output_file = default_filename
        
        print(f"\n✅ Team analysis prompt generated successfully!")
        print(f"📄 Saved to: {output_file}")
        print(f"🎯 Analysis for: {team_name}")
        print(f"\n💡 You can now copy the content of this file to your favorite LLM (ChatGPT, Claude, etc.) for analysis.")
        
    except Exception as e:
        print(f"❌ Error analyzing team: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def list_teams(league_key: str) -> None:
    """List all teams in the league with their IDs."""
    try:
        # Initialize API
        api = YahooFantasyAPI()
        if not api.access_token:
            print("❌ No access token found.")
            print("🔧 Please authenticate first by running:")
            print("   uv run python -m ggg_luck.cli_tools.example")
            print("   This will save your authentication tokens for future use.")
            return
        
        # Initialize team analyzer
        analyzer = TeamAnalyzer(api)
        
        print(f"🔍 Fetching teams for league {league_key}...")
        
        # Get all teams
        teams = analyzer.get_league_teams(league_key)
        
        if not teams:
            print("❌ No teams found in league")
            return
            
        print(f"\n📋 Teams in League {league_key}:")
        print("=" * 50)
        
        for team in teams:
            wins = team.get('wins', 0)
            losses = team.get('losses', 0)
            points_for = team.get('points_for', 0)
            manager = team.get('manager', 'Unknown')
            
            print(f"Team ID: {team['team_id']}")
            print(f"  Name: {team['name']}")
            print(f"  Manager: {manager}")
            print(f"  Record: {wins}-{losses}")
            print(f"  Points For: {points_for}")
            print()
        
        print("💡 Use either the Team Name or Team ID to analyze a specific team:")
        print(f"   python -m ggg_luck.cli_tools.team_analysis --league {league_key} --team \"<TEAM_NAME>\"")
        print(f"   python -m ggg_luck.cli_tools.team_analysis --league {league_key} --team <TEAM_ID>")
        
    except Exception as e:
        print(f"❌ Error listing teams: {e}")
        sys.exit(1)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Generate fantasy football team analysis prompts for LLMs")
    parser.add_argument("--league", "-l", required=True, help="Yahoo league key")
    parser.add_argument("--team", "-t", help="Team name or ID to analyze")
    parser.add_argument("--week", "-w", type=int, help="Week number (current week if not specified)")
    parser.add_argument("--output", "-o", help="Output file path for the prompt")
    parser.add_argument("--list-teams", action="store_true", help="List all teams in the league")
    parser.add_argument("--include-trades", action="store_true", default=True, 
                       help="Include trade analysis with other team rosters (default: True)")
    parser.add_argument("--no-trades", action="store_true", 
                       help="Exclude trade analysis and other team rosters")
    
    args = parser.parse_args()
    
    print("Fantasy Football Team Analyzer")
    print("=" * 40)
    
    if args.list_teams:
        list_teams(args.league)
    elif args.team:
        # Determine if trades should be included
        include_trades = not args.no_trades
        analyze_team(args.league, args.team, args.week, args.output, include_trades)
    else:
        print("❌ Please specify either --team <TEAM_NAME> or --list-teams")
        print("💡 Use --list-teams to see all team names in the league first")
        print("💡 You can use either team name or team ID with --team")
        print("💡 Use --no-trades to exclude trade analysis (useful for privacy)")
        print("💡 Examples:")
        print(f"   uv run python -m ggg_luck.cli_tools.team_analysis -l {args.league} --list-teams")
        print(f"   uv run python -m ggg_luck.cli_tools.team_analysis -l {args.league} -t \"Team Name\"")
        print(f"   uv run python -m ggg_luck.cli_tools.team_analysis -l {args.league} -t \"Team Name\" --no-trades")
        sys.exit(1)


if __name__ == "__main__":
    main()