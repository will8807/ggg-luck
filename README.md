# 🏈 GGG Luck - Fantasy Football Luck Calculator

A sophisticated fantasy football analysis tool that calculates team "luck" by comparing actual wins vs. expected wins based on weekly scoring performance and opponent strength.

## 🎯 What It Does

- **Connects to Yahoo Fantasy API** with OAuth2 authentication
- **Analyzes weekly matchups** to determine luck scores
- **Calculates expected wins** based on scoring vs. all possible opponents  
- **Generates beautiful reports** with charts and rankings
- **Automatically detects completed weeks** (excludes in-progress games)

## 📊 Sample Analysis

Check out our [latest analysis report](analysis_report.md) to see the tool in action!

### Key Features:
- 🍀 **Luck Rankings**: See which teams are getting lucky breaks
- 📈 **Visual Charts**: Comprehensive graphs showing luck distribution
- ⚖️ **Expected vs Actual Wins**: Compare what records "should be"
- 🎰 **Extreme Weeks**: Highlight the most lucky/unlucky matchups

## 🏗️ What This Generates

- **Comprehensive Markdown Report** ([see example](analysis_report.md))
- **Interactive Charts** showing luck rankings, distribution, and win comparisons
- **GitHub-ready visualizations** with professional formatting
- **Detailed team analysis** with should-have records and luck differentials

## � Available Commands

- `ggg-luck-analyze` - Run complete luck analysis with markdown report and charts
- `ggg-luck-example` - Interactive authentication setup and testing
- `ggg-luck-debug` - Debug API connections and configurations
- `ggg-luck-test` - Test Yahoo API connectivity

## �📋 Prerequisites

### Yahoo Developer App Setup

