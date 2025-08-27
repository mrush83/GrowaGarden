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
    # Pull once for all data, plus quick weather status
    data = get_json("/alldata")
    weather_now = get_json("/weather")

    # ---------- helpers ----------
    def qbadge(q):
        return f"`×{q}`" if isinstance(q, int) else ""

    def fmt_list(items, max_items=20):
        # “• Name ×Q” bullets; trimmed to keep embeds small
        parts = [f"• **{it.get('name','?')}** {qbadge(it.get('quantity'))}".strip()
                 for it in items[:max_items]]
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

    # ---------- header embed ----------
    wtype = weather_now.get("type", "?")
    wactive = "active" if weather_now.get("active") else "inactive"
    wx_line = f"**Weather:** {wtype} ({wactive})"

    tm = data.get("travelingMerchant") or {}
    tm_line = ""
    if tm.get("items"):
        items = ", ".join(f"{i['name']} {qbadge(i.get('quantity',1))}" for i in tm["items"])
        tm_line = f"**{tm.get('merchantName','Traveling Merchant')}**: {items}"

    header = {
        "title": "Grow a Garden — Stocks & Weather",
        "url": "https://www.game.guide/grow-a-garden-stock-tracker",
        "description": "\n\n".join(x for x in [wx_line, tm_line] if x),
        "color": 0x5865F2,  # blurple
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # ---------- category embeds ----------
    embeds = [header]
    embeds.append(make_cat_embed("Seeds", "🌱", 0x22C55E, "seeds"))
    embeds.append(make_cat_embed("Gear", "🛠️", 0x3B82F6, "gear"))
    embeds.append(make_cat_embed("Eggs", "🥚", 0xF59E0B, "eggs"))
    embeds.append(make_cat_embed("Cosmetics", "🎨", 0xEC4899, "cosmetics"))
    embeds.append(make_cat_embed("Honey / Crates", "🍯", 0xD97706, "honey"))
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
        # Best-effort error ping to Discord, then re-raise for Actions logs
        try:
            requests.post(WEBHOOK_URL, json={"content": f"Grow-a-Garden bot error: `{e}`"}, timeout=TIMEOUT)
        except Exception:
            pass
        raise
