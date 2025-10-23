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
        self.access_token = None
        self.refresh_token = None
        
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
        
        return token_data

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
                          count: int = 25) -> Dict[str, Any]:
        """Get players in a league with pagination."""
        endpoint = f"league/{league_key}/players;start={start};count={count}"
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