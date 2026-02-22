#!/usr/bin/env python3
"""Tweet Scheduler Bot — Posts to Twitter/X and Discord on a configurable schedule."""

import logging
import os
import signal
import sys
import time
from pathlib import Path

import schedule
import yaml
from dotenv import load_dotenv

from discord_notifier import DiscordNotifier
from twitter_poster import TwitterPoster

PROJECT_DIR = Path(__file__).parent
load_dotenv(PROJECT_DIR / ".env")

running = True


def shutdown(signum, frame):
    global running
    logging.info("Shutdown signal received. Stopping gracefully...")
    running = False


def setup_logging(level="INFO"):
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def load_config():
    config_path = PROJECT_DIR / "config.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def schedule_poster(poster, sched_config):
    """Schedule a poster's .post() method based on config."""
    times = sched_config.get("times")
    interval_hours = sched_config.get("interval_hours")

    if times:
        for t in times:
            schedule.every().day.at(t).do(poster.post)
            logging.info("Scheduled %s at %s daily.", poster.__class__.__name__, t)
    elif interval_hours:
        schedule.every(interval_hours).hours.do(poster.post)
        logging.info("Scheduled %s every %d hours.", poster.__class__.__name__, interval_hours)
    else:
        logging.warning("No schedule configured for %s. Skipping.", poster.__class__.__name__)


def validate_env(keys):
    """Check that required environment variables are set."""
    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        logging.error("Missing environment variables: %s", ", ".join(missing))
        logging.error("Copy .env.example to .env and fill in your keys.")
        sys.exit(1)


def main():
    config = load_config()
    setup_logging(config.get("general", {}).get("log_level", "INFO"))

    logger = logging.getLogger("bot")
    logger.info("Starting Tweet Scheduler Bot...")

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    twitter_enabled = config.get("twitter", {}).get("enabled", False)
    discord_enabled = config.get("discord", {}).get("enabled", False)

    if not twitter_enabled and not discord_enabled:
        logger.error("Both Twitter and Discord are disabled in config.yaml. Nothing to do.")
        sys.exit(1)

    if twitter_enabled:
        validate_env(["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET"])
        twitter_config = config["twitter"]
        poster = TwitterPoster(
            api_key=os.getenv("TWITTER_API_KEY"),
            api_secret=os.getenv("TWITTER_API_SECRET"),
            access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
            access_secret=os.getenv("TWITTER_ACCESS_SECRET"),
            behavior_on_empty=twitter_config.get("behavior_on_empty", "loop"),
        )
        schedule_poster(poster, twitter_config["schedule"])

    if discord_enabled:
        validate_env(["DISCORD_WEBHOOK_URL"])
        discord_config = config["discord"]
        notifier = DiscordNotifier(
            webhook_url=os.getenv("DISCORD_WEBHOOK_URL"),
            behavior_on_empty=discord_config.get("behavior_on_empty", "loop"),
        )
        schedule_poster(notifier, discord_config["schedule"])

    logger.info("Bot is running. Press Ctrl+C to stop.")

    # Run any jobs that are already due (e.g. if starting after a scheduled time)
    schedule.run_all(delay_seconds=1)

    while running:
        schedule.run_pending()
        time.sleep(30)

    logger.info("Bot stopped.")


if __name__ == "__main__":
    main()
