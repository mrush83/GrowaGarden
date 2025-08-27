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
    data = get_json("/alldata")
    weather_now = get_json("/weather")  # {"type":"...", "active":bool, "effects":[...], ...}

    # ---------- helpers ----------
    def qbadge(q):
        return f"`×{q}`" if isinstance(q, int) else ""

    def fmt_list(items, max_items=20):
        parts = []
        for it in items[:max_items]:
            name = it.get("name", "?")
            # Tasteful emphasis for rares
            if any(t in name for t in ("Mythical", "Legendary", "Elder")):
                name = f"__{name}__"
            parts.append(f"• **{name}** {qbadge(it.get('quantity'))}".strip())
        more = len(items) - max_items
        if more > 0:
            parts.append(f"*…and {more} more*")
        return "\n".join(parts) if parts else "_None_"

    def make_cat_embed(title, emoji, color, key):
        items = data.get(key, [])
        return {
            "title": f"{emoji} {title}",
            "description": fmt_list(items),
            "color": color,
            "footer": {"text": f"{len(items)} item(s)"},
        }

    # ---------- header embed (Weather only) ----------
    wtype = weather_now.get("type", "?")
    active = weather_now.get("active", False)
    effects = weather_now.get("effects") or []

    if active and effects:
        fx = ", ".join(effects)
        wx_desc = f"**Weather:** {wtype} (**active**) — _{fx}_"
    else:
        wx_desc = f"**Weather:** {wtype} (inactive)"

    header = {
        "title": "Grow a Garden — Stocks & Weather",
        "url": "https://www.game.guide/grow-a-garden-stock-tracker",
        "description": wx_desc,
        "color": 0x5865F2,  # blurple
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # ---------- category embeds (only the four you want) ----------
    embeds = [header]
    embeds.append(make_cat_embed("Seeds", "🌱", 0x22C55E, "seeds"))
    embeds.append(make_cat_embed("Gear", "🛠️", 0x3B82F6, "gear"))
    embeds.append(make_cat_embed("Eggs", "🥚", 0xF59E0B, "eggs"))
    embeds.append(make_cat_embed("Events", "🎪", 0x8B5CF6, "events"))

    # Guard against over-long descriptions
    for e in embeds:
        if e.get("description"):
            e["description"] = e["description"][:3800]

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
