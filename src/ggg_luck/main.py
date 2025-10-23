"""Main application for calculating fantasy football team luck."""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime
import numpy as np
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
class ScoringTrends:
    """Represents scoring trends and momentum for a team."""
    team_id: str
    team_name: str
    weekly_scores: List[float]
    avg_score: float
    score_std: float  # Standard deviation (consistency)
    trend_slope: float  # Linear regression slope (momentum)
    recent_avg: float  # Last 3 weeks average
    peak_week: int  # Week with highest score
    valley_week: int  # Week with lowest score
    hot_streak: int  # Current consecutive weeks above average
    cold_streak: int  # Current consecutive weeks below average
    volatility_index: float  # Measure of scoring volatility (0-100)


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
    scoring_trends: Optional['ScoringTrends'] = None  # Add scoring trends analysis


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
                
                # Calculate scoring trends
                scoring_trends = self._calculate_scoring_trends(matchups)
                
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
                    luck_differential=luck_differential,
                    scoring_trends=scoring_trends
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
    
    def _calculate_scoring_trends(self, matchups: List[WeeklyMatchup]) -> ScoringTrends:
        """Calculate scoring trends and momentum for a team."""
        if not matchups:
            return None
            
        # Sort matchups by week to ensure proper ordering
        matchups = sorted(matchups, key=lambda m: m.week)
        
        team_id = matchups[0].team_id
        team_name = matchups[0].team_name
        weekly_scores = [m.team_score for m in matchups]
        
        # Basic statistics
        avg_score = np.mean(weekly_scores)
        score_std = np.std(weekly_scores)
        
        # Calculate trend (linear regression slope)
        weeks = np.arange(1, len(weekly_scores) + 1)
        trend_slope = np.polyfit(weeks, weekly_scores, 1)[0] if len(weekly_scores) > 1 else 0
        
        # Recent form (last 3 weeks average)
        recent_avg = np.mean(weekly_scores[-3:]) if len(weekly_scores) >= 3 else avg_score
        
        # Peak and valley weeks
        peak_week = matchups[np.argmax(weekly_scores)].week
        valley_week = matchups[np.argmin(weekly_scores)].week
        
        # Calculate hot/cold streaks
        hot_streak, cold_streak = self._calculate_streaks(weekly_scores, avg_score)
        
        # Volatility index (coefficient of variation * 100)
        volatility_index = (score_std / avg_score * 100) if avg_score > 0 else 0
        
        return ScoringTrends(
            team_id=team_id,
            team_name=team_name,
            weekly_scores=weekly_scores,
            avg_score=avg_score,
            score_std=score_std,
            trend_slope=trend_slope,
            recent_avg=recent_avg,
            peak_week=peak_week,
            valley_week=valley_week,
            hot_streak=hot_streak,
            cold_streak=cold_streak,
            volatility_index=volatility_index
        )
    
    def _calculate_streaks(self, weekly_scores: List[float], avg_score: float) -> Tuple[int, int]:
        """Calculate current hot and cold streaks."""
        if not weekly_scores:
            return 0, 0
            
        # Start from the most recent week and work backwards
        hot_streak = 0
        cold_streak = 0
        
        # Check current streak from the end
        for i in range(len(weekly_scores) - 1, -1, -1):
            score = weekly_scores[i]
            if score > avg_score:
                if cold_streak == 0:  # Still in hot streak
                    hot_streak += 1
                else:  # Hit a cold week, stop counting
                    break
            else:
                if hot_streak == 0:  # Still in cold streak
                    cold_streak += 1
                else:  # Hit a hot week, stop counting
                    break
                    
        return hot_streak, cold_streak
    
    def _get_trend_indicator(self, trends: Optional[ScoringTrends]) -> str:
        """Generate a trend indicator string for display."""
        if not trends:
            return ""
            
        # Momentum indicator
        if trends.trend_slope > 2:
            momentum = "📈📈"  # Strong upward
        elif trends.trend_slope > 0.5:
            momentum = "📈"     # Upward
        elif trends.trend_slope < -2:
            momentum = "📉📉"  # Strong downward 
        elif trends.trend_slope < -0.5:
            momentum = "📉"     # Downward
        else:
            momentum = "➡️"      # Flat
            
        # Streak indicator
        if trends.hot_streak > 0:
            streak = f"🔥{trends.hot_streak}"
        elif trends.cold_streak > 0:
            streak = f"🧊{trends.cold_streak}"
        else:
            streak = ""
            
        return f"{momentum}{streak}"
    
    def display_luck_analysis(self, luck_metrics: List[LuckMetrics]):
        """Display formatted luck analysis results."""
        if not luck_metrics:
            print("❌ No luck data to display")
            return
        
        print(f"\n🍀 FANTASY FOOTBALL LUCK ANALYSIS")
        print("=" * 80)
        print(f"{'Rank':<4} {'Team':<20} {'Luck':<8} {'W-L':<6} {'Should Be':<9} {'Diff':<6} {'Trend':<10}")
        print("-" * 80)
        
        for i, metrics in enumerate(luck_metrics, 1):
            actual_wins = sum(1 for m in [metrics.luckiest_week, metrics.unluckiest_week] if m and m.won)
            actual_record = f"{metrics.should_have_wins + metrics.luck_differential}-{metrics.weeks_played - metrics.should_have_wins - metrics.luck_differential}"
            should_record = f"{metrics.should_have_wins}-{metrics.should_have_losses}"
            
            luck_indicator = "🍀" if metrics.total_luck_score > 20 else "💀" if metrics.total_luck_score < -20 else "😐"
            
            # Generate trend indicator
            trend_indicator = self._get_trend_indicator(metrics.scoring_trends)
            
            print(f"{i:<4} {metrics.team_name[:19]:<20} {metrics.avg_luck_per_week:>+6.1f}{luck_indicator} "
                  f"{actual_record:<6} {should_record:<9} {metrics.luck_differential:>+4} {trend_indicator:<10}")
        
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
        
        # Show scoring trends
        print(f"\n📈 SCORING TRENDS & MOMENTUM:")
        print("-" * 50)
        
        # Sort by recent form for trends display
        trends_sorted = sorted([m for m in luck_metrics if m.scoring_trends], 
                             key=lambda x: x.scoring_trends.recent_avg, reverse=True)
        
        for metrics in trends_sorted[:10]:  # Top 10
            trends = metrics.scoring_trends
            momentum = "📈" if trends.trend_slope > 1 else "📉" if trends.trend_slope < -1 else "➡️"
            streak_info = ""
            
            if trends.hot_streak > 0:
                streak_info = f"🔥{trends.hot_streak}W"
            elif trends.cold_streak > 0:
                streak_info = f"🧊{trends.cold_streak}W"
            else:
                streak_info = "😐"
                
            print(f"{metrics.team_name[:20]:<20} Avg: {trends.avg_score:>6.1f} Recent: {trends.recent_avg:>6.1f} "
                  f"{momentum} {streak_info} Vol: {trends.volatility_index:>4.0f}%")

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
        self._create_scoring_trends_chart(luck_metrics, charts_dir)
        
        # Generate markdown content
        current_date = datetime.now().strftime("%B %d, %Y")
        completed_weeks = max(m.weeks_played for m in luck_metrics) if luck_metrics else 0
        
        markdown = f"""# 🏈 {league_name} - Fantasy Football Analysis Report

> **Analysis Date:** {current_date} | **Weeks Analyzed:** {completed_weeks} completed weeks

---

## � Table of Contents
- [Executive Summary](#-executive-summary)
- [Luck Rankings](#-luck-rankings) 
- [Weekly Scoring Trends](#-weekly-scoring-trends)
- [Performance Analysis](#-performance-analysis)
- [Methodology](#-methodology)

---

## 📊 Executive Summary

This comprehensive analysis examines team performance across **{completed_weeks} weeks** of fantasy football action. We analyze both **luck factors** (schedule strength and opponent matchups) and **scoring trends** (momentum and consistency) to provide actionable insights for your league.

### Key Findings:
- **Most Lucky Team:** Teams with positive luck scores are winning more than their scoring suggests
- **Most Unlucky Team:** Teams with negative luck scores are underperforming their scoring ability
- **Hottest Team:** Teams with strong upward scoring trends are building momentum
- **Most Consistent:** Teams with low volatility provide reliable weekly production

---

## 🏆 Luck Rankings

*Teams ranked by luck score - negative scores indicate unlucky teams who should have better records*

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

---

## 📊 Performance Analysis

### ⚖️ Wins: Actual vs Expected

*Comparing real records against "should have" records based on scoring performance*

![Wins Comparison](charts/wins_comparison.png)

This analysis reveals which teams have been **schedule beneficiaries** versus **schedule victims**. The orange bars show what each team's record should be based purely on their scoring output, while blue bars show their actual record.

### 🎲 Luck Distribution

![Luck Distribution](charts/luck_distribution.png)

*Distribution of luck scores across the league - most teams cluster around neutral (0)*

---

## 📈 Weekly Scoring Trends

*Track team momentum, consistency, and recent form to predict future performance*

![Scoring Trends](charts/scoring_trends.png)

This visualization reveals crucial **momentum patterns** and **scoring consistency** across all teams. The solid lines show actual weekly scores, while dashed trend lines indicate each team's trajectory. Teams with strong upward trends are building momentum for playoff pushes.

### 🔥 Momentum Analysis

*Teams sorted by recent form (last 3 weeks average)*

| Team | Avg Score | Recent Form | Trend | Volatility |
|------|-----------|-------------|-------|------------|
"""
        
        # Add momentum analysis table
        trends_sorted = sorted([m for m in luck_metrics if m.scoring_trends], 
                             key=lambda x: x.scoring_trends.recent_avg, reverse=True)
        
        for metrics in trends_sorted:
            trends = metrics.scoring_trends
            trend_arrow = "⬆️" if trends.trend_slope > 1 else "⬇️" if trends.trend_slope < -1 else "➡️"
            
            markdown += f"| {metrics.team_name} | {trends.avg_score:.1f} | {trends.recent_avg:.1f} | {trend_arrow} {trends.trend_slope:+.1f}/wk | {trends.volatility_index:.0f}% |\n"
        
        markdown += f"""

### 🎰 Most Extreme Weeks

*The biggest lucky breaks and unlucky losses of the season*

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

---

## � Methodology

### Luck Score Calculation
- **Weekly Analysis**: For each week, calculate how many teams you would have beaten with your score
- **Opponent Strength**: Compare your actual opponent's strength to average opponent difficulty
- **Luck Factors**: 
  - ✅ **Positive Luck**: Beating stronger opponents or losing to weaker ones
  - ❌ **Negative Luck**: Losing to stronger opponents or beating weaker ones

### Scoring Trends Analysis
- **Momentum**: Linear regression slope showing points gained/lost per week
- **Recent Form**: Average scoring over last 3 weeks
- **Volatility**: Standard deviation of scoring (consistency measure)
- **Streaks**: Consecutive weeks above/below personal average

### Expected Wins Model
- **Fair Scheduling**: Calculate record based on scoring vs. all possible opponents each week
- **Schedule Strength**: Account for actual opponents faced vs. league average
- **Performance Prediction**: Use trends to project future performance

---

<div align="center">

**📈 Generated by GGG Luck Fantasy Football Analyzer**

*Analysis Date: {current_date}*

*Unlock the patterns behind your fantasy success*

</div>
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

    def _create_scoring_trends_chart(self, luck_metrics: List[LuckMetrics], charts_dir: str):
        """Create a line chart showing weekly scoring trends for all teams."""
        plt.figure(figsize=(14, 8))
        
        # Filter teams with scoring trends
        teams_with_trends = [m for m in luck_metrics if m.scoring_trends]
        
        if not teams_with_trends:
            return
            
        # Create color palette
        colors = plt.cm.Set3(np.linspace(0, 1, len(teams_with_trends)))
        
        for i, metrics in enumerate(teams_with_trends):
            trends = metrics.scoring_trends
            weeks = range(1, len(trends.weekly_scores) + 1)
            
            # Plot the scoring line
            plt.plot(weeks, trends.weekly_scores, 
                    color=colors[i], marker='o', linewidth=2, markersize=4, 
                    label=f"{metrics.team_name[:12]} ({trends.avg_score:.1f})", alpha=0.8)
            
            # Add trend line
            if len(trends.weekly_scores) > 1:
                z = np.polyfit(weeks, trends.weekly_scores, 1)
                trend_line = np.poly1d(z)
                plt.plot(weeks, trend_line(weeks), 
                        color=colors[i], linestyle='--', alpha=0.5, linewidth=1)
        
        # Add league average line
        all_scores = []
        max_weeks = max(len(m.scoring_trends.weekly_scores) for m in teams_with_trends)
        
        for week in range(1, max_weeks + 1):
            week_scores = [m.scoring_trends.weekly_scores[week-1] 
                          for m in teams_with_trends 
                          if len(m.scoring_trends.weekly_scores) >= week]
            if week_scores:
                all_scores.append(np.mean(week_scores))
        
        if all_scores:
            plt.plot(range(1, len(all_scores) + 1), all_scores, 
                    color='black', linewidth=3, linestyle='-', 
                    label='League Average', alpha=0.7)
        
        plt.xlabel('Week', fontsize=12, fontweight='bold')
        plt.ylabel('Points Scored', fontsize=12, fontweight='bold')
        plt.title('Weekly Scoring Trends by Team\\n(Dashed lines show trend direction)', fontsize=14, fontweight='bold', pad=20)
        plt.grid(True, alpha=0.3)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        
        # Set reasonable axis limits
        if teams_with_trends:
            all_weekly_scores = [score for m in teams_with_trends for score in m.scoring_trends.weekly_scores]
            min_score = min(all_weekly_scores) * 0.9
            max_score = max(all_weekly_scores) * 1.1
            plt.ylim(min_score, max_score)
        
        plt.tight_layout()
        plt.savefig(f'{charts_dir}/scoring_trends.png', dpi=300, bbox_inches='tight')
        plt.close()

    def save_markdown_report(self, luck_metrics: List[LuckMetrics], filename: str = "analysis_report.md", league_name: str = "Fantasy League"):
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
        calculator.save_markdown_report(luck_metrics, "analysis_report.md", "Gang of Gridiron Gurus")
        
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