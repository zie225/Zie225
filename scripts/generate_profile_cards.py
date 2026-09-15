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
        '<rect x="1" y="1" width="818" height="' + str(height - 2) + '" rx="18" fill="#0b1220" stroke="#26344b"/>',
        '<rect x="32" y="29" width="4" height="24" rx="2" fill="#38bdf8"/>',
        text(48, 48, title, 26), text(32, 78, subtitle, 15, "#a2b1c6"),
        *body, text(32, height - 18, "Updated " + updated, 12, "#8b949e"), '</svg>',
    ])


def update_image_urls(readme, profile_dir):
    content = readme.read_text(encoding="utf-8")
    for name in ("banner", "stats", "top-langs", "streak"):
        version = hashlib.sha256((profile_dir / f"{name}.svg").read_bytes()).hexdigest()[:16]
        url = f"https://raw.githubusercontent.com/zie225/Zie225/master/profile/{name}.svg?v={version}"
        content = re.sub(
            rf'src="(?:\./profile/|https://raw\.githubusercontent\.com/zie225/Zie225/master/profile/){name}\.svg(?:\?[^\"]*)?"',
            f'src="{url}"', content,
        )
    readme.write_text(content, encoding="utf-8")


def recent_repositories(repos):
    return sorted(
        (r for r in repos if not r["fork"] and not r.get("archived")
         and r["name"].casefold() != USER.casefold() and r.get("pushed_at")
         and r.get("size", 0) > 0),
        key=lambda r: (r["pushed_at"], r["name"]), reverse=True,
    )[:4]


def update_recent_repositories(readme, repos):
    rows = ["| Repository | Main language | Last push |", "| :--- | :--- | :--- |"]
    for repo in recent_repositories(repos):
        # HTML inside the Markdown table safely handles repository names.
        label = escape(repo["name"]).replace("|", "&#124;").replace("_", "&#95;")
        language = escape(repo.get("language") or "Not specified").replace("|", "&#124;")
        rows.append(f'| <a href="{escape(repo["html_url"], quote=True)}">{label}</a> | {language} | {repo["pushed_at"][:10]} |')
    content = readme.read_text(encoding="utf-8")
    start, end = "<!-- RECENT-REPOS:START -->", "<!-- RECENT-REPOS:END -->"
    if content.count(start) != 1 or content.count(end) != 1:
        raise ValueError("Missing or duplicate recent repository markers")
    before, rest = content.split(start)
    _, after = rest.split(end)
    body = "\n".join(rows) if len(rows) > 2 else "No public repositories to display."
    readme.write_text(before + start + "\n\n" + body + "\n\n" + end + after, encoding="utf-8")


def activity_heatmap(days):
    recent = days[-84:]
    cells = [text(32, 222, "LAST 12 WEEKS", 13, "#a2b1c6")]
    # Chronological rows, one week per column, using real contribution counts.
    for i, (day, count) in enumerate(recent):
        color = "#18263a" if not count else ("#1e3a8a" if count < 3 else "#2563eb" if count < 6 else "#38bdf8")
        cells.append(f'<rect x="{32 + (i // 7) * 27}" y="{237 + (i % 7) * 11}" width="22" height="8" rx="2" fill="{color}"><title>{day}: {count} contributions</title></rect>')
    last30 = days[-30:]
    cells.extend([text(408, 253, f"{sum(n for _, n in last30)} contributions", 24, "#38bdf8"),
                  text(408, 283, f"{sum(n > 0 for _, n in last30)} active days in the last 30 days", 17, "#a2b1c6"),
                  text(32, 339, f"{recent[0][0]} to {recent[-1][0]} | Brighter = more contributions", 13, "#a2b1c6")])
    return cells


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
    stats = [("Public repos", user["public_repos"]), ("Non-fork repos", sum(not r["fork"] for r in repos)),
             ("Followers", user["followers"]), ("Following", user["following"]),
             ("Stars / non-fork repos", sum(r["stargazers_count"] for r in repos if not r["fork"])), ("Contributions (12 mo)", sum(n for _, n in days))]
    body = []
    for i, (label, value) in enumerate(stats):
        x, y = 32 + (i % 3) * 260, 114 + (i // 3) * 88
        body.extend([text(x, y, label, 16, "#a2b1c6"), text(x, y + 36, f"{value:,}", 34, "#7dd3fc")])
    stats_svg = card("GitHub at a glance", f"@{USER} | Public repositories and contributions", body)

    languages = Counter(r["language"] for r in repos if not r["fork"] and r["language"])
    total = sum(languages.values())
    body = []
    colors = ["#38bdf8", "#7dd3fc", "#a5b4fc", "#f9a8d4", "#fcd34d", "#94a3b8"]
    for i, (language, count) in enumerate(languages.most_common(6)):
        y = 108 + i * 28
        pct = count / total * 100
        body.extend([text(32, y, language, 15),
                     f'<rect x="220" y="{y - 12}" width="{420 * pct / 100:.1f}" height="12" rx="6" fill="{colors[i]}"/>',
                     text(670, y, f"{pct:.1f}% ({count})", 14, "#8b949e")])
    if not languages:
        body.append(text(32, 140, "No primary language reported by GitHub."))
    languages_svg = card("Language landscape", "Primary language of public, non-fork repositories", body)

    body = []
    for i, (label, value) in enumerate([("Contributions", sum(n for _, n in days)), ("Current streak", current), ("Longest in period", longest)]):
        x = 32 + i * 260
        body.extend([text(x, 140, f"{value:,}" + ((" day" if value == 1 else " days") if i else ""), 32, "#a5b4fc"), text(x, 179, label, 18)])
    body.extend(activity_heatmap(days))
    streak_svg = card("Contribution rhythm", f"Public calendar | {days[0][0]} to {days[-1][0]}", body, height=382)
    # Network/validation failures above leave every previous SVG untouched.
    PROFILE_DIR.mkdir(exist_ok=True)
    for name, svg in [("stats", stats_svg), ("top-langs", languages_svg), ("streak", streak_svg)]:
        temporary = PROFILE_DIR / f"{name}.svg.tmp"
        temporary.write_text(svg, encoding="utf-8")
        temporary.replace(PROFILE_DIR / f"{name}.svg")
    update_recent_repositories(ROOT / "README.md", repos)
    update_image_urls(ROOT / "README.md", PROFILE_DIR)
    print(f"Generated cards for {USER}: {len(repos)} repos, {len(days)} calendar days")


if __name__ == "__main__":
    generate()
