import logging
from datetime import datetime, timezone
from pathlib import Path

import requests

from csv_reader import get_next_post, load_state, mark_posted, save_state

logger = logging.getLogger(__name__)

REMINDERS_CSV = Path(__file__).parent / "reminders.csv"

CATEGORY_COLORS = {
    "goal": 0x2ECC71,      # green
    "plan": 0x3498DB,      # blue
    "campaign": 0xE74C3C,  # red
}


class DiscordNotifier:
    def __init__(self, webhook_url, behavior_on_empty="loop"):
        self.webhook_url = webhook_url
        self.behavior_on_empty = behavior_on_empty

    def post(self):
        state = load_state()
        post = get_next_post(REMINDERS_CSV, "discord", state, self.behavior_on_empty)

        if post is None:
            logger.info("No Discord reminder to post.")
            return

        embed = {
            "title": post["category"].upper(),
            "description": post["text"],
            "color": CATEGORY_COLORS.get(post["category"], 0x95A5A6),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {"text": "Tweet Scheduler Bot"},
        }

        payload = {"embeds": [embed]}

        try:
            resp = requests.post(self.webhook_url, json=payload, timeout=10)
            if resp.status_code == 204:
                logger.info("Discord reminder posted successfully.")
                mark_posted("discord", state, post["index"], post["category"])
            else:
                logger.error("Discord webhook returned %d: %s", resp.status_code, resp.text)
                save_state(state)
        except requests.Timeout:
            logger.warning("Discord webhook timed out. Will retry next cycle.")
            save_state(state)
        except Exception as e:
            logger.error("Failed to post Discord reminder: %s", e)
            save_state(state)
