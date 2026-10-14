#!/usr/bin/env python3
"""
Scrape daily contribution counts from GitHub's public contributions fragment
(https://github.com/users/<user>/contributions -- the same HTML the profile
page loads) and write data/contributions.json: the raw days plus derived stats
(total, active days, current/longest streak, best day, monthly totals).

No token, no GraphQL. Run daily by .github/workflows/update-profile-art.yml.

    python scripts/fetch_contributions.py
    GH_PROFILE_USER=someone python scripts/fetch_contributions.py
"""
import datetime
import json
import os
import re
import sys

USERNAME = os.environ.get("GH_PROFILE_USER", "Subhajit7710")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "contributions.json")


def fetch_days():
    import requests
    from bs4 import BeautifulSoup

    resp = requests.get(URL, headers={"User-Agent": f"{USERNAME}-profile-readme/1.0"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day[data-date]")
    if not cells:
        sys.exit("no calendar cells found -- GitHub's markup may have changed")

    # tooltips live in separate <tool-tip for="cell-id"> elements
    tips = {t.get("for"): t.get_text(" ", strip=True) for t in soup.find_all("tool-tip")}

    days = []
    for td in cells:
        text = tips.get(td.get("id"), "")
        m = re.match(r"(\d[\d,]*)\s+contribution", text)
        count = int(m.group(1).replace(",", "")) if m else 0
        days.append({"date": td["data-date"], "count": count, "level": int(td.get("data-level") or 0)})
    days.sort(key=lambda d: d["date"])
    return days


def streaks(days):
    # current: walk back from the end; an empty *today* doesn't break it yet
    i = len(days) - 1
    if i >= 0 and days[i]["count"] == 0:
        i -= 1
    end = i
    while i >= 0 and days[i]["count"] > 0:
        i -= 1
    cur_len = end - i
    current = {"length": cur_len,
               "start": days[i + 1]["date"] if cur_len else None,
               "end": days[end]["date"] if cur_len else None}

    best = {"length": 0, "start": None, "end": None}
    run_start = None
    for j, d in enumerate(days):
        if d["count"] > 0:
            run_start = j if run_start is None else run_start
            if j - run_start + 1 > best["length"]:
                best = {"length": j - run_start + 1, "start": days[run_start]["date"], "end": d["date"]}
        else:
            run_start = None
    return current, best


def build_data(days, username=USERNAME):
    total = sum(d["count"] for d in days)
    active = sum(1 for d in days if d["count"] > 0)
    best_day = max(days, key=lambda d: d["count"])
    current, longest = streaks(days)
    monthly = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]
    return {
        "username": username,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total_contributions": total,
        "active_days": active,
        "avg_per_active_day": round(total / active, 1) if active else 0,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best_day["date"], "count": best_day["count"]},
        "monthly": [{"month": k, "total": v} for k, v in sorted(monthly.items())],
        "days": days,
    }


if __name__ == "__main__":
    data = build_data(fetch_days())
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"wrote {os.path.normpath(OUT_PATH)}: {data['total_contributions']} contributions, "
          f"current streak {data['current_streak']['length']}, longest {data['longest_streak']['length']}")
