import os, requests
from datetime import datetime, timezone

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
API_BASE = os.environ.get("GAG_API_BASE", "https://gagapi.onrender.com")
TIMEOUT = 12
HEADERS = {"Cache-Control": "no-cache", "Pragma": "no-cache"}

def get_json(path: str):
    r = requests.get(f"{API_BASE}{path}", timeout=TIMEOUT, headers=HEADERS)
    r.raise_for_status()
    return r.json()

def qbadge(q): return f"`×{q}`" if isinstance(q, int) else ""

def fmt_list(items, max_items=20):
    parts = []
    for it in items[:max_items]:
        name = it.get("name", "?")
        if any(t in name for t in ("Mythical", "Legendary", "Elder")):
            name = f"__{name}__"
        parts.append(f"• **{name}** {qbadge(it.get('quantity'))}".strip())
    more = len(items) - max_items
    if more > 0: parts.append(f"*…and {more} more*")
    return "\n".join(parts) if parts else "_None_"

def make_cat_embed(title, emoji, color, key, data):
    items = data.get(key, [])
    return {
        "title": f"{emoji} {title}",
        "description": fmt_list(items),
        "color": color,
        "footer": {"text": f"{len(items)} item(s) • {datetime.now(timezone.utc).strftime('%H:%M UTC')}"}
    }

def main():
    data = get_json("/alldata")
    embeds = [
        make_cat_embed("Seeds",  "🌱", 0x22C55E, "seeds",  data),
        make_cat_embed("Gear",   "🛠️", 0x3B82F6, "gear",   data),
        make_cat_embed("Eggs",   "🥚", 0xF59E0B, "eggs",   data),
        make_cat_embed("Events", "🎪", 0x8B5CF6, "events", data),
    ]
    for e in embeds:
        if e.get("description"): e["description"] = e["description"][:3800]
    requests.post(WEBHOOK_URL, json={"embeds": embeds}, timeout=TIMEOUT).raise_for_status()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        try:
            requests.post(WEBHOOK_URL, json={"content": f"Grow-a-Garden bot error: `{e}`"}, timeout=TIMEOUT)
        except Exception:
            pass
        raise