1. Go to [Yahoo Developer Console](https://developer.yahoo.com/apps/)
2. Create a new app with these settings:
   - **Application Type**: Web Application
   - **Callback Domain**: localhost  
   - **API Permissions**: Fantasy Sports (Read)
3. Note your Client ID and Client Secret

### Environment Setup

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your Yahoo API credentials:
YAHOO_CLIENT_ID=your_client_id_here
YAHOO_CLIENT_SECRET=your_client_secret_here
YAHOO_REDIRECT_URI=https://localhost:8443/callback
```

## 💻 Usage Examples

### Complete Analysis Workflow

```bash
# 1. Authenticate with Yahoo (one-time setup)
uv run ggg-luck-example

# 2. Run full luck analysis (generates report + charts)
uv run ggg-luck-analyze

# 3. View generated files:
# - analysis_report.md (main report)
# - charts/luck_rankings.png
# - charts/luck_distribution.png  
# - charts/wins_comparison.png
```

### Programmatic Usage

```python
from ggg_luck.main import LuckCalculator
from ggg_luck.api import YahooFantasyAPI

# Initialize components
api = YahooFantasyAPI()
calculator = LuckCalculator(api)

# Run analysis for a specific league
league_key = "461.l.168803"  # Your league key
luck_metrics = calculator.analyze_team_luck(league_key)

# Generate markdown report with charts
calculator.save_markdown_report(luck_metrics, "my_report.md", "My League")

# Display console results
calculator.display_luck_analysis(luck_metrics)
```

### Core Features

- **Automatic Week Detection** - Only analyzes completed weeks
- **OAuth2 HTTPS Authentication** - Secure token management with automatic refresh
- **Sophisticated Luck Algorithm** - Compares actual vs expected performance
- **Professional Visualizations** - matplotlib/seaborn charts with proper styling
- **GitHub Integration** - Markdown reports ready for repository hosting

## 🏗️ Project Structure

```
ggg-luck/
├── src/ggg_luck/
│   ├── main.py              # Core luck calculation and report generation
│   ├── api/
│   │   ├── yahoo_api.py     # Yahoo Fantasy API client with OAuth2
│   │   └── oauth_server.py  # HTTPS callback server for authentication
│   ├── cli_tools/
│   │   ├── cli.py           # Command-line utilities
│   │   └── example.py       # Interactive authentication setup
│   └── utils/
│       └── debug.py         # Debugging and diagnostics
├── charts/                  # Generated visualization files
│   ├── luck_rankings.png
│   ├── luck_distribution.png
│   └── wins_comparison.png
├── tests/                   # Unit tests
├── luck_analysis_report.md  # Generated analysis report
├── pyproject.toml          # Project configuration with CLI scripts
└── .env.example            # Environment template
```

## 🔐 Authentication & Security

### HTTPS OAuth2 Flow
1. **Secure HTTPS Server**: Automatically starts on localhost:8443 with self-signed certificates
2. **Yahoo Authorization**: Opens browser to Yahoo's OAuth consent page
3. **Secure Token Exchange**: Handles callback and exchanges authorization code for tokens
4. **Automatic Refresh**: Tokens automatically refresh when expired
5. **Environment Storage**: Securely stores credentials in `.env` file

### Technical Features

- **Week Completion Detection**: Automatically excludes incomplete/ongoing games
- **Robust XML Parsing**: Handles Yahoo's XML API responses with comprehensive error handling
- **Professional Visualizations**: High-quality charts (300 DPI) suitable for presentations
- **GitHub Integration**: Generated reports render perfectly on GitHub with embedded images
- **Comprehensive Logging**: Detailed progress tracking and error diagnostics

## 🧪 Development

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
├── src/ggg_luck/
│   ├── main.py              # Core luck calculation and report generation
│   ├── api/
│   │   ├── yahoo_api.py     # Yahoo Fantasy API client with OAuth2
│   │   └── oauth_server.py  # HTTPS callback server for authentication
│   ├── cli_tools/
│   │   ├── cli.py           # Command-line utilities
│   │   └── example.py       # Interactive authentication setup
│   └── utils/
│       └── debug.py         # Debugging and diagnostics
├── charts/                  # Generated visualization files
│   ├── luck_rankings.png
│   ├── luck_distribution.png
│   └── wins_comparison.png
├── tests/                   # Unit tests
├── luck_analysis_report.md  # Generated analysis report
├── pyproject.toml          # Project configuration with CLI scripts
└── .env.example            # Environment template
```

## 🔐 Authentication & Security

### HTTPS OAuth2 Flow
1. **Secure HTTPS Server**: Automatically starts on localhost:8443 with self-signed certificates
2. **Yahoo Authorization**: Opens browser to Yahoo's OAuth consent page
3. **Secure Token Exchange**: Handles callback and exchanges authorization code for tokens
4. **Automatic Refresh**: Tokens automatically refresh when expired
5. **Environment Storage**: Securely stores credentials in `.env` file

### Technical Features

- **Week Completion Detection**: Automatically excludes incomplete/ongoing games
- **Robust XML Parsing**: Handles Yahoo's XML API responses with comprehensive error handling
- **Professional Visualizations**: High-quality charts (300 DPI) suitable for presentations
- **GitHub Integration**: Generated reports render perfectly on GitHub with embedded images
- **Comprehensive Logging**: Detailed progress tracking and error diagnostics

## � Automated Weekly Analysis

This project includes GitHub Actions workflow for automated weekly analysis every Tuesday morning:

### Quick Setup
1. **Add Repository Secrets**: Configure your Yahoo API credentials in GitHub repository settings
2. **Enable Actions**: The workflow runs automatically every Tuesday at 9 AM UTC
3. **Manual Trigger**: Test anytime from the Actions tab

See [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md) for detailed setup instructions.

### Test Locally First
```bash
# Test your setup before deploying to GitHub Actions
python test_workflow_locally.py
```

### What Gets Generated Automatically
- 📊 Updated `analysis_report.md` with latest data  
- 📈 Fresh charts in `/charts` directory
- 🏷️ Tagged releases for each week's analysis
- 🌐 Optional GitHub Pages deployment

## �🧪 Development

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=ggg_luck

# Test specific functionality
uv run pytest tests/test_yahoo_api.py -v

# Test GitHub Actions setup locally
python test_workflow_locally.py
```

## 🤝 Contributing

This project is built for the "Gang of Gridiron Gurus" fantasy league, but the code is designed to work with any Yahoo Fantasy Football league. Feel free to fork and adapt for your own league!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`uv run pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

MIT License - feel free to use this for your own fantasy league analysis!

**Note**: This project uses the Yahoo Fantasy Sports API and is subject to Yahoo's Terms of Service.

---

*Built with ❤️ for fantasy football fanatics who love data-driven insights*
