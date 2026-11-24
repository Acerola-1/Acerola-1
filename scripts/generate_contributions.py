import json
import os
import urllib.request
from datetime import datetime
from pathlib import Path

LEVELS = {
    "NONE": "#ebedf0",
    "FIRST_QUARTILE": "#9be9a8",
    "SECOND_QUARTILE": "#40c463",
    "THIRD_QUARTILE": "#30a14e",
    "FOURTH_QUARTILE": "#216e39",
}
QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            contributionLevel
          }
        }
      }
    }
  }
}
"""
CELL = 10
GAP = 3
STEP = CELL + GAP
LEFT = 28
TOP = 18


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "contribution-heatmap",
        },
    )
    with urllib.request.urlopen(req) as resp:
        payload = json.load(resp)
    if "errors" in payload:
        raise SystemExit(payload["errors"])
    return payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def render(calendar):
    weeks = calendar["weeks"]
    width = LEFT + len(weeks) * STEP + 8
    height = TOP + 7 * STEP + 8
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;font-size:10px;fill:#57606a}</style>',
    ]
    prev_month = None
    prev_label_x = -100
    for wi, week in enumerate(weeks):
        days = week["contributionDays"]
        month = datetime.fromisoformat(days[0]["date"]).strftime("%b")
        x_label = LEFT + wi * STEP
        if month != prev_month and x_label - prev_label_x >= 26:
            parts.append(f'<text x="{x_label}" y="12">{month}</text>')
            prev_label_x = x_label
        prev_month = month
        for day in days:
            row = (datetime.fromisoformat(day["date"]).weekday() + 1) % 7
            x = LEFT + wi * STEP
            y = TOP + row * STEP
            fill = LEVELS[day["contributionLevel"]]
            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{fill}">'
                f'<title>{day["date"]}: {day["contributionCount"]} contributions</title></rect>'
            )
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(f'<text x="0" y="{TOP + row * STEP + 9}">{label}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    login = os.environ.get("GITHUB_REPOSITORY_OWNER", "Acerola-1")
    token = os.environ["GH_TOKEN"]
    calendar = fetch(login, token)
    out = Path(__file__).resolve().parent.parent / "assets" / "contributions.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(calendar), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
