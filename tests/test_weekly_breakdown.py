"""Tests for weekly breakdown functionality."""

import pytest
from unittest.mock import Mock, patch
from ggg_luck.main import LuckCalculator, WeeklyMatchup


class TestWeeklyBreakdown:
    """Test cases for weekly breakdown functionality."""

    def test_get_weekly_luck_breakdown_no_weeks(self):
        """Test behavior when no weeks are found."""
        mock_api = Mock()
        mock_api.make_api_request.side_effect = Exception("No data")
        
        calculator = LuckCalculator(mock_api)
        result = calculator.get_weekly_luck_breakdown("test_league")
        
        assert result['weeks'] == {}
        assert result['completed_weeks'] == []

    def test_get_weekly_luck_breakdown_with_data(self):
        """Test successful weekly breakdown generation."""
        # Mock API
        mock_api = Mock()
        
        # Mock successful week 1 call, then failure for week 2
        mock_api.make_api_request.side_effect = [
            # Week 1 (complete)
            {
                'fantasy_content': {
                    'league': {
                        'scoreboard': {
                            'matchups': {
                                'matchup': {
                                    'status': 'postevent',
                                    'winner_team_key': 'team1',
                                    'teams': {
                                        'team': [
                                            {
                                                'team_id': '1',
                                                'name': 'Team A',
                                                'team_points': {'total': '120.5'}
                                            },
                                            {
                                                'team_id': '2', 
                                                'name': 'Team B',
                                                'team_points': {'total': '110.0'}
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    }
                }
            },
            # Week 2 (no data - incomplete)
            Exception("Week not available"),
            # Repeat call for analysis
            {
                'fantasy_content': {
                    'league': {
                        'scoreboard': {
                            'matchups': {
                                'matchup': {
                                    'status': 'postevent',
                                    'winner_team_key': 'team1',
                                    'teams': {
                                        'team': [
                                            {
                                                'team_id': '1',
                                                'name': 'Team A',
                                                'team_points': {'total': '120.5'}
                                            },
                                            {
                                                'team_id': '2',
                                                'name': 'Team B', 
                                                'team_points': {'total': '110.0'}
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        ]
        
        calculator = LuckCalculator(mock_api)
        result = calculator.get_weekly_luck_breakdown("test_league")
        
        assert 1 in result['weeks']
        assert result['completed_weeks'] == [1]
        
        week_1_data = result['weeks'][1]
        assert 'luckiest' in week_1_data
        assert 'unluckiest' in week_1_data
        assert 'all_luck_scores' in week_1_data
        assert 'all_matchups' in week_1_data

    @patch.object(LuckCalculator, '_create_luck_ranking_chart')
    @patch.object(LuckCalculator, '_create_luck_distribution_chart')
    @patch.object(LuckCalculator, '_create_wins_comparison_chart')
    @patch.object(LuckCalculator, '_create_scoring_trends_chart')
    def test_generate_markdown_with_weekly_breakdown(self, mock_trends, mock_wins, mock_dist, mock_rank):
        """Test markdown generation includes weekly breakdown when league_key provided."""
        mock_api = Mock()
        calculator = LuckCalculator(mock_api)
        
        # Mock the weekly breakdown method
        calculator.get_weekly_luck_breakdown = Mock(return_value={
            'weeks': {
                1: {
                    'luckiest': {
                        'team_name': 'Team A',
                        'matchup': WeeklyMatchup(1, '1', 'Team A', 120.5, '2', 'Team B', 110.0, True),
                        'luck_score': 50.0
                    },
                    'unluckiest': {
                        'team_name': 'Team B', 
                        'matchup': WeeklyMatchup(1, '2', 'Team B', 110.0, '1', 'Team A', 120.5, False),
                        'luck_score': -50.0
                    }
                }
            },
            'completed_weeks': [1]
        })
        
        # Create some test luck metrics
        from ggg_luck.main import LuckMetrics
        luck_metrics = [
            LuckMetrics(
                team_id='1',
                team_name='Team A',
                total_luck_score=10.0,
                avg_luck_per_week=10.0,
                luckiest_week=None,
                unluckiest_week=None,
                weeks_played=1,
                should_have_wins=1,
                should_have_losses=0,
                luck_differential=0
            )
        ]
        
        # Generate markdown with league key
        markdown = calculator.generate_markdown_report(luck_metrics, "Test League", "test_league_key")
        
        # Check that weekly breakdown section is included
        assert "Weekly Luck Breakdown" in markdown
        assert "Team A (120.5 vs Team B 110.0, W) +50.0" in markdown
        assert "Team B (110.0 vs Team A 120.5, L) -50.0" in markdown

    @patch.object(LuckCalculator, '_create_luck_ranking_chart')
    @patch.object(LuckCalculator, '_create_luck_distribution_chart')
    @patch.object(LuckCalculator, '_create_wins_comparison_chart')
    @patch.object(LuckCalculator, '_create_scoring_trends_chart')
    def test_generate_markdown_without_league_key(self, mock_trends, mock_wins, mock_dist, mock_rank):
        """Test markdown generation without league_key shows fallback message."""
        mock_api = Mock()
        calculator = LuckCalculator(mock_api)
        
        from ggg_luck.main import LuckMetrics
        luck_metrics = [
            LuckMetrics(
                team_id='1',
                team_name='Team A',
                total_luck_score=10.0,
                avg_luck_per_week=10.0,
                luckiest_week=None,
                unluckiest_week=None,
                weeks_played=1,
                should_have_wins=1,
                should_have_losses=0,
                luck_differential=0
            )
        ]
        
        # Generate markdown without league key
        markdown = calculator.generate_markdown_report(luck_metrics, "Test League")
        
        # Check that fallback message is shown
        assert "Weekly breakdown requires league key" in markdown