from decimal import Decimal

def _fmt_conf(val):
    if isinstance(val, Decimal):
        return f"{float(val):.2f}"
    if isinstance(val, (int, float)):
        return f"{val:.2f}"
    return str(val)

def _format_xray_items(items: list[dict]) -> str:
    if not items:
        return "No X-ray AI results found for this encounter."
    lines = []
    for i, item in enumerate(items, 1):
        ts   = item.get("timestamp", "unknown time")
        pred = item.get("prediction", "unknown")
        conf = _fmt_conf(item.get("confidence", "n/a"))
        lines.append(f"[XRay #{i} @ {ts}] impression: {pred} ({conf})")
    return "\n".join(lines)