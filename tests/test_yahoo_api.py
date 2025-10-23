"""Tests for Yahoo Fantasy API module."""

import pytest
from unittest.mock import Mock, patch
from ggg_luck.api import YahooFantasyAPI


class TestYahooFantasyAPI:
    """Test cases for YahooFantasyAPI class."""

    def test_init_missing_credentials(self):
        """Test that initialization fails without credentials."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="Yahoo API credentials not found"):
                YahooFantasyAPI()

    @patch.dict('os.environ', {
        'YAHOO_CLIENT_ID': 'test_client_id',
        'YAHOO_CLIENT_SECRET': 'test_client_secret'
    })
    def test_init_with_credentials(self):
        """Test successful initialization with credentials."""
        api = YahooFantasyAPI()
        assert api.client_id == 'test_client_id'
        assert api.client_secret == 'test_client_secret'
        assert api.redirect_uri == 'http://localhost:8080/callback'

    @patch.dict('os.environ', {
        'YAHOO_CLIENT_ID': 'test_client_id',
        'YAHOO_CLIENT_SECRET': 'test_client_secret',
        'YAHOO_REDIRECT_URI': 'https://example.com/callback'
    })
    def test_init_with_custom_redirect_uri(self):
        """Test initialization with custom redirect URI."""
        api = YahooFantasyAPI()
        assert api.redirect_uri == 'https://example.com/callback'

    @patch.dict('os.environ', {
        'YAHOO_CLIENT_ID': 'test_client_id',
        'YAHOO_CLIENT_SECRET': 'test_client_secret'
    })
    def test_get_auth_url(self):
        """Test generation of authorization URL."""
        api = YahooFantasyAPI()
        auth_url = api.get_auth_url()
        
        assert 'https://api.login.yahoo.com/oauth2/request_auth' in auth_url
        assert 'client_id=test_client_id' in auth_url
        assert 'redirect_uri=http://localhost:8080/callback' in auth_url
        assert 'response_type=code' in auth_url
        assert 'scope=fspt-r' in auth_url

    @patch.dict('os.environ', {
        'YAHOO_CLIENT_ID': 'test_client_id',
        'YAHOO_CLIENT_SECRET': 'test_client_secret'
    })
    @patch('ggg_luck.api.yahoo_api.requests.post')
    def test_exchange_code_for_token_success(self, mock_post):
        """Test successful token exchange."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token'
        }
        mock_post.return_value = mock_response
        
        api = YahooFantasyAPI()
        result = api.exchange_code_for_token('test_auth_code')
        
        assert api.access_token == 'test_access_token'
        assert api.refresh_token == 'test_refresh_token'
        assert result['access_token'] == 'test_access_token'

    @patch.dict('os.environ', {
        'YAHOO_CLIENT_ID': 'test_client_id',
        'YAHOO_CLIENT_SECRET': 'test_client_secret'
    })
    def test_make_api_request_no_token(self):
        """Test API request without access token."""
        api = YahooFantasyAPI()
        
        with pytest.raises(ValueError, match="No access token available"):
            api.make_api_request('test/endpoint')

    @patch.dict('os.environ', {
        'YAHOO_CLIENT_ID': 'test_client_id',
        'YAHOO_CLIENT_SECRET': 'test_client_secret'
    })
    @patch('ggg_luck.api.yahoo_api.requests.get')
    def test_make_api_request_success(self, mock_get):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.json.return_value = {'test': 'data'}
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        api = YahooFantasyAPI()
        api.access_token = 'test_token'
        
        result = api.make_api_request('test/endpoint')
        
        assert result == {'test': 'data'}
        mock_get.assert_called_once()
        
        # Check that authorization header was set
        call_args = mock_get.call_args
        headers = call_args[1]['headers']
        assert headers['Authorization'] == 'Bearer test_token'