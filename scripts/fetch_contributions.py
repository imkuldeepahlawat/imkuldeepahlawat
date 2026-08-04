#!/usr/bin/env python3
"""Scrape real daily contribution counts from GitHub's public, unauthenticated
contributions endpoint (the same fragment github.com's own profile page uses)
and write data/contributions.json with the raw days plus a couple of derived
stats. No token, no GraphQL -- just the public HTML GitHub already serves.

Usage:
    python scripts/fetch_contributions.py [--user imkuldeepahlawat]
                                           [--out data/contributions.json]
"""

import argparse
import datetime
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup


def fetch_days(username):
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(url, headers={"User-Agent": "profile-readme-bot/1.0"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        print("no calendar cells found -- github markup may have changed", file=sys.stderr)
        sys.exit(1)

    days = []
    for td in cells:
        date = td.get("data-date")
        if not date:
            continue
        tooltip = soup.find("tool-tip", attrs={"for": td.get("id")})
        text = tooltip.get_text(strip=True) if tooltip else ""
        if re.search(r"no contributions", text, re.I):
            count = 0
        else:
            m = re.match(r"(\d+)", text)
            count = int(m.group(1)) if m else 0
        days.append({"date": date, "count": count})

    days.sort(key=lambda d: d["date"])
    return days


def compute_current_streak(days):
    idx = len(days) - 1
    if days[idx]["count"] == 0:
        idx -= 1  # today may not be over yet -- don't break the streak on it
    streak = 0
    while idx >= 0 and days[idx]["count"] > 0:
        streak += 1
        idx -= 1
    return streak


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user", default="imkuldeepahlawat")
    parser.add_argument("--out", default="data/contributions.json")
    args = parser.parse_args()

    days = fetch_days(args.user)
    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"])
    data = {
        "username": args.user,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total_contributions": total,
        "current_streak": compute_current_streak(days),
        "best_day": {"date": best["date"], "count": best["count"]},
        "days": days,
    }

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(data, f, indent=2)
    print(f"wrote {args.out}: {total} contributions, current streak {data['current_streak']}", file=sys.stderr)


if __name__ == "__main__":
    main()
