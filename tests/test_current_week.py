"""Tests for current week functionality."""

import pytest
from unittest.mock import Mock, patch
from ggg_luck.main import LuckCalculator, WeeklyMatchup


class TestCurrentWeekSummary:
    """Test cases for current week summary functionality."""

    def test_get_current_week_summary_no_weeks(self):
        """Test behavior when no weeks are found."""
        mock_api = Mock()
        mock_api.make_api_request.side_effect = Exception("No data")
        
        calculator = LuckCalculator(mock_api)
        result = calculator.get_current_week_summary("test_league")
        
        assert result['error'] == 'No completed weeks found'
        assert result['week'] is None
        assert result['matchups'] == []

    def test_get_current_week_summary_with_data(self):
        """Test successful current week summary generation."""
        # Mock API
        mock_api = Mock()
        
        # Mock successful week 1 call
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
        result = calculator.get_current_week_summary("test_league")
        
        assert result['error'] is None
        assert result['week'] == 1
        assert len(result['matchups']) == 2  # Two teams means two matchup objects
        assert '1' in result['luck_scores']
        assert '2' in result['luck_scores']

    def test_display_current_week_summary_with_error(self, capsys):
        """Test display function with error."""
        mock_api = Mock()
        calculator = LuckCalculator(mock_api)
        
        week_summary = {
            'error': 'Test error message',
            'week': None,
            'matchups': [],
            'luck_scores': {}
        }
        
        calculator.display_current_week_summary(week_summary)
        
        captured = capsys.readouterr()
        assert "❌ Test error message" in captured.out

    def test_display_current_week_summary_success(self, capsys):
        """Test successful display of current week summary."""
        mock_api = Mock()
        calculator = LuckCalculator(mock_api)
        
        # Create mock data
        matchup1 = WeeklyMatchup(
            week=5,
            team_id='1',
            team_name='Team A',
            team_score=120.5,
            opponent_id='2',
            opponent_name='Team B',
            opponent_score=110.0,
            won=True
        )
        
        matchup2 = WeeklyMatchup(
            week=5,
            team_id='2',
            team_name='Team B',
            team_score=110.0,
            opponent_id='1',
            opponent_name='Team A',
            opponent_score=120.5,
            won=False
        )
        
        week_summary = {
            'error': None,
            'week': 5,
            'matchups': [matchup1, matchup2],
            'team_matchups': {'1': matchup1, '2': matchup2},
            'luck_scores': {'1': 25.0, '2': -25.0}
        }
        
        calculator.display_current_week_summary(week_summary)
        
        captured = capsys.readouterr()
        assert "CURRENT WEEK LUCK SUMMARY - WEEK 5" in captured.out
        assert "Team A" in captured.out
        assert "Team B" in captured.out
        assert "+25.0" in captured.out
        assert "-25.0" in captured.out