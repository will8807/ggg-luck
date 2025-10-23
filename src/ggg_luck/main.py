"""Main application for calculating fantasy football team luck."""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from .api import YahooFantasyAPI


@dataclass
class WeeklyMatchup:
    """Represents a single week's matchup between two teams."""
    week: int
    team_id: str
    team_name: str
    team_score: float
    opponent_id: str
    opponent_name: str
    opponent_score: float
    won: bool


@dataclass
class LuckMetrics:
    """Represents luck metrics for a team."""
    team_id: str
    team_name: str
    total_luck_score: float
    avg_luck_per_week: float
    luckiest_week: Optional[WeeklyMatchup]
    unluckiest_week: Optional[WeeklyMatchup]
    weeks_played: int
    should_have_wins: int
    should_have_losses: int
    luck_differential: int  # actual wins - expected wins


class LuckCalculator:
    """Calculates team luck based on weekly scoring matchups."""
    
    def __init__(self, api: YahooFantasyAPI):
        """Initialize the luck calculator with Yahoo API client."""
        self.api = api
    
    def calculate_weekly_luck(self, matchups: List[WeeklyMatchup], week: int) -> Dict[str, float]:
        """
        Calculate luck for all teams in a specific week.
        
        Luck is determined by:
        - How many teams you would have beaten if matched against them instead
        - Your actual opponent's rank compared to average opponent strength
        """
        # Get all scores for the week
        week_matchups = [m for m in matchups if m.week == week]
        all_scores = [(m.team_score, m.team_id, m.team_name) for m in week_matchups]
        all_scores.sort(reverse=True)  # Highest to lowest
        
        luck_scores = {}
        
        for matchup in week_matchups:
            team_score = matchup.team_score
            opponent_score = matchup.opponent_score
            
            # Calculate how many teams this team would have beaten
            teams_would_beat = sum(1 for score, _, _ in all_scores if score < team_score)
            total_possible_opponents = len(all_scores) - 1  # Exclude self
            
            # Calculate opponent's percentile (0 = weakest opponent, 1 = strongest)
            opponent_percentile = sum(1 for score, _, _ in all_scores if score < opponent_score) / total_possible_opponents
            
            # Expected win percentage based on score ranking
            expected_win_pct = teams_would_beat / total_possible_opponents if total_possible_opponents > 0 else 0.5
            
            # Actual result (1 for win, 0 for loss)
            actual_result = 1 if matchup.won else 0
            
            # Luck score: positive = lucky, negative = unlucky
            # Scale by 100 for easier interpretation
            base_luck = (actual_result - expected_win_pct) * 100
            
            # Bonus/penalty for opponent strength
            # Playing weaker opponent when you should win = less impressive
            # Playing stronger opponent when you should lose = more impressive
            opponent_strength_factor = (opponent_percentile - 0.5) * 20
            
            if actual_result == 1:  # Won
                # Beating strong opponent = skill bonus, beating weak opponent = luck penalty
                luck_score = base_luck - opponent_strength_factor
            else:  # Lost
                # Losing to weak opponent = unlucky penalty, losing to strong opponent = less unlucky
                luck_score = base_luck - opponent_strength_factor
            
            luck_scores[matchup.team_id] = luck_score
            
        return luck_scores
    
    def analyze_team_luck(self, league_key: str, current_week: int = 8) -> List[LuckMetrics]:
        """
        Analyze luck for all teams in a league.
        
        Args:
            league_key: Yahoo league key
            current_week: Current week to analyze through
        """
        print(f"🔍 Analyzing team luck for league {league_key}...")
        
        # Get all matchups for the season
        all_matchups = []
        
        for week in range(1, current_week + 1):
            print(f"📊 Fetching week {week} matchups...")
            try:
                matchups_data = self.api.make_api_request(f"league/{league_key}/scoreboard;week={week}")
                week_matchups = self._parse_matchups(matchups_data, week)
                all_matchups.extend(week_matchups)
            except Exception as e:
                print(f"⚠️  Could not fetch week {week}: {e}")
                continue
        
        if not all_matchups:
            print("❌ No matchup data found")
            return []
        
        # Calculate luck for each week
        team_luck_totals = {}
        team_matchups = {}
        
        for week in range(1, current_week + 1):
            week_luck = self.calculate_weekly_luck(all_matchups, week)
            
            for team_id, luck_score in week_luck.items():
                if team_id not in team_luck_totals:
                    team_luck_totals[team_id] = []
                    team_matchups[team_id] = []
                
                team_luck_totals[team_id].append(luck_score)
                
                # Store the matchup for this team/week
                team_week_matchup = next((m for m in all_matchups 
                                        if m.team_id == team_id and m.week == week), None)
                if team_week_matchup:
                    team_matchups[team_id].append(team_week_matchup)
        
        # Create LuckMetrics for each team
        luck_metrics = []
        
        for team_id, luck_scores in team_luck_totals.items():
            if not luck_scores:
                continue
                
            matchups = team_matchups.get(team_id, [])
            total_luck = sum(luck_scores)
            avg_luck = total_luck / len(luck_scores)
            
            # Find luckiest and unluckiest weeks
            luckiest_week = None
            unluckiest_week = None
            
            if matchups:
                team_name = matchups[0].team_name
                
                # Find extreme weeks
                max_luck_idx = luck_scores.index(max(luck_scores))
                min_luck_idx = luck_scores.index(min(luck_scores))
                
                if max_luck_idx < len(matchups):
                    luckiest_week = matchups[max_luck_idx]
                if min_luck_idx < len(matchups):
                    unluckiest_week = matchups[min_luck_idx]
                
                # Calculate should-have record
                actual_wins = sum(1 for m in matchups if m.won)
                should_have_wins = self._calculate_expected_wins(matchups, all_matchups)
                should_have_losses = len(matchups) - should_have_wins
                luck_differential = actual_wins - should_have_wins
                
                metrics = LuckMetrics(
                    team_id=team_id,
                    team_name=team_name,
                    total_luck_score=total_luck,
                    avg_luck_per_week=avg_luck,
                    luckiest_week=luckiest_week,
                    unluckiest_week=unluckiest_week,
                    weeks_played=len(matchups),
                    should_have_wins=should_have_wins,
                    should_have_losses=should_have_losses,
                    luck_differential=luck_differential
                )
                luck_metrics.append(metrics)
        
        # Sort by total luck score (most unlucky first)
        luck_metrics.sort(key=lambda x: x.total_luck_score)
        
        return luck_metrics
    
    def _parse_matchups(self, matchups_data: Dict, week: int) -> List[WeeklyMatchup]:
        """Parse Yahoo API matchup data into WeeklyMatchup objects."""
        matchups = []
        
        try:
            # Navigate the XML structure
            if 'fantasy_content' not in matchups_data:
                return matchups
                
            league_data = matchups_data['fantasy_content']['league']
            if isinstance(league_data, list):
                league_data = league_data[1]['league']
                
            if 'scoreboard' not in league_data:
                return matchups
                
            scoreboard = league_data['scoreboard']
            if 'matchups' not in scoreboard:
                return matchups
                
            matchup_data = scoreboard['matchups']
            if 'matchup' not in matchup_data:
                return matchups
                
            matchup_list = matchup_data['matchup']
            if not isinstance(matchup_list, list):
                matchup_list = [matchup_list]
            
            for matchup in matchup_list:
                if 'teams' not in matchup:
                    continue
                    
                teams = matchup['teams']['team']
                if not isinstance(teams, list) or len(teams) != 2:
                    continue
                
                # Extract team data
                team1_data = teams[0]
                team2_data = teams[1]
                
                # Parse team 1
                team1_info = team1_data[0][2]['team']  # Team info is nested
                team1_stats = team1_data[1]['team']   # Team stats
                
                team2_info = team2_data[0][2]['team']
                team2_stats = team2_data[1]['team']
                
                # Get scores and determine winner
                team1_score = float(team1_stats.get('team_points', {}).get('total', 0))
                team2_score = float(team2_stats.get('team_points', {}).get('total', 0))
                
                team1_won = team1_score > team2_score
                team2_won = team2_score > team1_score
                
                # Create matchup objects for both teams
                matchup1 = WeeklyMatchup(
                    week=week,
                    team_id=team1_info['team_id'],
                    team_name=team1_info['name'],
                    team_score=team1_score,
                    opponent_id=team2_info['team_id'],
                    opponent_name=team2_info['name'],
                    opponent_score=team2_score,
                    won=team1_won
                )
                
                matchup2 = WeeklyMatchup(
                    week=week,
                    team_id=team2_info['team_id'],
                    team_name=team2_info['name'],
                    team_score=team2_score,
                    opponent_id=team1_info['team_id'],
                    opponent_name=team1_info['name'],
                    opponent_score=team1_score,
                    won=team2_won
                )
                
                matchups.extend([matchup1, matchup2])
                
        except (KeyError, IndexError, TypeError, ValueError) as e:
            print(f"⚠️  Error parsing matchup data for week {week}: {e}")
            
        return matchups
    
    def _calculate_expected_wins(self, team_matchups: List[WeeklyMatchup], all_matchups: List[WeeklyMatchup]) -> int:
        """Calculate how many wins a team should have had based on their scores."""
        expected_wins = 0
        
        for matchup in team_matchups:
            # Count how many teams they would have beaten this week
            week_scores = [(m.team_score, m.team_id) for m in all_matchups 
                          if m.week == matchup.week and m.team_id != matchup.team_id]
            
            teams_would_beat = sum(1 for score, _ in week_scores if score < matchup.team_score)
            total_opponents = len(week_scores)
            
            if total_opponents > 0:
                win_probability = teams_would_beat / total_opponents
                expected_wins += win_probability
        
        return round(expected_wins)
    
    def display_luck_analysis(self, luck_metrics: List[LuckMetrics]):
        """Display formatted luck analysis results."""
        if not luck_metrics:
            print("❌ No luck data to display")
            return
        
        print(f"\n🍀 FANTASY FOOTBALL LUCK ANALYSIS")
        print("=" * 60)
        print(f"{'Rank':<4} {'Team':<20} {'Luck':<8} {'W-L':<6} {'Should Be':<9} {'Diff':<6}")
        print("-" * 60)
        
        for i, metrics in enumerate(luck_metrics, 1):
            actual_wins = sum(1 for m in [metrics.luckiest_week, metrics.unluckiest_week] if m and m.won)
            actual_record = f"{metrics.should_have_wins + metrics.luck_differential}-{metrics.weeks_played - metrics.should_have_wins - metrics.luck_differential}"
            should_record = f"{metrics.should_have_wins}-{metrics.should_have_losses}"
            
            luck_indicator = "🍀" if metrics.total_luck_score > 20 else "💀" if metrics.total_luck_score < -20 else "😐"
            
            print(f"{i:<4} {metrics.team_name[:19]:<20} {metrics.avg_luck_per_week:>+6.1f}{luck_indicator} "
                  f"{actual_record:<6} {should_record:<9} {metrics.luck_differential:>+4}")
        
        # Show most extreme weeks
        print(f"\n🎰 MOST EXTREME WEEKS:")
        print("-" * 40)
        
        all_weeks = []
        for metrics in luck_metrics:
            if metrics.luckiest_week:
                all_weeks.append(("LUCKY", metrics.luckiest_week, metrics.avg_luck_per_week))
            if metrics.unluckiest_week:
                all_weeks.append(("UNLUCKY", metrics.unluckiest_week, metrics.avg_luck_per_week))
        
        # Sort by extremeness
        all_weeks.sort(key=lambda x: abs(x[2]), reverse=True)
        
        for i, (luck_type, matchup, luck_score) in enumerate(all_weeks[:5]):
            result = "W" if matchup.won else "L"
            print(f"{luck_type:>7}: {matchup.team_name} Week {matchup.week} "
                  f"({matchup.team_score:.1f} vs {matchup.opponent_score:.1f}, {result}) "
                  f"Luck: {luck_score:+.1f}")


