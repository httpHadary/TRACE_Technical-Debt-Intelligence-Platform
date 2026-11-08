"""Shared helpers (effort parsing) so every script reads Sonar effort the same way."""
import re
from contracts import number

MINUTES_PER_HOUR = 60
MINUTES_PER_DAY = 8 * 60  # SonarQube's default: 1 working day = 8 hours

_D = re.compile(r"(\d+(?:\.\d+)?)\s*d", re.I)
_H = re.compile(r"(\d+(?:\.\d+)?)\s*h", re.I)
_M = re.compile(r"(\d+(?:\.\d+)?)\s*m", re.I)


def parse_minutes(effort):
    """Sonar effort -> minutes. Handles 5, '5min', '1h30min', '2d', '1d2h30min'.
    (The old per-script parsers ignored 'd' and let the digits leak into the next unit.)"""
    if not isinstance(effort, str) or not effort.strip():
        return number(effort)
    s = effort.strip()
    if re.fullmatch(r'\d+(?:\.\d+)?', s):
        return number(s)
    match = re.fullmatch(r'(?:(\d+(?:\.\d+)?)\s*d\s*)?(?:(\d+(?:\.\d+)?)\s*h\s*)?(?:(\d+(?:\.\d+)?)\s*(?:min|m))?', s, re.I)
    if not match or not any(match.groups()):
        raise ValueError(f'Malformed effort: {effort!r}')
    return sum(number(v) * scale for v, scale in zip(match.groups(), (480, 60, 1)) if v is not None)


def assert_contiguous_weeks(labels):
    """labels like ['week_01', 'week_02', ...]. Rolling windows are index-based, so a gap
    (e.g. 1, 14, 18) silently turns a '3-week' window into a 17-week one. Fail loudly."""
    nums = sorted(int(str(l).rsplit("_", 1)[-1]) for l in labels)
    if not nums:
        return nums
    missing = sorted(set(range(nums[0], nums[-1] + 1)) - set(nums))
    if missing:
        shown = ", ".join(str(m) for m in missing[:15]) + (" ..." if len(missing) > 15 else "")
        raise SystemExit(
            f"!!! Weekly snapshots are not contiguous: missing week(s) {shown}. "
            "Re-run scan_weekly_snapshots.py (it now fills duplicate-commit weeks).")
    return nums


def week_number(label):
    """'week_07' -> 7, 'week_123' -> 123."""
    return int(str(label).rsplit("_", 1)[-1])


def sorted_week_labels(labels):
    """
    Labels in CALENDAR order. Never use plain sorted() on 'week_NN' strings: once a run has
    100+ weeks, 'week_100' sorts before 'week_11', which silently scrambles every index-based
    rolling window (slopes, volatility, finding arrivals/closures). Also fails loudly on gaps.
    """
    labels = sorted(set(labels), key=week_number)
    assert_contiguous_weeks(labels)
    return labels
