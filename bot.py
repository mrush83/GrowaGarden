import os, requests
from datetime import datetime, timezone

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
API_BASE = os.environ.get("GAG_API_BASE", "https://gagapi.onrender.com")
TIMEOUT = 12

def get_json(path: str):
    r = requests.get(f"{API_BASE}{path}", timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def main():
    data = get_json("/alldata")     # single call returns everything
    weather_now = get_json("/weather")  # tiny call for quick status

    # Buckets we’ll summarize (add/remove to taste)
    buckets = ("seeds", "gear", "eggs", "cosmetics", "honey", "events")
    counts = {b: len(data.get(b, [])) for b in buckets}

    # Build a few sample names per bucket so the embed is readable
    def sample(key, n=5):
        items = data.get(key, [])[:n]
        # items are dicts like {"name":"Carrot","quantity":24}
        parts = []
        for it in items:
            q = it.get("quantity")
            nm = it.get("name", "?")
            parts.append(f"{nm}" + (f" x{q}" if isinstance(q, int) else ""))
        return ", ".join(parts) + ("…" if len(data.get(key, [])) > n else "")

    lines = []
    for b in buckets:
        if counts[b]:
            lines.append(f"**{b.title()}**: {sample(b)}")

    # Weather
    wtype = weather_now.get("type", "?")
    wactive = "active" if weather_now.get("active") else "inactive"
    wx_line = f"**Weather:** {wtype} ({wactive})"

    # Traveling Merchant (if present)
    tm = data.get("travelingMerchant") or {}
    tm_line = None
    if tm.get("items"):
        items = ", ".join(f"{i['name']} x{i.get('quantity',1)}" for i in tm["items"])
        tm_line = f"**{tm.get('merchantName','Traveling Merchant')}**: {items}"

    # Compose description
    desc_parts = [wx_line, ""]
    if tm_line:
        desc_parts.extend([tm_line, ""])
    desc_parts.extend(lines)
    description = "\n".join(desc_parts)[:3800]

    # Embed fields (counts)
    fields = [{"name": b.title(), "value": str(counts[b]), "inline": True} for b in buckets]

    embed = {
        "title": "Grow a Garden — Stocks & Weather",
        "url": "https://www.game.guide/grow-a-garden-stock-tracker",
        "description": description,
        "fields": fields,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    requests.post(WEBHOOK_URL, json={"embeds":[embed]}, timeout=TIMEOUT).raise_for_status()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        try:
            requests.post(
                os.environ["DISCORD_WEBHOOK"],
                json={"content": f"Grow-a-Garden bot error: `{e}`"},
                timeout=TIMEOUT,
            )
        except Exception:
            pass
        raise
