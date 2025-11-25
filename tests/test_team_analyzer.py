"""Tests for the team analysis functionality."""

import pytest
from unittest.mock import Mock, patch
from ggg_luck.team_analyzer import TeamAnalyzer, Player, TeamRoster, FreeAgent, LeagueData
from ggg_luck.api import YahooFantasyAPI


class TestTeamAnalyzer:
    """Test cases for TeamAnalyzer class."""
    
    @pytest.fixture
    def mock_api(self):
        """Create a mock Yahoo API."""
        api = Mock(spec=YahooFantasyAPI)
        api.access_token = "mock_token"
        return api
    
    @pytest.fixture
    def analyzer(self, mock_api):
        """Create a TeamAnalyzer with mocked API."""
        return TeamAnalyzer(mock_api)
    
    def test_player_creation(self):
        """Test Player dataclass creation."""
        player = Player(
            player_id="123",
            name="Test Player",
            position="RB",
            team="NYG",
            status="starter",
            bye_week=7,
            injury_status="Healthy"
        )
        
        assert player.player_id == "123"
        assert player.name == "Test Player"
        assert player.position == "RB"
        assert player.team == "NYG"
        assert player.status == "starter"
        assert player.bye_week == 7
        assert player.injury_status == "Healthy"
    
    def test_team_roster_creation(self):
        """Test TeamRoster dataclass creation."""
        player1 = Player("1", "QB Player", "QB", "NYG", "starter")
        player2 = Player("2", "RB Player", "RB", "DAL", "bench")
        
        roster = TeamRoster(
            team_id="team1",
            team_name="Test Team",
            players=[player1, player2],
            starting_lineup=[player1],
            bench_players=[player2],
            ir_players=[]
        )
        
        assert roster.team_id == "team1"
        assert roster.team_name == "Test Team"
        assert len(roster.players) == 2
        assert len(roster.starting_lineup) == 1
        assert len(roster.bench_players) == 1
        assert len(roster.ir_players) == 0
    
    def test_free_agent_creation(self):
        """Test FreeAgent dataclass creation."""
        fa = FreeAgent(
            player_id="456",
            name="Free Agent",
            position="WR",
            team="MIA",
            ownership_percentage=15.5,
            bye_week=9
        )
        
        assert fa.player_id == "456"
        assert fa.name == "Free Agent"
        assert fa.position == "WR"
        assert fa.team == "MIA"
        assert fa.ownership_percentage == 15.5
        assert fa.bye_week == 9
    
    def test_league_data_creation(self):
        """Test LeagueData dataclass creation."""
        player = Player("1", "Test Player", "QB", "NYG", "starter")
        roster = TeamRoster("team1", "Team 1", [player], [player], [], [])
        fa = FreeAgent("2", "Free Agent", "RB", "DAL")
        
        league_data = LeagueData(
            league_id="league123",
            league_name="Test League",
            team_rosters=[roster],
            free_agents=[fa]
        )
        
        assert league_data.league_id == "league123"
        assert league_data.league_name == "Test League"
        assert len(league_data.team_rosters) == 1
        assert len(league_data.free_agents) == 1
    
    def test_analyzer_initialization(self, mock_api):
        """Test TeamAnalyzer initialization."""
        analyzer = TeamAnalyzer(mock_api)
        assert analyzer.api == mock_api
    
    def test_generate_team_analysis_prompt_basic(self, analyzer):
        """Test basic prompt generation."""
        # Create test data
        player1 = Player("1", "Patrick Mahomes", "QB", "KC", "QB")
        player2 = Player("2", "Saquon Barkley", "RB", "NYG", "RB")
        bench_player = Player("3", "Backup RB", "RB", "DAL", "BN")
        
        target_roster = TeamRoster(
            team_id="team1",
            team_name="Test Team",
            players=[player1, player2, bench_player],
            starting_lineup=[player1, player2],
            bench_players=[bench_player],
            ir_players=[]
        )
        
        other_roster = TeamRoster(
            team_id="team2",
            team_name="Other Team",
            players=[Player("4", "Other QB", "QB", "BUF", "QB")],
            starting_lineup=[Player("4", "Other QB", "QB", "BUF", "QB")],
            bench_players=[],
            ir_players=[]
        )
        
        fa = FreeAgent("5", "Free Agent RB", "RB", "MIA", ownership_percentage=25.0)
        
        league_data = LeagueData(
            league_id="league123",
            league_name="Test League",
            team_rosters=[target_roster, other_roster],
            free_agents=[fa]
        )
        
        # Generate prompt
        prompt = analyzer.generate_team_analysis_prompt("team1", league_data, "league123")
        
        # Verify prompt contains expected content
        assert "Test League" in prompt
        assert "Test Team" in prompt
        assert "Patrick Mahomes" in prompt
        assert "Saquon Barkley" in prompt
        assert "Free Agent RB" in prompt
        assert "Other Team" in prompt
        assert "Analysis Request" in prompt
    
    def test_generate_team_analysis_prompt_team_not_found(self, analyzer):
        """Test prompt generation with invalid team ID."""
        league_data = LeagueData(
            league_id="league123",
            league_name="Test League",
            team_rosters=[],
            free_agents=[]
        )
        
        with pytest.raises(ValueError, match="Team nonexistent not found"):
            analyzer.generate_team_analysis_prompt("nonexistent", league_data, "league123")


if __name__ == "__main__":
    pytest.main([__file__])