def main():
    """Main function to run luck analysis."""
    try:
        # Initialize Yahoo API
        api = YahooFantasyAPI()
        
        print("🏈 GGG Luck - Fantasy Football Luck Calculator")
        print("=" * 50)
        
        # Check if we have access token, try to load from environment
        if not api.access_token:
            import os
            api.access_token = os.getenv('YAHOO_ACCESS_TOKEN')
            api.refresh_token = os.getenv('YAHOO_REFRESH_TOKEN')
            
            if not api.access_token:
                print("❌ No access token found. Please run 'uv run ggg-luck-example' first to authenticate.")
                return
        
        # Get user's leagues
        print("🔍 Fetching your fantasy leagues...")
        leagues = api.get_user_leagues("nfl")
        
        # Extract league key (assuming first league for now)
        league_key = None
        if 'fantasy_content' in leagues:
            fantasy_content = leagues['fantasy_content']
            if 'users' in fantasy_content:
                users = fantasy_content['users']
                if 'user' in users:
                    user_data = users['user']
                    if 'games' in user_data and 'game' in user_data['games']:
                        game_data = user_data['games']['game']
                        if 'leagues' in game_data and 'league' in game_data['leagues']:
                            league = game_data['leagues']['league']
                            league_key = league.get('league_key')
        
        if not league_key:
            print("❌ Could not find league key")
            return
            
        print(f"🏆 Analyzing league: {league_key}")
        
        # Run luck analysis
        calculator = LuckCalculator(api)
        luck_metrics = calculator.analyze_team_luck(league_key)
        
        # Display results
        calculator.display_luck_analysis(luck_metrics)
        
        print(f"\n💡 Luck Score Explanation:")
        print("  • Positive scores = Lucky (winning more than expected)")
        print("  • Negative scores = Unlucky (losing more than expected)")  
        print("  • Based on weekly scoring vs. opponent strength")
        
    except Exception as e:
        print(f"❌ Error running luck analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()