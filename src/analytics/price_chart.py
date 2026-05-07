"""
Color coding helper for metric values in the Stock Details tab.
Mirrors the threshold rules in static/js/utils.js Utils.colorCodeMetric.
"""

_RULES = [
    (["p/e ratio", "forward p/e"], lambda v: v < 15, lambda v: v > 30),
    (["p/b ratio"], lambda v: v < 1.5, lambda v: v > 4),
    (["p/s ratio"], lambda v: v < 2, lambda v: v > 8),
    (["peg ratio"], lambda v: v < 1, lambda v: v > 2),
    (["ev/ebitda"], lambda v: v < 10, lambda v: v > 25),
    (["roe"], lambda v: v > 15, lambda v: v < 0),
    (["roa"], lambda v: v > 5, lambda v: v < 0),
    (["roic"], lambda v: v > 10, lambda v: v < 0),
    (["profit margin"], lambda v: v > 10, lambda v: v < 0),
    (["operating margin"], lambda v: v > 10, lambda v: v < 0),
    (["debt/equity", "debt to equity"], lambda v: v < 0.5, lambda v: v > 2),
    (["current ratio"], lambda v: v > 2, lambda v: v < 1),
]


def color_code_metric(key: str, value) -> str:
    """Return CSS class string for a metric value, or '' if no rule applies."""
    if value is None:
        return ""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return ""
    k = key.lower()
    for matches, is_green, is_red in _RULES:
        if any(m in k for m in matches):
            if is_green(v):
                return "metric-value-good"
            if is_red(v):
                return "metric-value-bad"
            return ""
    return ""
