# Runs once per invocation (GitHub Actions will invoke it every 5 minutes)
# Fetches Grow-a-Garden stocks + weather and posts a tidy embed to a Discord webhook.

import os
import requests
from datetime import datetime, timezone

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]  # set in GitHub → Settings → Secrets → Actions
API_BASE = os.environ.get("GAG_API_BASE", "https://gagapi.onrender.com")  # override if needed
TIMEOUT = 12  # seconds

def get_json(path: str):
    r = requests.get(f"{API_BASE}{path}", timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def main():
    stocks = get_json("/api/stocks")       # expected keys: seeds, gear, eggs, cosmetics, event
    weather = get_json("/api/weather")     # expected keys: condition, region, (maybe) expires_at

    # Count buckets (defaults to 0 if missing)
    buckets = ("seeds", "gear", "eggs", "cosmetics", "event")
    counts = {b: len(stocks.get(b, [])) for b in buckets}

    # Show a few item names (trim to keep the embed short)
    def sample_names(key, n=5):
        items = stocks.get(key, [])[:n]
        names = [i.get("name", "?") for i in items]
        return ", ".join(names) + ("…" if len(stocks.get(key, [])) > n else "")

    lines = []
    for b in buckets:
        if counts[b]:
            lines.append(f"**{b.title()}**: {sample_names(b)}")

    desc_lines = [
        f"**Weather:** {weather.get('condition','?')}  •  **Region:** {weather.get('region','?')}",
        "",
        *lines
    ]
    description = "\n".join(desc_lines)[:3800]  # embed description max ~4096

    embed = {
        "title": "Grow a Garden — Stocks & Weather",
        "url": "https://www.game.guide/grow-a-garden-stock-tracker",
        "description": description,
        "fields": [
            {"name": "Seeds", "value": str(counts["seeds"]), "inline": True},
            {"name": "Gear", "value": str(counts["gear"]), "inline": True},
            {"name": "Eggs", "value": str(counts["eggs"]), "inline": True},
            {"name": "Cosmetics", "value": str(counts["cosmetics"]), "inline": True},
            {"name": "Event", "value": str(counts["event"]), "inline": True},
        ],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    payload = {"embeds": [embed]}
    resp = requests.post(WEBHOOK_URL, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # If something blows up, try to report it to Discord (best-effort).
        try:
            requests.post(
                os.environ["DISCORD_WEBHOOK"],
                json={"content": f"Grow-a-Garden bot error: `{e}`"},
                timeout=TIMEOUT,
            )
        except Exception:
            pass
        raise

