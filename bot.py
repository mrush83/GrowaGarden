import os
import requests
from datetime import datetime, timezone

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
API_BASE = os.environ.get("GAG_API_BASE", "https://gagapi.onrender.com")
TIMEOUT = 12
HEADERS = {"Cache-Control": "no-cache", "Pragma": "no-cache"}  # avoid CDN caching

# -------------------- HTTP helpers --------------------

def get_json(path: str):
    r = requests.get(f"{API_BASE}{path}", timeout=TIMEOUT, headers=HEADERS)
    r.raise_for_status()
    return r.json()

def _parse_iso(ts: str | None):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None

def _pretty_weather_name(wtype: str | None) -> str:
    return (wtype or "").replace("_", " ").strip().title() or "None"

def pick_live_weather(data: dict, weather_now: dict) -> dict:
    """
    Choose the most accurate current weather:
      1) Prefer an active/ongoing entry from alldata.weatherHistory.
      2) Else pick the newest of alldata.weather vs /weather by lastUpdated.
    Returns a dict with {type, active, effects, lastUpdated}.
    """
    now = datetime.now(timezone.utc)
    candidates: list[tuple[str, dict, datetime | None]] = []

    # /weather endpoint
    if isinstance(weather_now, dict):
        candidates.append(("endpoint", weather_now, _parse_iso(weather_now.get("lastUpdated"))))

    # alldata.weather
    w = data.get("weather") or {}
    candidates.append(("alldata.weather", w, _parse_iso(w.get("lastUpdated"))))

    # alldata.weatherHistory (prefer ongoing entries)
    for h in (data.get("weatherHistory") or []):
        st = _parse_iso(h.get("startTime"))
        en = _parse_iso(h.get("endTime"))
        ongoing = bool(h.get("active")) or (en and en > now) or (st and not en and (now - st).total_seconds() < 3600)
        if ongoing:
            # history usually lacks 'effects'; we still mark it active
            candidates.append(("history", {
                "type": h.get("type"),
                "active": True,
                "effects": h.get("effects", []),
                "lastUpdated": (en or st or now).isoformat()
            }, st or en or now))

    # Prefer any active, non-normal candidate by recency
    active = [c for c in candidates
              if c[1].get("active") and (c[1].get("type") or "").lower() not in ("normal", "none", "")]
    if active:
        active.sort(key=lambda c: (c[2] is not None, c[2]), reverse=True)
        return active[0][1]

    # Else pick newest overall
    candidates.sort(key=lambda c: (c[2] is not None, c[2]), reverse=True)
    return candidates[0][1] if candidates else {"type": "none", "active": False, "effects": [], "lastUpdated": None}

# -------------------- Formatting helpers --------------------

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

def make_cat_embed(title, emoji, color, key, data):
    items = data.get(key, [])
    return {
        "title": f"{emoji} {title}",
        "description": fmt_list(items),
        "color": color,
        "footer": {"text": f"{len(items)} item(s)"},
    }

# -------------------- Main --------------------

def main():
    data = get_json("/alldata")
    weather_now = get_json("/weather")

    # Weather header (accurate selection)
    w = pick_live_weather(data, weather_now)
    wname = _pretty_weather_name(w.get("type"))
    is_active = bool(w.get("active")) and wname.lower() not in ("normal", "none", "")
    effects = w.get("effects") or []

    if is_active and effects:
        wx_desc = f"**Weather:** {wname} (**active**) — _{', '.join(effects)}_"
    elif is_active:
        wx_desc = f"**Weather:** {wname} (**active**)"
    else:
        wx_desc = "**Weather:** none"

    header = {
        "title": "Grow a Garden — Stocks & Weather",
        "url": "https://www.game.guide/grow-a-garden-stock-tracker",
        "description": wx_desc,
        "color": 0x5865F2,  # blurple
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Category embeds: Seeds, Gear, Eggs, Events
    embeds = [header]
    embeds.append(make_cat_embed("Seeds", "🌱", 0x22C55E, "seeds", data))
    embeds.append(make_cat_embed("Gear", "🛠️", 0x3B82F6, "gear", data))
    embeds.append(make_cat_embed("Eggs", "🥚", 0xF59E0B, "eggs", data))
    embeds.append(make_cat_embed("Events", "🎪", 0x8B5CF6, "events", data))

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
