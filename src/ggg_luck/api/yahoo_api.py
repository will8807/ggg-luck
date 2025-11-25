"""Yahoo Fantasy Football API handler."""

import os
from typing import Dict, List, Optional, Any
import requests
import xmltodict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class YahooFantasyAPI:
    """Handler for Yahoo Fantasy Football API connections."""

    def __init__(self):
        """Initialize the Yahoo Fantasy API client."""
        self.client_id = os.getenv('YAHOO_CLIENT_ID')
        self.client_secret = os.getenv('YAHOO_CLIENT_SECRET')
        self.app_id = os.getenv('YAHOO_APP_ID')  # Optional for some endpoints
        self.redirect_uri = os.getenv('YAHOO_REDIRECT_URI', 'http://localhost:8080/callback')
        
        # Load existing tokens from environment if available
        self.access_token = os.getenv('YAHOO_ACCESS_TOKEN')
        self.refresh_token = os.getenv('YAHOO_REFRESH_TOKEN')
        
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Yahoo API credentials not found. Please set YAHOO_CLIENT_ID and "
                "YAHOO_CLIENT_SECRET environment variables."
            )

    def get_auth_url(self) -> str:
        """Get the authorization URL for OAuth2 flow."""
        auth_url = (
            "https://api.login.yahoo.com/oauth2/request_auth?"
            f"client_id={self.client_id}&"
            f"redirect_uri={self.redirect_uri}&"
            "response_type=code&"
            "scope=fspt-r"  # Fantasy Sports Read permission
        )
        return auth_url

    def exchange_code_for_token(self, auth_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        token_url = "https://api.login.yahoo.com/oauth2/get_token"
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'code': auth_code,
            'grant_type': 'authorization_code'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        print(f"🔍 Token Exchange Request:")
        print(f"   URL: {token_url}")
        print(f"   Redirect URI: {self.redirect_uri}")
        print(f"   Auth Code: {auth_code[:10]}...")
        
        response = requests.post(token_url, data=data, headers=headers)
        
        print(f"🔍 Token Response Status: {response.status_code}")
        print(f"🔍 Token Response: {response.text}")
        
        if response.status_code != 200:
            raise Exception(f"Token exchange failed: {response.status_code} - {response.text}")
        
        token_data = response.json()
        self.access_token = token_data.get('access_token')
        self.refresh_token = token_data.get('refresh_token')
        
        # Automatically save tokens to .env file
        self.save_tokens_to_env()
        
        return token_data

    def save_tokens_to_env(self):
        """Save access and refresh tokens to .env file."""
        if not self.access_token:
            return
            
        env_file_path = '.env'
        
        # Read existing .env content
        env_content = {}
        if os.path.exists(env_file_path):
            with open(env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_content[key.strip()] = value.strip()
        
        # Update token values
        env_content['YAHOO_ACCESS_TOKEN'] = self.access_token
        if self.refresh_token:
            env_content['YAHOO_REFRESH_TOKEN'] = self.refresh_token
        
        # Write back to .env file
        with open(env_file_path, 'w') as f:
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")
        
        print(f"💾 Tokens saved to {env_file_path}")

    def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh the access token using refresh token."""
        if not self.refresh_token:
            raise ValueError("No refresh token available")
            
        token_url = "https://api.login.yahoo.com/oauth2/get_token"
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.post(token_url, data=data, headers=headers)
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data.get('access_token')
        
        # Save the refreshed token
        self.save_tokens_to_env()
        
        return token_data

    def make_api_request(self, endpoint: str) -> Dict[str, Any]:
        """Make an authenticated request to the Yahoo Fantasy API."""
        if not self.access_token:
            raise ValueError("No access token available. Please authenticate first.")
            
        base_url = "https://fantasysports.yahooapis.com/fantasy/v2"
        url = f"{base_url}/{endpoint}"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        
        # Try to refresh token if unauthorized
        if response.status_code == 401 and self.refresh_token:
            self.refresh_access_token()
            headers['Authorization'] = f'Bearer {self.access_token}'
            response = requests.get(url, headers=headers)
        
        
        response.raise_for_status()
        
        # Handle empty responses
        if not response.text.strip():
            raise ValueError("API returned empty response")
        
        # Check if response is XML (Yahoo Fantasy API returns XML)
        content_type = response.headers.get('content-type', '').lower()
        if 'xml' in content_type or response.text.strip().startswith('<?xml'):
            try:
                # Convert XML to dictionary
                xml_dict = xmltodict.parse(response.text)
                return xml_dict
            except Exception as e:
                raise ValueError(f"Failed to parse XML response: {e}") from e
        else:
            # Try JSON parsing for other responses
            try:
                return response.json()
            except ValueError as e:
                raise ValueError(f"API returned unsupported response format: {response.text[:100]}") from e

    def get_user_leagues(self, game_key: str = "nfl") -> Dict[str, Any]:
        """Get user's fantasy leagues for a specific game."""
        endpoint = f"users;use_login=1/games;game_keys={game_key}/leagues"
        return self.make_api_request(endpoint)

    def get_league_info(self, league_key: str) -> Dict[str, Any]:
        """Get information about a specific league."""
        endpoint = f"league/{league_key}"
        return self.make_api_request(endpoint)

    def get_league_standings(self, league_key: str) -> Dict[str, Any]:
        """Get standings for a specific league."""
        endpoint = f"league/{league_key}/standings"
        return self.make_api_request(endpoint)

    def get_team_info(self, team_key: str) -> Dict[str, Any]:
        """Get information about a specific team."""
        endpoint = f"team/{team_key}"
        return self.make_api_request(endpoint)

    def get_team_roster(self, team_key: str, week: Optional[int] = None) -> Dict[str, Any]:
        """Get roster for a specific team and week."""
        endpoint = f"team/{team_key}/roster"
        if week:
            endpoint += f";week={week}"
        return self.make_api_request(endpoint)

    def get_league_players(self, league_key: str, 
                          start: int = 0, 
                          count: int = 25,
                          status: str = "ALL",
                          position: Optional[str] = None) -> Dict[str, Any]:
        """Get players in a league with pagination and filtering."""
        endpoint = f"league/{league_key}/players;start={start};count={count}"
        
        # Add status filter (A = available/free agents, T = taken, ALL = all players)
        if status != "ALL":
            endpoint += f";status={status}"
            
        # Add position filter
        if position:
            endpoint += f";position={position}"
            
        return self.make_api_request(endpoint)

    def get_league_free_agents(self, league_key: str,
                              position: Optional[str] = None,
                              start: int = 0,
                              count: int = 25,
                              sort: str = "OR") -> Dict[str, Any]:
        """
        Get free agents (available players) in a league.
        
        Args:
            league_key: Yahoo league key
            position: Position filter (QB, RB, WR, TE, K, DEF)
            start: Starting index for pagination
            count: Number of players to return
            sort: Sort criteria (OR = ownership percentage, AR = add/drop ranking)
        """
        endpoint = f"league/{league_key}/players;start={start};count={count};status=A"
        
        # Add position filter
        if position:
            endpoint += f";position={position}"
            
        # Add sort parameter (OR = ownership rank, AR = add/drop rank)
        endpoint += f";sort={sort}"
            
        return self.make_api_request(endpoint)

    def get_league_teams(self, league_key: str) -> Dict[str, Any]:
        """Get all teams in a league."""
        endpoint = f"league/{league_key}/teams"
        return self.make_api_request(endpoint)

    def get_player_stats(self, player_key: str, 
                        stat_type: str = "stats",
                        week: Optional[int] = None) -> Dict[str, Any]:
        """Get stats for a specific player."""
        endpoint = f"player/{player_key}/{stat_type}"
        if week:
            endpoint += f";week={week}"
        return self.make_api_request(endpoint)


# Convenience function for easy import
def create_yahoo_api() -> YahooFantasyAPI:
    """Create and return a Yahoo Fantasy API instance."""
    return YahooFantasyAPI()