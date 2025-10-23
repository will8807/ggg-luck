# GitHub Actions Setup Guide

This document explains how to configure GitHub Actions to automatically run your fantasy football luck analysis every Tuesday morning.

## 🔧 Required Repository Secrets

To run the workflow, you need to add the following secrets to your GitHub repository:

### Navigate to Repository Settings
1. Go to your GitHub repository
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret** for each of the following:

### Required Secrets

| Secret Name | Description | Where to Find |
|-------------|-------------|---------------|
| `YAHOO_CLIENT_ID` | Yahoo API Client ID | Yahoo Developer Console |
| `YAHOO_CLIENT_SECRET` | Yahoo API Client Secret | Yahoo Developer Console |
| `YAHOO_REDIRECT_URI` | OAuth callback URL | Usually `https://localhost:8443/callback` |

### Optional Secrets (for persistent authentication)
| Secret Name | Description |
|-------------|-------------|
| `YAHOO_ACCESS_TOKEN` | OAuth Access Token (if you have one) |
| `YAHOO_REFRESH_TOKEN` | OAuth Refresh Token (if you have one) |

## 📅 Schedule Configuration

The workflow is currently set to run:
- **Every Tuesday at 9:00 AM UTC**
- **Cron expression**: `0 9 * * 2`

### Adjust Timezone
To change the time zone, modify the cron expression in `.github/workflows/weekly-luck-analysis.yml`:

```yaml
schedule:
  # Examples for different times (all in UTC):
  - cron: '0 14 * * 2'  # Tuesday 2:00 PM UTC (9:00 AM EST)
  - cron: '30 16 * * 2' # Tuesday 4:30 PM UTC (11:30 AM EST)
  - cron: '0 12 * * 1'  # Monday 12:00 PM UTC
```

## 🎯 What the Workflow Does

1. **Checks out** your repository code
2. **Sets up Python 3.12** environment
3. **Installs** your project dependencies
4. **Runs the luck analysis** using your main.py script
5. **Commits and pushes** any generated reports back to the repository
6. **Creates artifacts** for download
7. **Creates releases** with weekly reports (optional)
8. **Deploys to GitHub Pages** (optional)

## 🔍 Manual Testing

You can manually trigger the workflow to test it:
1. Go to the **Actions** tab in your repository
2. Click on **Weekly Fantasy Football Luck Analysis**
3. Click **Run workflow**
4. Select the branch (usually `main`)
5. Click **Run workflow**

## 📊 Generated Outputs

The workflow will generate:
- Updated `luck_analysis_report.md`
- Chart images in the `charts/` directory
- Weekly release with analysis summary
- GitHub Pages deployment (if enabled)

## 🛠️ Troubleshooting

### Common Issues:

1. **Missing Secrets**: Make sure all required secrets are configured
2. **Authentication Errors**: Verify Yahoo API credentials are correct
3. **Permission Errors**: Ensure the repository has proper permissions set
4. **Timezone Issues**: Remember cron runs in UTC time

### Debug Steps:
1. Check the Actions tab for workflow run logs
2. Look at the "Run luck analysis" step for specific error messages
3. Verify your local setup works before troubleshooting the workflow

## 🔐 Security Notes

- Repository secrets are encrypted and only accessible to GitHub Actions
- Never commit API keys or tokens to your repository
- The workflow only has access to secrets you explicitly configure
- Generated tokens are scoped to repository access only

## 📈 Monitoring

You can monitor workflow runs in the **Actions** tab:
- ✅ Green checkmark: Successful run
- ❌ Red X: Failed run (click for details)
- 🟡 Yellow dot: In progress
- ⏸️ Gray: Skipped or cancelled

Set up notifications in your GitHub settings to get alerted about workflow failures.