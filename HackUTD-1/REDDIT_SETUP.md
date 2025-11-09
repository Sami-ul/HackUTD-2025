# Reddit API Setup Guide

## Getting Reddit API Credentials

The scraper now uses PRAW (Reddit API) instead of web scraping. You need to get API credentials.

### Step 1: Create a Reddit App

1. Go to https://www.reddit.com/prefs/apps
2. Scroll down and click **"create another app"** or **"create app"**
3. Fill in the form:
   - **Name**: `TMobile Sentiment Analyzer` (or any name you want)
   - **App type**: Select **"script"**
   - **Description**: Optional
   - **About URL**: Leave blank
   - **Redirect URI**: `http://localhost:8080` (required but not used for read-only)
4. Click **"create app"**

### Step 2: Get Your Credentials

After creating the app, you'll see:
- **Client ID**: The string under your app name (looks like: `abc123def456`)
- **Client Secret**: The "secret" field (looks like: `xyz789_secret_abc123`)

**Important**: The client ID is the string directly under your app name, NOT the "personal use script" text.

### Step 3: Set Environment Variables

#### On macOS/Linux:
```bash
export REDDIT_CLIENT_ID='your_client_id_here'
export REDDIT_CLIENT_SECRET='your_client_secret_here'
```

#### On Windows (Command Prompt):
```cmd
set REDDIT_CLIENT_ID=your_client_id_here
set REDDIT_CLIENT_SECRET=your_client_secret_here
```

#### On Windows (PowerShell):
```powershell
$env:REDDIT_CLIENT_ID='your_client_id_here'
$env:REDDIT_CLIENT_SECRET='your_client_secret_here'
```

### Step 4: Verify Setup

Test that it works:
```bash
cd hackutd-1
python -c "from src.reddit_scraper import RedditWebScraper; scraper = RedditWebScraper(); print('Success!')"
```

## Alternative: Pass Credentials Directly

Instead of environment variables, you can pass credentials directly:

```python
from src.reddit_scraper import RedditWebScraper

scraper = RedditWebScraper(
    client_id='your_client_id',
    client_secret='your_client_secret'
)
```

## Troubleshooting

### "Reddit API credentials required!"
- Make sure you set the environment variables correctly
- Check that there are no extra spaces or quotes
- Try passing credentials directly instead

### "401 Unauthorized"
- Double-check your client ID and secret
- Make sure you copied them correctly (no extra spaces)
- The client ID should be the string under the app name, not "personal use script"

### Rate Limiting
- PRAW automatically handles rate limiting
- Reddit allows 60 requests per minute for read-only access
- If you hit limits, wait a minute and try again

## Security Note

**Never commit your credentials to git!**

If you need to share credentials with your team:
1. Use environment variables
2. Create a `.env` file (and add it to `.gitignore`)
3. Use a secrets management service

## Need Help?

- Reddit API Documentation: https://www.reddit.com/dev/api
- PRAW Documentation: https://praw.readthedocs.io/
- Reddit App Preferences: https://www.reddit.com/prefs/apps


