import os, requests
from datetime import datetime, timezone

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
API_BASE = os.environ.get("GAG_API_BASE", "https://gagapi.onrender.com")
TIMEOUT = 12
HEADERS = {"Cache-Control": "no-cache", "Pragma": "no-cache"}  # avoid cached JSON

# ---------- HTTP ----------
def get_json(path: str):
    r = requests.get(f"{API_BASE}{path}", timeout=TIMEOUT, headers=HEADERS)
    r.raise_for_status()
    return r.json()

# ---------- Formatting ----------
def qbadge(q):  # quantity “pill”
    return f"`×{q}`" if isinstance(q, int) else ""

def list_lines(items, max_items=10):
    lines = []
    for it in items[:max_items]:
        name = it.get("name", "?")
        if any(t in name for t in ("Mythical", "Legendary", "Elder")):
            name = f"__{name}__"
        lines.append(f"• **{name}** {qbadge(it.get('quantity'))}".strip())
    more = len(items) - max_items
    if more > 0:
        lines.append(f"*…and {more} more*")
    return lines or ["_None_"]

def field_block(title, emoji, items):
    # Field name shows section + count; value is a bullet list
    name = f"{emoji} {title} · {len(items)}"
    value = "\n".join(list_lines(items))[:1024]  # Discord field value limit
    return {"name": name, "value": value, "inline": True}

def spacer():  # invisible spacer to complete a row of 3 inline fields
    return {"name": "\u200b", "value": "\u200b", "inline": True}

# ---------- Main ----------
def main():
    data = get_json("/alldata")  # seeds, gear, eggs, events

    seeds  = data.get("seeds", [])
    eggs   = data.get("eggs", [])
    gear   = data.get("gear", [])
    events = data.get("events", [])

    # Build a single embed with inline fields in a 2×2 grid
    embed = {
        "title": "Grow a Garden — Stocks",
        "url": "https://www.game.guide/grow-a-garden-stock-tracker",
        "color": 0x5865F2,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fields": [
            field_block("Seeds",  "🌱", seeds),
            field_block("Eggs",   "🥚", eggs),
            spacer(),  # completes row 1 (Discord shows up to 3 inline fields per row)
            field_block("Gear",   "🛠️", gear),
            field_block("Events", "🎪", events),
            spacer(),  # completes row 2
        ],
        "footer": {"text": datetime.now(timezone.utc).strftime("%H:%M UTC")}
    }

    requests.post(WEBHOOK_URL, json={"embeds": [embed]}, timeout=TIMEOUT).raise_for_status()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        try:
            requests.post(WEBHOOK_URL, json={"content": f"Grow-a-Garden bot error: `{e}`"}, timeout=TIMEOUT)
        except Exception:
            pass
        raise
