import csv
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

STATE_FILE = Path(__file__).parent / "state.json"


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {
        "twitter": {"last_index": -1, "last_category": None, "history": []},
        "discord": {"last_index": -1, "last_category": None, "history": []},
    }


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def read_csv(filepath):
    rows = []
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            rows.append({"index": i, "text": row["text"].strip(), "category": row["category"].strip().lower()})
    return rows


def get_next_post(csv_path, source_key, state, behavior_on_empty="loop"):
    """Pick the next unposted item using category rotation.

    Args:
        csv_path: Path to the CSV file.
        source_key: "twitter" or "discord" — used to track state separately.
        state: The full state dict (mutated in place, caller saves).
        behavior_on_empty: "loop" to restart from beginning, "stop" to return None.

    Returns:
        A dict with index, text, category — or None if nothing to post.
    """
    rows = read_csv(csv_path)
    if not rows:
        logger.warning("CSV file is empty: %s", csv_path)
        return None

    source_state = state[source_key]
    last_index = source_state["last_index"]
    last_category = source_state["last_category"]
    posted_indices = {entry["index"] for entry in source_state.get("history", [])}

    unposted = [r for r in rows if r["index"] not in posted_indices]

    if not unposted:
        if behavior_on_empty == "stop":
            logger.info("All items posted for %s. Behavior is 'stop'.", source_key)
            return None
        logger.info("All items posted for %s. Looping back to start.", source_key)
        source_state["history"] = []
        source_state["last_index"] = -1
        source_state["last_category"] = None
        posted_indices = set()
        unposted = list(rows)
        last_category = None

    # Category rotation: prefer a different category than last posted
    if last_category:
        different_category = [r for r in unposted if r["category"] != last_category]
        if different_category:
            unposted = different_category

    # Pick the first available (maintains CSV order within the filtered set)
    chosen = unposted[0]
    logger.info("Selected %s post [%d]: category=%s", source_key, chosen["index"], chosen["category"])
    return chosen


def mark_posted(source_key, state, index, category, extra=None):
    """Record a post as completed in state."""
    from datetime import datetime, timezone

    entry = {
        "index": index,
        "posted_at": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        entry.update(extra)

    source_state = state[source_key]
    source_state["last_index"] = index
    source_state["last_category"] = category
    source_state.setdefault("history", []).append(entry)

    # Keep history manageable — last 500 entries
    if len(source_state["history"]) > 500:
        source_state["history"] = source_state["history"][-500:]

    save_state(state)
    logger.info("Marked %s post [%d] as posted.", source_key, index)
