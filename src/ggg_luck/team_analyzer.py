"""Team Analysis and LLM Prompt Generator for Fantasy Football."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
from datetime import datetime
from .api import YahooFantasyAPI


@dataclass
class Player:
    """Represents a fantasy football player."""
    player_id: str
    name: str
    position: str
    team: str  # NFL team
    status: str  # roster status (starter, bench, IR, etc.)
    bye_week: Optional[int] = None
    injury_status: Optional[str] = None
    eligibility: Optional[List[str]] = None  # Position eligibilities


@dataclass
class TeamRoster:
    """Represents a fantasy team's roster."""
    team_id: str
    team_name: str
    players: List[Player]
    starting_lineup: List[Player]
    bench_players: List[Player]
    ir_players: List[Player]


@dataclass
class FreeAgent:
    """Represents a free agent player."""
    player_id: str
    name: str
    position: str
    team: str  # NFL team
    ownership_percentage: Optional[float] = None
    bye_week: Optional[int] = None
    injury_status: Optional[str] = None
    eligibility: Optional[List[str]] = None


@dataclass
class LeagueData:
    """Complete league data for analysis."""
    league_id: str
    league_name: str
    team_rosters: List[TeamRoster]
    free_agents: List[FreeAgent]
    waiver_order: Optional[List[str]] = None  # Team IDs in waiver order
    teams_info: Optional[List[Dict[str, Any]]] = None  # Team info with records


