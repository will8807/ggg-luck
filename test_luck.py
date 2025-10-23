"""Test the luck calculator with sample data."""

import sys
sys.path.insert(0, 'src')

from ggg_luck.main import LuckCalculator, WeeklyMatchup, YahooFantasyAPI
from unittest.mock import Mock


def test_luck_calculation():
    """Test luck calculation with sample matchup data."""
    print("🧪 Testing Luck Calculator Logic")
    print("=" * 40)
    
    # Create sample matchups for Week 1
    # Team A (highest score) beats Team B (2nd highest) - lucky matchup for B, unlucky for A  
    # Team C (3rd highest) beats Team D (lowest) - expected result
    sample_matchups = [
        WeeklyMatchup(
            week=1,
            team_id="1",
            team_name="High Scorers",
            team_score=150.0,
            opponent_id="2", 
            opponent_name="Almost There",
            opponent_score=140.0,
            won=True
        ),
        WeeklyMatchup(
            week=1,
            team_id="2",
            team_name="Almost There", 
            team_score=140.0,
            opponent_id="1",
            opponent_name="High Scorers",
            opponent_score=150.0,
            won=False
        ),
        WeeklyMatchup(
            week=1,
            team_id="3",
            team_name="Mid Pack",
            team_score=120.0,
            opponent_id="4",
            opponent_name="Strugglers", 
            opponent_score=90.0,
            won=True
        ),
        WeeklyMatchup(
            week=1,
            team_id="4", 
            team_name="Strugglers",
            team_score=90.0,
            opponent_id="3",
            opponent_name="Mid Pack",
            opponent_score=120.0,
            won=False
        )
    ]
    
    # Mock API client
    mock_api = Mock(spec=YahooFantasyAPI)
    calculator = LuckCalculator(mock_api)
    
    # Calculate luck for Week 1
    luck_scores = calculator.calculate_weekly_luck(sample_matchups, 1)
    
    print("Week 1 Matchups:")
    print("High Scorers (150) def. Almost There (140)")
    print("Mid Pack (120) def. Strugglers (90)")
    print()
    
    print("Luck Scores:")
    for matchup in sample_matchups:
        luck = luck_scores.get(matchup.team_id, 0)
        result = "W" if matchup.won else "L"
        print(f"{matchup.team_name:12} ({matchup.team_score:5.1f}, {result}): {luck:+6.1f}")
    
    print()
    print("Interpretation:")
    print("• 'Almost There' should be UNLUCKY (2nd highest score but lost)")
    print("• 'Strugglers' should be least unlucky (lowest score, expected to lose)")
    print("• 'High Scorers' should be slightly lucky (won but against tough opponent)")
    print("• 'Mid Pack' should be neutral (won against expected opponent)")
    
    # Test expected wins calculation
    print(f"\nExpected Wins Test:")
    for team_id in ["1", "2", "3", "4"]:
        team_matchups = [m for m in sample_matchups if m.team_id == team_id]
        expected = calculator._calculate_expected_wins(team_matchups, sample_matchups)
        actual = sum(1 for m in team_matchups if m.won)
        team_name = team_matchups[0].team_name if team_matchups else "Unknown"
        print(f"{team_name:12}: Expected {expected}, Actual {actual}, Diff {actual-expected:+d}")


if __name__ == "__main__":
    test_luck_calculation()