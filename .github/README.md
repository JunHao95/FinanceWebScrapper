# GitHub Actions Setup for FinanceWebScrapper

## 🚀 Automated Finance Reports

This project includes GitHub Actions workflows for automated daily finance reports.

## 📋 Workflows

### 1. Daily Finance Report (`daily-finance-report.yml`)
- **Schedule**: Runs Monday-Friday at 9 AM UTC
- **Features**: 
  - Full scraper execution with all sources
  - Email delivery of reports
  - Artifact storage for 30 days
  - Performance optimizations enabled

### 2. Manual Test (`test-scraper.yml`)
- **Trigger**: Manual execution only
- **Purpose**: Testing single tickers or specific sources
- **Features**: Dry-run mode, debug logging

## ⚙️ Configuration

### Required Secrets
Set these in GitHub repository settings → Secrets and variables → Actions:

```
ALPHA_VANTAGE_API_KEY    # Your Alpha Vantage API key
FINHUB_API_KEY           # Your Finhub API key
FINANCE_SENDER_EMAIL     # Gmail address for sending reports
FINANCE_SENDER_PASSWORD  # Gmail app password (not regular password)
FINANCE_SMTP_SERVER      # smtp.gmail.com
FINANCE_SMTP_PORT        # 587
FINANCE_USE_TLS          # true
DEFAULT_EMAIL            # Default recipient email
```

### Gmail App Password Setup
1. Enable 2-factor authentication on your Gmail account
2. Go to Google Account settings
3. Security → App passwords
4. Generate an app password for "Mail"
5. Use this app password (not your regular password) in `FINANCE_SENDER_PASSWORD`

## 🔧 Manual Execution

### Run Daily Report Manually
1. Go to repository → Actions tab
2. Select "Daily Finance Report"
3. Click "Run workflow"
4. Optionally customize tickers and email

### Test Single Ticker
1. Go to repository → Actions tab
2. Select "Manual Finance Scraper Test"
3. Click "Run workflow"
4. Enter test ticker (e.g., AAPL)
5. Choose sources to test
6. Enable/disable dry-run mode

## 📊 Viewing Results

### Artifacts
- Reports are automatically uploaded as artifacts
- Available for 30 days after each run
- Download from Actions tab → specific run → Artifacts

### Logs
- Real-time logs visible during execution
- Stored logs also available in artifacts
- Debug information for troubleshooting

## 🕐 Schedule Customization

To change the schedule, edit `.github/workflows/daily-finance-report.yml`:

```yaml
schedule:
  - cron: '0 9 * * 1-5'  # 9 AM UTC, weekdays
  
# Examples:
# '0 14 * * 1-5'  # 2 PM UTC, weekdays  
# '30 8 * * *'    # 8:30 AM UTC, daily
# '0 9 * * 1'     # 9 AM UTC, Mondays only
```

## 🌍 Timezone Notes

- All times are in UTC
- To convert to your timezone:
  - EST: UTC - 5 hours
  - PST: UTC - 8 hours
  - Singapore: UTC + 8 hours

## 🚨 Troubleshooting

### Common Issues:
1. **Email not sending**: Check Gmail app password setup
2. **API rate limits**: Reduce ticker count or add delays
3. **Timeout errors**: Increase `timeout-minutes` in workflow
4. **Missing artifacts**: Check if job completed successfully

### Debug Steps:
1. Run manual test workflow first
2. Check logs for specific error messages
3. Verify all secrets are set correctly
4. Test with single ticker before full list

## 💰 GitHub Actions Limits

- **Free tier**: 2,000 minutes/month
- **Typical usage**: ~10-15 minutes per run
- **Daily runs**: ~5 hours/month (well within limits)
- **Storage**: Artifacts count toward storage quota
