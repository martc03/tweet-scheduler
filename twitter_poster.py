import logging
from pathlib import Path

import tweepy

from csv_reader import get_next_post, load_state, mark_posted, save_state

logger = logging.getLogger(__name__)

TWEETS_CSV = Path(__file__).parent / "tweets.csv"


class TwitterPoster:
    def __init__(self, api_key, api_secret, access_token, access_secret, behavior_on_empty="loop"):
        self.behavior_on_empty = behavior_on_empty
        try:
            self.client = tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_secret,
            )
            logger.info("Twitter client initialized successfully.")
        except Exception as e:
            logger.error("Failed to initialize Twitter client: %s", e)
            raise

    def post(self):
        state = load_state()
        post = get_next_post(TWEETS_CSV, "twitter", state, self.behavior_on_empty)

        if post is None:
            logger.info("No tweet to post.")
            return

        text = post["text"]
        if len(text) > 280:
            logger.warning("Tweet text exceeds 280 chars (%d). Truncating.", len(text))
            text = text[:277] + "..."

        try:
            response = self.client.create_tweet(text=text)
            tweet_id = response.data["id"]
            logger.info("Tweet posted successfully. ID: %s", tweet_id)
            mark_posted("twitter", state, post["index"], post["category"], extra={"tweet_id": tweet_id})
        except tweepy.TooManyRequests:
            logger.warning("Rate limited by Twitter. Will retry next cycle.")
            save_state(state)
        except tweepy.TwitterServerError as e:
            logger.error("Twitter server error: %s. Will retry next cycle.", e)
            save_state(state)
        except Exception as e:
            logger.error("Failed to post tweet: %s", e)
            save_state(state)
