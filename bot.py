import os, requests
from datetime import datetime, timezone

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
API_BASE = os.environ.get("GAG_API_BASE", "https://gagapi.onrender.com")
TIMEOUT = 12
HEADERS = {"Cache-Control": "no-cache", "Pragma": "no-cache"}  # avoid any CDN caching

def get_json(path: str):
    r = requests.get(f"{API_BASE}{path}", timeout=TIMEOUT, headers=HEADERS)
    r.raise_for_status()
    return r.json()

def parse_iso(ts):
    if not ts:
        return None
    try:
        # "2025-08-27T06:19:01.802Z" -> aware datetime
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None

def pick_fresh_weather(w_from_alldata, w_from_endpoint):
    candidates = []
    for src, w in (("alldata", w_from_alldata), ("endpoint", w_from_endpoint)):
        if isinstance(w, dict):
            candidates.append((parse_iso(w.get("lastUpdated")), src, w))
    if not candidates:
        return {}
    # pick the newest by timestamp (None sorts oldest)
    candidates.sort(key=lambda t: (t[0] is not None, t[0]), reverse=True)
    return candidates[0][2]

def main():
    data = get_json("/alldata")
    weather_now = get_json("/weather")

    # ---------- WEATHER ----------
    w = pick_fresh_weather(data.get("weather"), weather_now)
    wtype = (w.get("type") or "").lower()
    active_flag = bool(w.get("active", False)) and wtype not in ("normal", "none", "")
    effects = w.get("effects") or []

    if active_flag and effects:
        wx_desc = f"**Weather:** {wtype} (**active**) — _{', '.join(effects)}_"
    elif active_flag:
        wx_desc = f"**Weather:** {wtype} (**active**)"
    else:
        wx_desc = "**Weather:** none"

    header = {
        "title": "Grow a Garden — Stocks & Weather",
        "url": "https://www.game.guide/grow-a-garden-stock-tracker",
        "description": wx_desc,
        "color": 0x5865F2,  # blurple
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # ---------- helpers ----------
    def qbadge(q):
        return f"`×{q}`" if isinstance(q, int) else ""

    def fmt_list(items, max_items=20):
        parts = []
        for it in items[:max_items]:
            name = it.get("name", "?")
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

    # ---------- category embeds (only the four you want) ----------
    embeds = [header]
    embeds.append(make_cat_embed("Seeds", "🌱", 0x22C55E, "seeds"))
    embeds.append(make_cat_embed("Gear", "🛠️", 0x3B82F6, "gear"))
    embeds.append(make_cat_embed("Eggs", "🥚", 0xF59E0B, "eggs"))
    embeds.append(make_cat_embed("Events", "🎪", 0x8B5CF6, "events"))

    # Guard against long text
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
