# 🏈 GGG Luck - Fantasy Football Luck Calculator

A sophisticated fantasy football analysis tool that calculates team "luck" by comparing actual wins vs. expected wins based on weekly scoring performance and opponent strength.

## 🎯 What It Does

- **Connects to Yahoo Fantasy API** with OAuth2 authentication
- **Analyzes weekly matchups** to determine luck scores
- **Calculates expected wins** based on scoring vs. all possible opponents  
- **Generates beautiful reports** with charts and rankings
- **Automatically detects completed weeks** (excludes in-progress games)

## 📊 Sample Analysis

Check out our [latest luck analysis report](luck_analysis_report.md) to see the tool in action!

### Key Features:
- 🍀 **Luck Rankings**: See which teams are getting lucky breaks
- 📈 **Visual Charts**: Comprehensive graphs showing luck distribution
- ⚖️ **Expected vs Actual Wins**: Compare what records "should be"
- 🎰 **Extreme Weeks**: Highlight the most lucky/unlucky matchups
- 🛠️ Easy-to-use CLI tools

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Clone the repository
git clone https://github.com/will8807/ggg-luck.git
cd ggg-luck

# Install dependencies
uv sync
```

## Setup

### 1. Create Yahoo Developer App

1. Go to [Yahoo Developer Console](https://developer.yahoo.com/apps/)
2. Create a new app with these settings:
   - **Application Type**: Web Application
   - **Callback Domain**: localhost
   - **API Permissions**: Fantasy Sports (Read)
3. Note your Client ID and Client Secret

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your credentials
YAHOO_CLIENT_ID=your_client_id_here
YAHOO_CLIENT_SECRET=your_client_secret_here
YAHOO_REDIRECT_URI=http://localhost:8080/callback
```

### 3. Test Connection

```bash
# Test your API credentials
uv run ggg-luck-test
```

## Usage

### CLI Tools

```bash
# Test API connection
uv run ggg-luck-test

# Run authentication example
uv run ggg-luck-example

# Run main application
uv run ggg-luck
```

### Python API

```python
from ggg_luck.yahoo_api import YahooFantasyAPI

# Initialize the API client
api = YahooFantasyAPI()

# Get authorization URL
auth_url = api.get_auth_url()
print(f"Visit: {auth_url}")

# Exchange authorization code for token
auth_code = input("Enter auth code: ")
token_data = api.exchange_code_for_token(auth_code)

# Now you can make API calls
leagues = api.get_user_leagues("nfl")
standings = api.get_league_standings("league_key_here")
```

### Available API Methods

- `get_user_leagues(game_key)` - Get user's fantasy leagues
- `get_league_info(league_key)` - Get league information
- `get_league_standings(league_key)` - Get league standings
- `get_team_info(team_key)` - Get team information
- `get_team_roster(team_key, week)` - Get team roster
- `get_league_players(league_key)` - Get league players
- `get_player_stats(player_key, week)` - Get player statistics

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=ggg_luck

# Run specific test file
uv run pytest tests/test_yahoo_api.py -v
```

### Project Structure

```
ggg-luck/
├── src/
│   └── ggg_luck/
│       ├── __init__.py
│       ├── main.py          # Main application
│       ├── yahoo_api.py     # Yahoo API client
│       ├── cli.py           # CLI tools
│       └── example.py       # Usage examples
├── tests/
│   ├── test_main.py
│   └── test_yahoo_api.py
├── .env.example             # Environment template
├── pyproject.toml          # Project configuration
└── README.md
```

## Authentication Flow

1. **Get Authorization URL**: Call `get_auth_url()` to get the Yahoo OAuth URL
2. **User Authorization**: User visits URL and authorizes your app
3. **Exchange Code**: Use the callback code with `exchange_code_for_token()`
4. **Make API Calls**: Use the access token for all subsequent API requests
5. **Token Refresh**: Automatically refresh tokens when they expire

## Error Handling

The API client includes comprehensive error handling:

- **Missing Credentials**: Clear error messages for setup issues
- **Token Expiration**: Automatic token refresh when possible
- **API Errors**: Proper HTTP error handling with meaningful messages
- **Network Issues**: Graceful handling of connection problems

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project uses the Yahoo Fantasy Sports API and is subject to Yahoo's Terms of Service.
