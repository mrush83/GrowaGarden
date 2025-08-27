def main():
    data = get_json("/alldata")
    weather_now = get_json("/weather")

    # ---------- helpers ----------
    def qbadge(q):
        return f"`×{q}`" if isinstance(q, int) else ""

    def fmt_list(items, max_items=20):
        # “Name ×Q” bullets, trimmed to keep embeds small
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
    embeds.append(make_cat_embed("Cosmetics", "🧱", 0xEC4899, "cosmetics"))
    embeds.append(make_cat_embed("Honey / Crates", "🍯", 0xD97706, "honey"))
    embeds.append(make_cat_embed("Events", "🎪", 0x8B5CF6, "events"))

    # Discord limits: ≤10 embeds, ≤6000 chars total; trim if needed
    # (Quick guard: if description is huge, slice it)
    for e in embeds:
        if "description" in e and e["description"]:
            e["description"] = e["description"][:3800]

    requests.post(WEBHOOK_URL, json={"embeds": embeds}, timeout=TIMEOUT).raise_for_status()
