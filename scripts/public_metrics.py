"""Render a public-only GitHub repository overview (no personal token required)."""
import os
import json
import urllib.request
from collections import Counter
from html import escape
from pathlib import Path

USER = "burakyurday"
headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-metrics"}
if os.environ.get("GH_TOKEN"):
    headers["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
repos = []
page = 1
while True:
    req = urllib.request.Request(
        f"https://api.github.com/users/{USER}/repos?type=owner&per_page=100&page={page}",
        headers=headers,
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        items = json.load(response)
    repos.extend(r for r in items if not r["private"] and not r["fork"] and r["name"].lower() != USER.lower())
    if len(items) < 100:
        break
    page += 1

counts = Counter(r["language"] for r in repos if r.get("language"))
colors = {"JavaScript": "#F1E05A", "TypeScript": "#3178C6", "Rust": "#DEA584", "Java": "#B07219", "Python": "#3572A5", "Swift": "#F05138", "HTML": "#E34C26", "CSS": "#563D7C"}
entries = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
shown = entries[:5]
if len(entries) > 5:
    shown = entries[:4] + [("Other", sum(v for _, v in entries[4:]))]
total = sum(counts.values())
segments = []
labels = []
x = 404
for i, (language, count) in enumerate(shown):
    color = colors.get(language, "#8B94A7")
    width = 531 * count / total if total else 0
    segments.append(f'<rect x="{x:.2f}" y="93" width="{width:.2f}" height="13" fill="{color}"/>')
    lx = 404 + (i % 3) * 178
    ly = 132 + (i // 3) * 28
    labels.append(f'<circle cx="{lx + 5}" cy="{ly-4}" r="5" fill="{color}"/><text x="{lx+17}" y="{ly}" font-size="13" fill="#F7F5F0">{escape(language[:17])} · {count}</text>')
    x += width

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="220" viewBox="0 0 960 220" role="img" aria-label="Public repositories: {len(repos)}; primary languages: {len(counts)}">
<rect width="960" height="220" rx="12" fill="#15171B"/>
<g font-family="Arial,Helvetica,sans-serif">
<text x="25" y="32" font-size="13" font-weight="700" letter-spacing="1.7" fill="#FF6537">PUBLIC REPOSITORY OVERVIEW</text>
<text x="935" y="32" text-anchor="end" font-size="12" fill="#A4A9B3">GITHUB / PUBLIC DATA</text>
<path d="M25 48H935M378 65V193" stroke="#383C44"/>
<text x="25" y="111" font-size="54" font-weight="700" fill="#F7F5F0">{len(repos):02d}</text>
<text x="25" y="137" font-size="14" fill="#B8BBC3">Public project repos</text>
<text x="201" y="111" font-size="54" font-weight="700" fill="#F7F5F0">{len(counts):02d}</text>
<text x="201" y="137" font-size="14" fill="#B8BBC3">Primary languages</text>
<text x="25" y="180" font-size="12" fill="#8F95A0">Profile and forks excluded</text>
<text x="404" y="76" font-size="13" font-weight="700" fill="#F7F5F0">PRIMARY LANGUAGE BY REPOSITORY</text>
<rect x="404" y="93" width="531" height="13" rx="6" fill="#373B43"/>
<clipPath id="bar"><rect x="404" y="93" width="531" height="13" rx="6"/></clipPath>
<g clip-path="url(#bar)">{"".join(segments)}</g>
{"".join(labels)}
<text x="404" y="193" font-size="12" fill="#8F95A0">Repository counts, not lines of code or proficiency.</text>
</g></svg>
'''
path = Path("assets/github-metrics.svg")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(svg, encoding="utf-8")
