#!/usr/bin/env python3
"""Generate profile SVGs; fetch and validate all data before replacing any card."""
import hashlib
import json
import os
import re
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from html import escape
from html.parser import HTMLParser
from pathlib import Path

USER = os.environ.get("PROFILE_USER", "zie225")
ROOT = Path(__file__).resolve().parent.parent
PROFILE_DIR = ROOT / "profile"


def fetch(url, authenticated=False):
    headers = {"User-Agent": "GitHub-Profile-Generator", "Accept": "application/vnd.github+json" if authenticated else "text/html", "Accept-Language": "en-US"}
    token = os.environ.get("GITHUB_TOKEN")
    if authenticated and token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
        return response.read().decode("utf-8")


def api(path):
    return json.loads(fetch("https://api.github.com" + path, authenticated=True))


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.counts = {}
        self.target = None
        self.parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("data-date") and attrs.get("id"):
            self.cells[attrs["id"]] = date.fromisoformat(attrs["data-date"])
        if tag == "tool-tip":
            self.target = attrs.get("for")
            self.parts = []

    def handle_data(self, data):
        if self.target:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self.target:
            match = re.match(r"(No|[0-9,]+) contributions? on ", "".join(self.parts).strip())
            if match:
                self.counts[self.target] = 0 if match[1] == "No" else int(match[1].replace(",", ""))
            self.target = None

    def days(self):
        if not self.cells or self.cells.keys() - self.counts.keys():
            raise ValueError("Incomplete contribution calendar; keeping previous cards")
        days = sorted((day, self.counts[key]) for key, day in self.cells.items())
        if len(days) < 365 or any(b[0] - a[0] != timedelta(days=1) for a, b in zip(days, days[1:])):
            raise ValueError("Invalid contribution calendar; keeping previous cards")
        return days


def streaks(days):
    longest = run = 0
    for _, count in days:
        run = run + 1 if count else 0
        longest = max(longest, run)
    # An empty final day does not break yesterday's active streak.
    current = 0
    for _, count in reversed(days[:-1] if days[-1][1] == 0 else days):
        if not count:
            break
        current += 1
    return current, longest


def text(x, y, value, size=16, color="#e6edf3"):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-family="Arial, sans-serif">{escape(str(value))}</text>'


def card(title, subtitle, body, height=310):
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="820" height="{height}" viewBox="0 0 820 {height}" role="img" aria-label="{escape(title)}">',
        '<rect width="100%" height="100%" rx="16" fill="#0d1117"/>',
        text(32, 44, title, 28), text(32, 74, subtitle, 14, "#8b949e"),
        *body, text(32, height - 18, "Updated " + updated, 12, "#8b949e"), '</svg>',
    ])


def update_image_urls(readme, profile_dir):
    content = readme.read_text(encoding="utf-8")
    for name in ("stats", "top-langs", "streak"):
        version = hashlib.sha256((profile_dir / f"{name}.svg").read_bytes()).hexdigest()[:16]
        url = f"https://raw.githubusercontent.com/zie225/Zie225/master/profile/{name}.svg?v={version}"
        content = re.sub(
            rf'src="(?:\./profile/|https://raw\.githubusercontent\.com/zie225/Zie225/master/profile/){name}\.svg(?:\?[^\"]*)?"',
            f'src="{url}"', content,
        )
    readme.write_text(content, encoding="utf-8")


def generate():
    user = api(f"/users/{USER}")
    repos = []
    page = 1
    while True:
        batch = api(f"/users/{USER}/repos?per_page=100&page={page}")
        if not isinstance(batch, list):
            raise ValueError("Invalid repository response")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    parser = CalendarParser()
    parser.feed(fetch(f"https://github.com/users/{USER}/contributions"))
    days = parser.days()
    if abs((datetime.now(timezone.utc).date() - days[-1][0]).days) > 1:
        raise ValueError("Stale contribution calendar; keeping previous cards")
    current, longest = streaks(days)
    stats = [("Public repos", user["public_repos"]), ("Stars received", sum(r["stargazers_count"] for r in repos)),
             ("Followers", user["followers"]), ("Following", user["following"]),
             ("Forks received", sum(r["forks_count"] for r in repos)), ("Contributions (12 mo)", sum(n for _, n in days))]
    body = []
    for i, (label, value) in enumerate(stats):
        x, y = 32 + (i % 3) * 260, 114 + (i // 3) * 88
        body.extend([text(x, y, label, 15, "#8b949e"), text(x, y + 36, f"{value:,}", 30, "#79c0ff")])
    stats_svg = card("GitHub Stats", f"@{USER} | Public GitHub activity", body)

    languages = Counter(r["language"] for r in repos if not r["fork"] and r["language"])
    total = sum(languages.values())
    body = []
    colors = ["#3572A5", "#f1e05a", "#e34c26", "#a371f7", "#2ea043", "#ffa657"]
    for i, (language, count) in enumerate(languages.most_common(6)):
        y = 108 + i * 28
        pct = count / total * 100
        body.extend([text(32, y, language, 15),
                     f'<rect x="220" y="{y - 12}" width="{420 * pct / 100:.1f}" height="12" rx="6" fill="{colors[i]}"/>',
                     text(670, y, f"{pct:.1f}% ({count})", 14, "#8b949e")])
    if not languages:
        body.append(text(32, 140, "No primary language reported by GitHub."))
    languages_svg = card("Top Languages", "Primary language per public, non-fork repository | Share of all classified repos", body)

    body = []
    for i, (label, value) in enumerate([("Contributions", sum(n for _, n in days)), ("Current streak", current), ("Longest in period", longest)]):
        x = 32 + i * 260
        body.extend([text(x, 140, f"{value:,}" + ((" day" if value == 1 else " days") if i else ""), 32, "#ff8c42"), text(x, 179, label, 18)])
    streak_svg = card("GitHub Streak", f"Public calendar | {days[0][0]} to {days[-1][0]}", body, height=250)
    # Network/validation failures above leave every previous SVG untouched.
    PROFILE_DIR.mkdir(exist_ok=True)
    for name, svg in [("stats", stats_svg), ("top-langs", languages_svg), ("streak", streak_svg)]:
        temporary = PROFILE_DIR / f"{name}.svg.tmp"
        temporary.write_text(svg, encoding="utf-8")
        temporary.replace(PROFILE_DIR / f"{name}.svg")
    update_image_urls(ROOT / "README.md", PROFILE_DIR)
    print(f"Generated cards for {USER}: {len(repos)} repos, {len(days)} calendar days")


if __name__ == "__main__":
    generate()
