# Tweet Scheduler Bot

A Python bot that automatically posts to **Twitter/X** and **Discord** on a configurable schedule.

- Reads tweet content from a CSV file
- Posts to Discord via webhook for team reminders
- Rotates through content categories (goals, plans, campaigns) evenly
- Tracks what's been posted so nothing repeats
- Runs as a systemd service on any Linux VPS

## Quick Start

```bash
git clone <this-repo>
cd tweet-scheduler
chmod +x install.sh
./install.sh
```

The install script handles everything: Python venv, dependencies, API keys, and systemd service.

## Requirements

- Python 3.9+
- Twitter/X API keys (Free tier works)
- Discord webhook URL

---

## Setup Guide

### Step 1: Get Twitter API Keys

1. Go to [developer.x.com](https://developer.x.com/en/portal/dashboard)
2. Sign up for a **Free** developer account
3. Create a new **Project** and **App**
4. In your app settings, go to **Keys and tokens**
5. Generate:
   - **API Key** and **API Secret** (under Consumer Keys)
   - **Access Token** and **Access Token Secret** (under Authentication Tokens)
   - Make sure the access token has **Read and Write** permissions
6. Save all 4 values — you'll need them during install

### Step 2: Create a Discord Webhook

1. Open your Discord server
2. Go to **Server Settings** > **Integrations** > **Webhooks**
3. Click **New Webhook**
4. Name it (e.g., "Scheduler Bot")
5. Select the channel where reminders should post
6. Click **Copy Webhook URL**
7. Save this URL — you'll need it during install

### Step 3: Add Your Content

Edit the CSV files with your own content:

**tweets.csv** — Content that gets posted to Twitter/X:
```csv
text,category
"Your tweet text here",goal
"Another tweet",campaign
"Planning update",plan
```

**reminders.csv** — Content that gets posted to Discord:
```csv
text,category
"Team reminder about Q1 goals",goal
"Campaign status check",campaign
```

Categories can be anything you want (goal, plan, campaign, update, etc.). The bot rotates through them so you don't get 5 "goal" posts in a row.

### Step 4: Configure the Schedule

Edit `config.yaml`:

```yaml
twitter:
  enabled: true
  schedule:
    # Post at specific times each day:
    times: ["09:00", "13:00", "18:00"]
    # OR post every N hours (comment out 'times' first):
    # interval_hours: 4
    timezone: "America/New_York"
  behavior_on_empty: "loop"  # "loop" = restart from top, "stop" = stop posting
```

Use either `times` (specific times) OR `interval_hours` (every N hours) — not both.

### Step 5: Install & Run

**On your VPS:**
```bash
git clone <this-repo>
cd tweet-scheduler
chmod +x install.sh
./install.sh
```

The installer will:
1. Create a Python virtual environment
2. Install dependencies
3. Prompt you for API keys (creates `.env`)
4. Optionally install a systemd service

**Run manually (for testing):**
```bash
cd tweet-scheduler
./venv/bin/python bot.py
```

---

## Managing the Bot

### Check status
```bash
sudo systemctl status tweet-scheduler
```

### View live logs
```bash
journalctl -u tweet-scheduler -f
```

### Restart after editing CSVs or config
```bash
sudo systemctl restart tweet-scheduler
```

### Stop the bot
```bash
sudo systemctl stop tweet-scheduler
```

### Update content
Edit the CSVs directly on your VPS, then restart:
```bash
nano tweets.csv
nano reminders.csv
sudo systemctl restart tweet-scheduler
```

---

## How It Works

1. Bot starts and loads `config.yaml` and `.env`
2. At each scheduled time, it reads the CSV and picks the next unposted item
3. **Category rotation**: If the last post was a "goal", the next one picks from "plan" or "campaign"
4. Posts to Twitter/X via API or Discord via webhook
5. Tracks posted items in `state.json` (auto-generated, don't edit)
6. When all items have been posted, either loops back to the start or stops (your choice in config)

### State Tracking

`state.json` tracks what's been posted. You never need to edit it, but if you want to reset and start over:

```bash
rm state.json
sudo systemctl restart tweet-scheduler
```

---

## Troubleshooting

### "Missing environment variables"
Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
nano .env
```

### "Rate limited by Twitter"
The Free tier allows 1,500 tweets/month (~50/day). If you're posting more than that, reduce the frequency in `config.yaml`.

### "Discord webhook returned 4xx"
Your webhook URL might be invalid or the webhook was deleted. Create a new one in Discord and update `.env`.

### Bot isn't posting at the right times
Check the `timezone` setting in `config.yaml`. Times are in 24-hour format relative to your configured timezone.

### Want to start fresh
```bash
rm state.json
sudo systemctl restart tweet-scheduler
```

---

## File Overview

| File | Purpose |
|------|---------|
| `bot.py` | Main entry point — runs the scheduler |
| `twitter_poster.py` | Twitter/X posting logic |
| `discord_notifier.py` | Discord webhook logic |
| `csv_reader.py` | CSV reading + category rotation |
| `config.yaml` | Schedule and behavior settings |
| `tweets.csv` | Twitter content (edit this) |
| `reminders.csv` | Discord content (edit this) |
| `.env` | API keys (never commit this) |
| `state.json` | Post tracking (auto-generated) |
| `install.sh` | One-command VPS setup |

---

## Twitter API Free Tier Limits

- 1,500 tweets per month
- 1 app per project
- Post-only (no reading timelines)
- No media uploads via API on Free tier

At 3 tweets/day = ~90/month, well within limits.
