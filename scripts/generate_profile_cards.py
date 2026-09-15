#!/usr/bin/env python3
import json
import os
import urllib.request
from collections import defaultdict
from pathlib import Path

BASE_URL = "https://api.github.com"
USER = "zie225"
ROOT = Path(__file__).resolve().parent.parent
PROFILE_DIR = ROOT / "profile"
PROFILE_DIR.mkdir(exist_ok=True)

headers = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "GitHub-Profile-Generator",
}

token = os.environ.get("GITHUB_TOKEN")
if token:
    headers["Authorization"] = f"Bearer {token}"


def fetch_json(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def safe_get(obj, key, default=0):
    return obj.get(key, default) if isinstance(obj, dict) else default


user = fetch_json(f"{BASE_URL}/users/{USER}")
repos = []
page = 1
while True:
    page_data = fetch_json(f"{BASE_URL}/users/{USER}/repos?per_page=100&page={page}")
    if not page_data:
        break
    repos.extend(page_data)
    if len(page_data) < 100:
        break
    page += 1

stars = sum(safe_get(repo, "stargazers_count", 0) for repo in repos)
forks = sum(safe_get(repo, "forks_count", 0) for repo in repos)
watchers = sum(safe_get(repo, "watchers_count", 0) for repo in repos)

langs = defaultdict(int)
for repo in repos:
    name = safe_get(repo, "name")
    if not name:
        continue
    try:
        repo_langs = fetch_json(f"{BASE_URL}/repos/{USER}/{name}/languages")
    except Exception:
        continue
    for language, value in repo_langs.items():
        langs[language] += int(value)

lang_rows = sorted(langs.items(), key=lambda item: item[1], reverse=True)[:6]


def escape_xml(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def draw_stats_card():
    width, height = 820, 250
    repo_count = safe_get(user, "public_repos", 0)
    followers = safe_get(user, "followers", 0)
    following = safe_get(user, "following", 0)
    created = user.get("created_at", "")[:10]

    stats = [
        ("Repos", str(repo_count)),
        ("Stars", str(stars)),
        ("Followers", str(followers)),
        ("Following", str(following)),
        ("Forks", str(forks)),
        ("Watching", str(watchers)),
    ]

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="GitHub Stats">',
        '<rect width="100%" height="100%" fill="#0d1117" rx="16"/>',
        '<text x="40" y="42" fill="#e6edf3" font-size="28" font-family="Arial, sans-serif" font-weight="700">GitHub Stats</text>',
        '<text x="40" y="78" fill="#8b949e" font-size="14" font-family="Arial, sans-serif">@zie225 • joined 2026-??</text>',
    ]

    start_x = 40
    start_y = 110
    box_w = 120
    box_h = 90
    gap = 18
    colors = ["#2ea043", "#79c0ff", "#d2a8ff", "#ffa657", "#f85149", "#7ee787"]

    for i, (label, value) in enumerate(stats):
        x = start_x + (box_w + gap) * (i % 3)
        y = start_y + (box_h + 18) * (i // 3)
        c = colors[i % len(colors)]
        svg.append(f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="12" fill="#1f2633" stroke="{c}" stroke-opacity="0.44"/>')
        svg.append(f'<text x="{x + 16}" y="{y + 26}" fill="{c}" font-size="12" font-family="Arial, sans-serif">{escape_xml(label)}</text>')
        svg.append(f'<text x="{x + 16}" y="{y + 60}" fill="#f0f6fc" font-size="28" font-family="Arial, sans-serif" font-weight="700">{escape_xml(value)}</text>')

    svg.append('</svg>')
    return "\n".join(svg)


def draw_languages_card():
    width, height = 820, 260
    total = sum(value for _, value in lang_rows) if lang_rows else 1
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Top Languages">',
        '<rect width="100%" height="100%" fill="#0d1117" rx="16"/>',
        '<text x="40" y="42" fill="#e6edf3" font-size="28" font-family="Arial, sans-serif" font-weight="700">Top Languages</text>',
    ]
    colors = ["#2ea043", "#79c0ff", "#d2a8ff", "#ffa657", "#f85149", "#7ee787"]
    bar_y = 90
    for index, (name, value) in enumerate(lang_rows):
        x = 40
        y = bar_y + index * 28
        pct = value / total * 100
        bar_w = 640 * (pct / 100)
        svg.append(f'<text x="{x}" y="{y}" fill="#e6edf3" font-size="14" font-family="Arial, sans-serif">{escape_xml(name)}</text>')
        svg.append(f'<text x="{x + 710}" y="{y}" fill="#8b949e" font-size="12" font-family="Arial, sans-serif">{pct:.1f}%</text>')
        svg.append(f'<rect x="{x + 140}" y="{y - 12}" width="{bar_w}" height="12" rx="6" fill="{colors[index % len(colors)]}"/>')
    svg.append('</svg>')
    return "\n".join(svg)


def draw_streak_card():
    width, height = 820, 240
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="GitHub Streak">',
        '<rect width="100%" height="100%" fill="#0d1117" rx="16"/>',
        '<text x="40" y="42" fill="#e6edf3" font-size="28" font-family="Arial, sans-serif" font-weight="700">GitHub Streak</text>',
        f'<text x="40" y="92" fill="#ff7b72" font-size="18" font-family="Arial, sans-serif">🔥 Active developer</text>',
        f'<text x="40" y="134" fill="#c9d1d9" font-size="20" font-family="Arial, sans-serif">Public repos: {safe_get(user, "public_repos", 0)}</text>',
        f'<text x="40" y="166" fill="#c9d1d9" font-size="20" font-family="Arial, sans-serif">Followers: {safe_get(user, "followers", 0)}</text>',
        f'<text x="40" y="198" fill="#c9d1d9" font-size="20" font-family="Arial, sans-serif">Joined: {user.get("created_at", "")[:10]}</text>',
        '</svg>',
    ]
    return "\n".join(svg)


(PROFILE_DIR / "stats.svg").write_text(draw_stats_card(), encoding="utf-8")
(PROFILE_DIR / "top-langs.svg").write_text(draw_languages_card(), encoding="utf-8")
(PROFILE_DIR / "streak.svg").write_text(draw_streak_card(), encoding="utf-8")

print(f"Generated profile cards for {USER}")
print(f"Repos: {safe_get(user, 'public_repos', 0)}")
print(f"Stars: {stars}")
print(f"Top languages: {', '.join(name for name, _ in lang_rows[:3])}")