class TeamAnalyzer:
    """Analyzes team rosters and generates LLM prompts for fantasy advice."""
    
    def __init__(self, api: YahooFantasyAPI):
        """Initialize the team analyzer with Yahoo API client."""
        self.api = api

    def get_league_teams(self, league_key: str) -> List[Dict[str, Any]]:
        """Get all teams in the league."""
        print(f"🔍 Fetching all teams for league {league_key}...")
        
        standings_data = self.api.get_league_standings(league_key)
        teams = []
        
        try:
            # Navigate the XML structure to get teams
            if 'fantasy_content' not in standings_data:
                raise ValueError("No fantasy content in standings data")
                
            league_data = standings_data['fantasy_content']['league']
            if isinstance(league_data, list):
                league_data = league_data[1]['league']
                
            if 'standings' not in league_data:
                raise ValueError("No standings data found")
                
            standings = league_data['standings']
            if 'teams' not in standings:
                raise ValueError("No teams found in standings")
                
            teams_data = standings['teams']
            if 'team' not in teams_data:
                raise ValueError("No team data found")
                
            team_list = teams_data['team']
            if not isinstance(team_list, list):
                team_list = [team_list]
            
            for team in team_list:
                teams.append({
                    'team_id': team['team_id'],
                    'team_key': team['team_key'],
                    'name': team['name'],
                    'manager': team.get('managers', {}).get('manager', {}).get('nickname', 'Unknown'),
                    'wins': team.get('team_standings', {}).get('outcome_totals', {}).get('wins', 0),
                    'losses': team.get('team_standings', {}).get('outcome_totals', {}).get('losses', 0),
                    'points_for': team.get('team_standings', {}).get('points_for', 0),
                    'points_against': team.get('team_standings', {}).get('points_against', 0),
                })
                
        except (KeyError, IndexError, TypeError, ValueError) as e:
            print(f"⚠️  Error parsing teams data: {e}")
            print(f"🔍  Full standings data structure: {json.dumps(standings_data, indent=2)[:500]}...")
            
        print(f"✅ Found {len(teams)} teams")
        return teams

    def find_team_by_name_or_id(self, league_key: str, identifier: str) -> Optional[Dict[str, Any]]:
        """Find a team by either name or ID."""
        teams = self.get_league_teams(league_key)
        
        if not teams:
            return None
            
        # First try exact ID match
        for team in teams:
            if team['team_id'] == identifier:
                return team
        
        # Then try exact name match (case-insensitive)
        for team in teams:
            if team['name'].lower() == identifier.lower():
                return team
        
        # Finally try partial name match
        matching_teams = []
        for team in teams:
            if identifier.lower() in team['name'].lower():
                matching_teams.append(team)
        
        # Return single match, None if no match or multiple matches
        return matching_teams[0] if len(matching_teams) == 1 else None

    def get_team_roster_data(self, team_key: str, week: Optional[int] = None) -> TeamRoster:
        """Get detailed roster data for a specific team."""
        print(f"🔍 Fetching roster for team {team_key}...")
        
        roster_data = self.api.get_team_roster(team_key, week)
        
        players = []
        starting_lineup = []
        bench_players = []
        ir_players = []
        
        try:
            # Navigate the XML structure to get roster
            if 'fantasy_content' not in roster_data:
                raise ValueError("No fantasy content in roster data")
                
            team_data = roster_data['fantasy_content']['team']
            if isinstance(team_data, list):
                team_data = team_data[1]['team']
                
            team_id = team_data['team_id']
            team_name = team_data['name']
            
            if 'roster' not in team_data:
                raise ValueError("No roster data found")
                
            roster = team_data['roster']
            if 'players' not in roster:
                raise ValueError("No players found in roster")
                
            players_data = roster['players']
            if 'player' not in players_data:
                raise ValueError("No player data found")
                
            player_list = players_data['player']
            if not isinstance(player_list, list):
                player_list = [player_list]
            
            for player_data in player_list:
                # Parse player information
                player_info = player_data
                
                # Get basic player info
                player_id = player_info['player_id']
                name = player_info['name']['full']
                
                # Get position and eligibility
                eligibility = player_info.get('eligible_positions', {}).get('position', [])
                if isinstance(eligibility, str):
                    eligibility = [eligibility]
                elif isinstance(eligibility, dict):
                    eligibility = [eligibility.get('position', 'UNKNOWN')]
                
                position = eligibility[0] if eligibility else 'UNKNOWN'
                
                # Get NFL team
                nfl_team = player_info.get('editorial_team_abbr', 'FA')
                
                # Get roster position (starter, bench, etc.)
                selected_position = player_data.get('selected_position', {})
                if isinstance(selected_position, dict):
                    roster_status = selected_position.get('position', 'BN')
                else:
                    roster_status = 'BN'
                
                # Get injury status
                injury_note = player_info.get('status', '')
                
                # Get bye week
                bye_week = player_info.get('bye_weeks', {})
                if isinstance(bye_week, dict) and 'week' in bye_week:
                    bye_week = int(bye_week['week'])
                else:
                    bye_week = None
                
                player = Player(
                    player_id=player_id,
                    name=name,
                    position=position,
                    team=nfl_team,
                    status=roster_status,
                    bye_week=bye_week,
                    injury_status=injury_note if injury_note else None,
                    eligibility=eligibility
                )
                
                players.append(player)
                
                # Categorize by roster position
                if roster_status in ['QB', 'RB', 'WR', 'TE', 'FLEX', 'K', 'DEF']:
                    starting_lineup.append(player)
                elif roster_status == 'IR':
                    ir_players.append(player)
                else:  # BN or other
                    bench_players.append(player)
                    
        except (KeyError, IndexError, TypeError, ValueError) as e:
            print(f"⚠️  Error parsing roster data for team {team_key}: {e}")
            print(f"🔍  Roster data structure: {json.dumps(roster_data, indent=2)[:500]}...")
            # Return empty roster structure
            team_id = "unknown"
            team_name = "Unknown Team"
            
        return TeamRoster(
            team_id=team_id,
            team_name=team_name,
            players=players,
            starting_lineup=starting_lineup,
            bench_players=bench_players,
            ir_players=ir_players
        )

    def get_free_agents(self, league_key: str, position: Optional[str] = None, 
                       count: int = 50, start: int = 0) -> List[FreeAgent]:
        """Get free agents from the league."""
        print(f"🔍 Fetching free agents for league {league_key}...")
        
        free_agents = []
        
        try:
            # Get free agents using the new API method with ownership sorting
            players_data = self.api.get_league_free_agents(
                league_key=league_key,
                position=position,
                start=start,
                count=count,
                sort="OR"  # Sort by ownership rank
            )
            
            # Navigate the XML structure
            if 'fantasy_content' not in players_data:
                raise ValueError("No fantasy content in players data")
                
            league_data = players_data['fantasy_content']['league']
            if isinstance(league_data, list):
                league_data = league_data[1]['league']
                
            if 'players' not in league_data:
                print("📝 No players data found - might be empty result")
                return free_agents
                
            players_container = league_data['players']
            if 'player' not in players_container:
                print("📝 No player entries found")
                return free_agents
                
            player_list = players_container['player']
            if not isinstance(player_list, list):
                player_list = [player_list]
            
            for player_data in player_list:
                try:
                    # Get basic player info
                    player_id = player_data['player_id']
                    name = player_data['name']['full']
                    
                    # Get position and eligibility
                    eligibility = player_data.get('eligible_positions', {}).get('position', [])
                    if isinstance(eligibility, str):
                        eligibility = [eligibility]
                    elif isinstance(eligibility, dict):
                        eligibility = [eligibility.get('position', 'UNKNOWN')]
                    
                    position_primary = eligibility[0] if eligibility else 'UNKNOWN'
                    
                    # Get NFL team
                    nfl_team = player_data.get('editorial_team_abbr', 'FA')
                    
                    # Get ownership percentage (if available)
                    ownership_pct = player_data.get('percent_owned', {})
                    if isinstance(ownership_pct, dict) and 'value' in ownership_pct:
                        ownership_pct = float(ownership_pct['value'])
                    else:
                        ownership_pct = None
                    
                    # Get bye week
                    bye_week = player_data.get('bye_weeks', {})
                    if isinstance(bye_week, dict) and 'week' in bye_week:
                        bye_week = int(bye_week['week'])
                    else:
                        bye_week = None
                    
                    # Get injury/status
                    injury_note = player_data.get('status', '')
                    
                    # Filter out irrelevant players
                    if self._is_relevant_free_agent(name, position_primary, nfl_team, ownership_pct, injury_note):
                        free_agent = FreeAgent(
                            player_id=player_id,
                            name=name,
                            position=position_primary,
                            team=nfl_team,
                            ownership_percentage=ownership_pct,
                            bye_week=bye_week,
                            injury_status=injury_note if injury_note else None,
                            eligibility=eligibility
                        )
                        
                        free_agents.append(free_agent)
                    
                except (KeyError, IndexError, TypeError, ValueError) as e:
                    print(f"⚠️  Error parsing free agent data: {e}")
                    continue
                    
        except (KeyError, IndexError, TypeError, ValueError) as e:
            print(f"⚠️  Error fetching free agents: {e}")
            print(f"🔍  Players data structure: {json.dumps(players_data, indent=2)[:500]}...")
        
        print(f"✅ Found {len(free_agents)} free agents")
        return free_agents

    def _is_relevant_free_agent(self, name: str, position: str, nfl_team: str, 
                               ownership_pct: Optional[float], injury_status: str) -> bool:
        """Filter out irrelevant free agents."""
        
        # Skip players on IR or suspended
        if injury_status and injury_status.upper() in ['IR', 'SUSP', 'SUS']:
            return False
            
        # Skip free agents (no NFL team)
        if nfl_team in ['FA', '', 'N/A']:
            return False
            
        # Position-specific filtering
        if position == 'QB':
            # Only include QBs with some ownership or known starters/backups
            if ownership_pct is not None and ownership_pct < 0.1:
                return False
            # Skip obvious third-stringers
            excluded_qb_names = ['josh johnson', 'brian hoyer', 'blaine gabbert', 'tyrod taylor']
            if any(excluded in name.lower() for excluded in excluded_qb_names):
                return False
                
        elif position in ['RB', 'WR']:
            # Skip fullbacks and special teamers
            excluded_names = [
                'kyle juszczyk', 'keith smith', 'brandon bolden', 'cordarrelle patterson',
                'latavius murray', 'jerick mckinnon', 'damien williams', 'melvin gordon',
                'randall cobb', 'marvin jones', 'robert woods', 'marquise goodwin'
            ]
            if any(excluded in name.lower() for excluded in excluded_names):
                return False
                
            # For RB/WR, prefer players with at least minimal ownership or recent relevance
            if ownership_pct is not None and ownership_pct < 0.5:
                return False
                
        elif position == 'TE':
            # Skip blocking TEs
            excluded_te_names = ['marcedes lewis', 'jimmy graham', 'blake bell', 'mycole pruitt']
            if any(excluded in name.lower() for excluded in excluded_te_names):
                return False
                
        elif position == 'K':
            # Skip injured or non-active kickers
            if injury_status and injury_status.upper() in ['IR', 'OUT', 'Q']:
                return False
                
        elif position == 'DEF':
            # All defenses are generally relevant
            pass
            
        return True

    def get_complete_league_data(self, league_key: str, week: Optional[int] = None) -> LeagueData:
        """Get complete league data including all team rosters and free agents."""
        print(f"🔍 Fetching complete league data for {league_key}...")
        
        # Get league info
        league_info = self.api.get_league_info(league_key)
        league_name = "Unknown League"
        
        try:
            if 'fantasy_content' in league_info:
                league_data = league_info['fantasy_content']['league']
                if isinstance(league_data, list):
                    league_data = league_data[1]['league']
                league_name = league_data.get('name', 'Unknown League')
        except Exception as e:
            print(f"⚠️  Could not get league name: {e}")
        
        # Get all teams (store this for later use)
        teams = self.get_league_teams(league_key)
        
        # Get rosters for each team
        team_rosters = []
        for team in teams:
            roster = self.get_team_roster_data(team['team_key'], week)
            team_rosters.append(roster)
        
        # Get free agents (top available players across positions)
        free_agents = []
        positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']
        
        for position in positions:
            # Get more players per position to account for filtering
            position_count = 30 if position in ['RB', 'WR'] else 20
            position_free_agents = self.get_free_agents(league_key, position, count=position_count)
            free_agents.extend(position_free_agents)
        
        # Also get some general free agents without position filter for additional coverage
        general_free_agents = self.get_free_agents(league_key, count=100)
        
        # Combine and deduplicate free agents
        all_free_agents = {}
        for fa in free_agents + general_free_agents:
            # Only add if it passes our relevance filter
            if self._is_relevant_free_agent(fa.name, fa.position, fa.team, fa.ownership_percentage, fa.injury_status or ''):
                all_free_agents[fa.player_id] = fa
        
        # Sort by ownership percentage (descending) to prioritize more relevant players
        unique_free_agents = sorted(
            all_free_agents.values(), 
            key=lambda x: x.ownership_percentage if x.ownership_percentage is not None else 0, 
            reverse=True
        )
        
        # Create enhanced LeagueData with team info
        league_data = LeagueData(
            league_id=league_key,
            league_name=league_name,
            team_rosters=team_rosters,
            free_agents=unique_free_agents
        )
        
        # Store teams data for later use
        league_data.teams_info = teams
        
        return league_data

    def generate_team_analysis_prompt(self, target_team_id: str, league_data: LeagueData, league_key: str) -> str:
        """Generate an LLM prompt for analyzing a specific team's potential moves."""
        
        # Find the target team
        target_roster = None
        for roster in league_data.team_rosters:
            if roster.team_id == target_team_id:
                target_roster = roster
                break
        
        if not target_roster:
            raise ValueError(f"Team {target_team_id} not found in league data")
        
        # Build the prompt
        prompt = f"""You are an expert fantasy football advisor. Analyze the following team and provide strategic recommendations for potential moves.

## League Information
- League: {league_data.league_name}
- Target Team: {target_roster.team_name}

## Current Team Roster

### Starting Lineup:
"""
        
        # Add starting lineup
        for player in target_roster.starting_lineup:
            injury_info = f" ({player.injury_status})" if player.injury_status else ""
            bye_info = f" [Bye: {player.bye_week}]" if player.bye_week else ""
            prompt += f"- {player.status}: {player.name} ({player.position}, {player.team}){injury_info}{bye_info}\n"
        
        prompt += "\n### Bench Players:\n"
        
        # Add bench players
        for player in target_roster.bench_players:
            injury_info = f" ({player.injury_status})" if player.injury_status else ""
            bye_info = f" [Bye: {player.bye_week}]" if player.bye_week else ""
            prompt += f"- {player.name} ({player.position}, {player.team}){injury_info}{bye_info}\n"
        
        if target_roster.ir_players:
            prompt += "\n### IR Players:\n"
            for player in target_roster.ir_players:
                injury_info = f" ({player.injury_status})" if player.injury_status else ""
                prompt += f"- {player.name} ({player.position}, {player.team}){injury_info}\n"
        
        prompt += "\n## Available Free Agents (Top Relevant Options by Position)\n"
        prompt += "*Note: Filtered to show fantasy-relevant players with active NFL status and meaningful potential*\n\n"
        
        # Group free agents by position
        fa_by_position = {}
        for fa in league_data.free_agents:
            if fa.position not in fa_by_position:
                fa_by_position[fa.position] = []
            fa_by_position[fa.position].append(fa)
        
        # Sort each position by ownership percentage (if available)
        for position, players in fa_by_position.items():
            players.sort(key=lambda x: x.ownership_percentage or 0, reverse=True)
            # Keep top players per position, but filter for minimum relevance
            relevant_players = []
            for player in players:
                if (player.ownership_percentage is None or player.ownership_percentage >= 0.1 or 
                    len(relevant_players) < 3):  # Always show at least 3 per position
                    relevant_players.append(player)
                if len(relevant_players) >= 10:  # Max 10 per position
                    break
            fa_by_position[position] = relevant_players
        
        # Add free agents to prompt
        for position in ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']:
            if position in fa_by_position and fa_by_position[position]:
                prompt += f"### {position}:\n"
                for fa in fa_by_position[position][:8]:  # Top 8 per position
                    ownership_info = f" ({fa.ownership_percentage:.1f}% owned)" if fa.ownership_percentage is not None else ""
                    injury_info = f" ({fa.injury_status})" if fa.injury_status else ""
                    bye_info = f" [Bye: {fa.bye_week}]" if fa.bye_week else ""
                    prompt += f"- {fa.name} ({fa.team}){ownership_info}{injury_info}{bye_info}\n"
                prompt += "\n"
        
        prompt += "\n## Other Team Rosters (for Trade Analysis)\n\n"
        
        # Add other team rosters with records
        for roster in league_data.team_rosters:
            if roster.team_id != target_team_id:
                # Find team record from the stored teams data
                team_record = ""
                if hasattr(league_data, 'teams_info'):
                    for team in league_data.teams_info:
                        if team['team_id'] == roster.team_id:
                            wins = team.get('wins', 0)
                            losses = team.get('losses', 0)
                            team_record = f" ({wins}-{losses})"
                            break
                
                prompt += f"### {roster.team_name}{team_record}:\n"
                
                # Group players by position
                team_by_position = {}
                for player in roster.players:
                    if player.position not in team_by_position:
                        team_by_position[player.position] = []
                    team_by_position[player.position].append(player)
                
                # Show key positions
                for position in ['QB', 'RB', 'WR', 'TE']:
                    if position in team_by_position:
                        # Show all players for better trade analysis
                        players_str = ", ".join([p.name for p in team_by_position[position]])
                        prompt += f"  {position}: {players_str}\n"
                prompt += "\n"
        
        prompt += """
## Analysis Request

**IMPORTANT: Before providing recommendations, please research current fantasy football stats, trends, and news for Week 12 of the 2025 NFL season. Consider:**
- Recent player performance trends and target shares
- Injury updates and their impact on player values
- Upcoming schedule strength and matchups
- Current waiver wire buzz and emerging players
- Trade deadline implications and team needs across the NFL
- Weather conditions and game environments that could affect scoring

Please provide a comprehensive analysis covering:

1. **Roster Strengths and Weaknesses:**
   - Identify the strongest and weakest positions on the current roster
   - Note any depth concerns or injury risks
   - Assess upcoming bye week challenges

2. **Waiver Wire Opportunities:**
   - Recommend top waiver wire pickups based on team needs
   - Suggest who could be dropped to make room
   - Identify potential breakout candidates or handcuffs

3. **Trade Recommendations:**
   - Suggest realistic trade targets that address team weaknesses
   - Identify players from other teams who might be available
   - Propose specific trade scenarios with fair value exchanges
   - Consider positional depth of trading partners

4. **Stash Candidates:**
   - Identify players to stash for playoffs or future breakouts
   - Consider handcuffs for key players
   - Look for players returning from injury

5. **Strategic Considerations:**
   - Assess whether the team should be buying for playoffs or selling for next year
   - Consider league standings and remaining schedule strength
   - Identify any urgent moves needed for this week vs. longer-term moves

Provide specific player names and actionable recommendations. Focus on realistic moves that improve the team's championship potential.
"""
        
        return prompt

    def save_analysis_prompt(self, prompt: str, filename: str = None) -> str:
        """Save the generated prompt to a file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"team_analysis_prompt_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        print(f"✅ Analysis prompt saved to {filename}")
        return filename


# Convenience function for easy import
def create_team_analyzer(api: YahooFantasyAPI) -> TeamAnalyzer:
    """Create and return a TeamAnalyzer instance."""
    return TeamAnalyzer(api)