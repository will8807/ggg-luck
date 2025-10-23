"""Main application for calculating fantasy football team luck."""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime
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
    
    def analyze_team_luck(self, league_key: str, current_week: int = 17) -> List[LuckMetrics]:
        """
        Analyze luck for all teams in a league.
        
        Args:
            league_key: Yahoo league key
            current_week: Maximum week to check (will stop at first incomplete week)
        """
        print(f"🔍 Analyzing team luck for league {league_key}...")
        
        # Determine which weeks are complete
        completed_weeks = []
        for week in range(1, current_week + 1):
            print(f"📊 Checking week {week} completion...")
            try:
                matchups_data = self.api.make_api_request(f"league/{league_key}/scoreboard;week={week}")
                week_matchups = self._parse_matchups(matchups_data, week)
                if week_matchups:  # If we got matchups, week is complete
                    completed_weeks.append(week)
                    print(f"✅ Week {week} is complete")
                else:
                    print(f"⏳ Week {week} is not complete yet - stopping here")
                    break
            except Exception as e:
                print(f"⏳ Week {week} is not available yet - stopping here")
                break
        
        if not completed_weeks:
            print("❌ No completed weeks found")
            return []
            
        print(f"📊 Analyzing {len(completed_weeks)} completed weeks: {completed_weeks}")
        
        # Get all matchups for completed weeks
        all_matchups = []
        
        for week in completed_weeks:
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
        
        # Calculate luck for each completed week
        team_luck_totals = {}
        team_matchups = {}
        
        for week in completed_weeks:
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
            
            for i, matchup in enumerate(matchup_list):
                if 'teams' not in matchup:
                    continue
                    
                # Check if matchup is complete - 'postevent' means finished, 'midevent' means in progress
                matchup_status = matchup.get('status', 'unknown')
                
                # Skip incomplete weeks (midevent, preevent, etc.)
                if matchup_status != 'postevent':
                    print(f"⏳ Week {week} is not complete yet (status: {matchup_status}) - skipping")
                    return matchups  # Return early, don't process this week
                
                # Also check for winner_team_key presence as additional confirmation
                if 'winner_team_key' not in matchup:
                    print(f"⚠️ Week {week} appears incomplete (no winner) - skipping")
                    return matchups
                    
                teams_data = matchup['teams']
                
                teams = teams_data.get('team', [])
                if not isinstance(teams, list):
                    teams = [teams]  # Single team structure
                    
                if len(teams) != 2:
                    print(f"⚠️  Expected 2 teams, got {len(teams)}")
                    continue
                
                
                # Extract team data - Yahoo API provides teams directly as dicts
                team1_data = teams[0]
                team2_data = teams[1]
                
                # Parse team data - teams are already in the correct format
                try:
                    # Teams are direct dictionaries with all the info we need
                    team1_info = team1_data
                    team1_stats = team1_data
                    team2_info = team2_data
                    team2_stats = team2_data
                    
                    # Get scores - try different possible locations
                    team1_score = 0
                    team2_score = 0
                    
                    # Try team_points structure
                    if 'team_points' in team1_stats:
                        team1_score = float(team1_stats['team_points'].get('total', 0))
                    elif 'points' in team1_stats:
                        team1_score = float(team1_stats['points'].get('total', 0))
                    elif 'team_projected_points' in team1_stats:
                        team1_score = float(team1_stats['team_projected_points'].get('total', 0))
                    
                    if 'team_points' in team2_stats:
                        team2_score = float(team2_stats['team_points'].get('total', 0))
                    elif 'points' in team2_stats:
                        team2_score = float(team2_stats['points'].get('total', 0))
                    elif 'team_projected_points' in team2_stats:
                        team2_score = float(team2_stats['team_projected_points'].get('total', 0))
                        
                except (KeyError, IndexError, TypeError) as e:
                    print(f"⚠️  Could not parse team data for matchup: {e}")
                    print(f"🔍  Team1 structure: {team1_data}")
                    print(f"🔍  Team2 structure: {team2_data}")
                    continue
                
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

    def generate_markdown_report(self, luck_metrics: List[LuckMetrics], league_name: str = "Fantasy League") -> str:
        """Generate a comprehensive markdown report with charts."""
        
        # Create charts directory if it doesn't exist
        charts_dir = "charts"
        if not os.path.exists(charts_dir):
            os.makedirs(charts_dir)
            
        # Generate charts
        self._create_luck_ranking_chart(luck_metrics, charts_dir)
        self._create_luck_distribution_chart(luck_metrics, charts_dir)
        self._create_wins_comparison_chart(luck_metrics, charts_dir)
        
        # Generate markdown content
        current_date = datetime.now().strftime("%B %d, %Y")
        completed_weeks = max(m.weeks_played for m in luck_metrics) if luck_metrics else 0
        
        markdown = f"""# 🏈 Fantasy Football Luck Analysis Report

**League:** {league_name}  
**Analysis Date:** {current_date}  
**Weeks Analyzed:** {completed_weeks} completed weeks

---

## 📊 Executive Summary

This report analyzes team "luck" by comparing actual wins vs. expected wins based on weekly scoring performance. Teams that consistently win against weaker opponents while losing to stronger ones are considered "unlucky," while teams that beat stronger opponents or lose to weaker ones are "lucky."

## 🏆 Luck Rankings

![Luck Rankings](charts/luck_rankings.png)

| Rank | Team | Luck Score | Record | Should Be | Diff |
|------|------|------------|--------|-----------|------|
"""
        
        # Add team rankings
        for i, metrics in enumerate(luck_metrics, 1):
            actual_wins = metrics.should_have_wins + metrics.luck_differential
            actual_losses = metrics.weeks_played - actual_wins
            actual_record = f"{actual_wins}-{actual_losses}"
            should_record = f"{metrics.should_have_wins}-{metrics.should_have_losses}"
            
            luck_emoji = "💀" if metrics.total_luck_score < -5 else "😐" if abs(metrics.total_luck_score) <= 5 else "🍀"
            
            markdown += f"| {i} | {metrics.team_name} {luck_emoji} | {metrics.total_luck_score:+.1f} | {actual_record} | {should_record} | {metrics.luck_differential:+d} |\n"
        
        markdown += f"""

## 📈 Luck Distribution

![Luck Distribution](charts/luck_distribution.png)

The chart above shows the distribution of luck scores across all teams. Positive values indicate lucky teams, while negative values show unlucky teams.

## ⚖️ Wins: Actual vs Expected

![Wins Comparison](charts/wins_comparison.png)

This chart compares each team's actual wins against what they "should have" won based on their scoring performance.

## 🎰 Most Extreme Weeks

"""
        
        # Add extreme weeks
        all_weeks = []
        for metrics in luck_metrics:
            if metrics.luckiest_week:
                all_weeks.append(("Luckiest", metrics.luckiest_week, metrics.total_luck_score))
            if metrics.unluckiest_week:
                all_weeks.append(("Unluckiest", metrics.unluckiest_week, metrics.total_luck_score))
        
        all_weeks.sort(key=lambda x: abs(x[2]), reverse=True)
        
        for luck_type, matchup, luck_score in all_weeks[:5]:
            result = "**WIN**" if matchup.won else "**LOSS**"
            markdown += f"- **{luck_type}:** {matchup.team_name} Week {matchup.week} - {matchup.team_score:.1f} vs {matchup.opponent_score:.1f} ({result})\n"
        
        markdown += f"""

## 📊 Methodology

**Luck Score Calculation:**
- Each week, we calculate how many teams you would have beaten with your score
- Compare your actual opponent's strength to the average opponent
- Positive luck = beating stronger opponents or losing to weaker ones
- Negative luck = losing to stronger opponents or beating weaker ones

**Expected Wins:**
- Based on your weekly scoring performance vs. all possible opponents
- Shows what your record "should be" in a perfectly fair scheduling system

---

*Generated by GGG Luck Fantasy Football Analyzer*  
*Analysis Date: {current_date}*
"""
        
        return markdown

    def _create_luck_ranking_chart(self, luck_metrics: List[LuckMetrics], charts_dir: str):
        """Create a horizontal bar chart of luck rankings."""
        plt.figure(figsize=(12, 8))
        
        teams = [m.team_name for m in luck_metrics]
        scores = [m.total_luck_score for m in luck_metrics]
        
        # Color bars based on luck (red for unlucky, green for lucky)
        colors = ['#e74c3c' if score < -5 else '#f39c12' if abs(score) <= 5 else '#27ae60' for score in scores]
        
        bars = plt.barh(teams, scores, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        
        # Add value labels on bars
        for i, (bar, score) in enumerate(zip(bars, scores)):
            plt.text(score + (1 if score >= 0 else -1), i, f'{score:+.1f}', 
                    ha='left' if score >= 0 else 'right', va='center', fontweight='bold')
        
        plt.axvline(x=0, color='black', linestyle='-', alpha=0.3)
        plt.xlabel('Luck Score', fontsize=12, fontweight='bold')
        plt.title('Fantasy Football Team Luck Rankings\n(Lower scores = More unlucky)', fontsize=14, fontweight='bold', pad=20)
        plt.grid(axis='x', alpha=0.3)
        
        # Reverse y-axis so most unlucky (lowest score) appears at top
        plt.gca().invert_yaxis()
        
        plt.tight_layout()
        plt.savefig(f'{charts_dir}/luck_rankings.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_luck_distribution_chart(self, luck_metrics: List[LuckMetrics], charts_dir: str):
        """Create a distribution plot of luck scores."""
        plt.figure(figsize=(10, 6))
        
        scores = [m.total_luck_score for m in luck_metrics]
        
        # Create histogram
        plt.hist(scores, bins=8, alpha=0.7, color='skyblue', edgecolor='black', linewidth=1)
        
        # Add vertical line at zero
        plt.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Neutral Luck')
        
        plt.xlabel('Luck Score', fontsize=12, fontweight='bold')
        plt.ylabel('Number of Teams', fontsize=12, fontweight='bold')
        plt.title('Distribution of Team Luck Scores', fontsize=14, fontweight='bold', pad=20)
        plt.grid(axis='y', alpha=0.3)
        plt.legend()
        
        # Add annotations
        unlucky_count = len([s for s in scores if s < -5])
        lucky_count = len([s for s in scores if s > 5])
        neutral_count = len(scores) - unlucky_count - lucky_count
        
        plt.text(0.02, 0.98, f'Unlucky Teams: {unlucky_count}\nNeutral Teams: {neutral_count}\nLucky Teams: {lucky_count}', 
                transform=plt.gca().transAxes, verticalalignment='top', 
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(f'{charts_dir}/luck_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_wins_comparison_chart(self, luck_metrics: List[LuckMetrics], charts_dir: str):
        """Create a comparison chart of actual vs expected wins."""
        plt.figure(figsize=(12, 8))
        
        teams = [m.team_name for m in luck_metrics]
        actual_wins = []
        expected_wins = [m.should_have_wins for m in luck_metrics]
        
        # Calculate actual wins from should_have_wins + luck_differential
        for m in luck_metrics:
            actual_wins.append(m.should_have_wins + m.luck_differential)
        
        x = range(len(teams))
        width = 0.35
        
        bars1 = plt.bar([i - width/2 for i in x], actual_wins, width, label='Actual Wins', 
                       color='#3498db', alpha=0.8, edgecolor='black', linewidth=0.5)
        bars2 = plt.bar([i + width/2 for i in x], expected_wins, width, label='Expected Wins', 
                       color='#e67e22', alpha=0.8, edgecolor='black', linewidth=0.5)
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,f'{int(height)}',
                        ha='center', va='bottom', fontweight='bold')
        
        plt.xlabel('Teams', fontsize=12, fontweight='bold')
        plt.ylabel('Wins', fontsize=12, fontweight='bold')
        plt.title('Actual vs Expected Wins by Team', fontsize=14, fontweight='bold', pad=20)
        plt.xticks(x, teams, rotation=45, ha='right')
        plt.legend()
        plt.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{charts_dir}/wins_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()

    def save_markdown_report(self, luck_metrics: List[LuckMetrics], filename: str = "luck_analysis_report.md", league_name: str = "Fantasy League"):
        """Generate and save markdown report to file."""
        markdown_content = self.generate_markdown_report(luck_metrics, league_name)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
            
        print(f"📄 Markdown report saved to: {filename}")
        print(f"📊 Charts saved to: charts/ directory")


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
        
        # Generate markdown report
        print(f"\n📊 Generating markdown report...")
        calculator.save_markdown_report(luck_metrics, "luck_analysis_report.md", "Gang of Gridiron Gurus")
        
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