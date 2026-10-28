"""Fetch public/shared anonymous contribution counts and render a standalone contribution calendar SVG."""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

QUERY = """query($login:String!, $from:DateTime!, $to:DateTime!) {
 user(login:$login) { login contributionsCollection(from:$from,to:$to) {
 startedAt endedAt hasAnyRestrictedContributions restrictedContributionsCount
 contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
 } }
}"""


def fetch(login: str, now: datetime) -> dict:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN ou GH_TOKEN requis pour lire GraphQL.")
    start = now.date() - timedelta(days=364)
    variables = {
        "login": login,
        "from": f"{start}T00:00:00Z",
        "to": now.isoformat().replace("+00:00", "Z"),
    }
    request = Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": variables}).encode(),
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "User-Agent": "SouphianeJ-profile-activity",
        },
    )
    try:
        with urlopen(request, timeout=45) as response:
            payload = json.load(response)
    except HTTPError as error:
        raise ValueError(
            f"GitHub GraphQL : HTTP {error.code}. Graphiques précédents conservés."
        ) from None
    except (URLError, TimeoutError, json.JSONDecodeError):
        raise ValueError(
            "Réponse GitHub indisponible ou invalide. Graphiques précédents conservés."
        ) from None
    if not isinstance(payload, dict):
        raise ValueError("Réponse GraphQL invalide. Graphiques précédents conservés.")
    if payload.get("errors"):
        raise ValueError("GitHub a refusé la requête GraphQL. Graphiques précédents conservés.")
    response_data = payload.get("data")
    if not isinstance(response_data, dict):
        raise ValueError("Données GraphQL absentes. Graphiques précédents conservés.")
    user = response_data.get("user")
    if not isinstance(user, dict) or user.get("login", "").lower() != login.lower():
        raise ValueError("Profil GitHub introuvable dans la réponse.")
    return {
        "user": login,
        "source": "GitHub GraphQL API",
        "fetched_at": now.isoformat().replace("+00:00", "Z"),
        "collection": user["contributionsCollection"],
    }


def validate(data: dict) -> tuple[date, date, dict[date, int]]:
    try:
        c = data["collection"]
        calendar = c["contributionCalendar"]
        start = date.fromisoformat(c["startedAt"][:10])
        end = date.fromisoformat(c["endedAt"][:10])
        if (end - start).days != 364:
            raise ValueError("La fenêtre doit couvrir exactement 365 dates.")
        days = {}
        for week in calendar["weeks"]:
            for entry in week["contributionDays"]:
                day = date.fromisoformat(entry["date"])
                if not start <= day <= end:
                    continue
                count = entry["contributionCount"]
                if day in days or type(count) is not int or count < 0:
                    raise ValueError("Dates dupliquées ou compteurs invalides.")
                days[day] = count
        total = calendar["totalContributions"]
        restricted = c["restrictedContributionsCount"]
        if len(days) != 365 or sum(days.values()) != total:
            raise ValueError("Calendrier incomplet ou total incohérent.")
        if type(total) is not int or type(restricted) is not int or not 0 <= restricted <= total:
            raise ValueError("Totaux invalides.")
        if type(c["hasAnyRestrictedContributions"]) is not bool:
            raise ValueError("Indicateur de contributions anonymisées absent.")
        return start, end, dict(sorted(days.items()))
    except (KeyError, TypeError, IndexError):
        raise ValueError("Schéma de contributions incomplet.") from None


def render(data):
    from profile_design.calendar import render_calendar

    start, end, days = validate(data)
    snapshot = {
        "user": data["user"],
        "period": {"from": str(start), "to": str(end)},
        "total_contributions": sum(days.values()),
        "restricted_contributions": data["collection"]["restrictedContributionsCount"],
        "fetched_at": data["fetched_at"],
        "days": [{"date": str(day), "count": count} for day, count in days.items()],
    }
    return {"activity.svg": render_calendar(snapshot)}


def publish_local(data, output):
    # Validate and render before touching existing artifacts. Workflow only commits
    # after this command succeeds; an API failure preserves the previous graphs.
    rendered = render(data)
    start, end, days = validate(data)
    safe = {
        "user": data["user"],
        "source": "GitHub GraphQL API",
        "fetched_at": data["fetched_at"],
        "period": {"from": start.isoformat(), "to": end.isoformat()},
        "total_contributions": sum(days.values()),
        "restricted_contributions": data["collection"]["restrictedContributionsCount"],
        "days": [{"date": str(day), "count": count} for day, count in days.items()],
    }
    rendered["activity.json"] = json.dumps(safe, ensure_ascii=False, indent=2) + "\n"
    output = Path(output)
    # Preserve the timestamp of identical data to avoid twice-daily bot commits
    # solely for a new observation time. Re-render anyway so template edits apply.
    try:
        previous = json.loads((output / "activity.json").read_text())

        def without_time(value):
            return {k: v for k, v in value.items() if k != "fetched_at"}

        datetime.fromisoformat(previous["fetched_at"].replace("Z", "+00:00"))
        if without_time(previous) == without_time(safe):
            data = dict(data, fetched_at=previous["fetched_at"])
            safe["fetched_at"] = previous["fetched_at"]
            rendered = render(data)
            rendered["activity.json"] = json.dumps(safe, ensure_ascii=False, indent=2) + "\n"
    except (OSError, ValueError, KeyError, TypeError):
        pass
    output.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".activity-", dir=output) as temporary:
        for name, contents in rendered.items():
            (Path(temporary) / name).write_text(contents, encoding="utf-8")
        for name in rendered:
            (Path(temporary) / name).replace(output / name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--login", default="SouphianeJ")
    parser.add_argument("--output", type=Path, default=Path("assets"))
    parser.add_argument(
        "--input", type=Path, help="Réponse agrégée déjà enregistrée, pour validation hors réseau."
    )
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9-]{1,39}", args.login):
        parser.error("Identifiant GitHub invalide.")
    try:
        data = (
            json.loads(args.input.read_text())
            if args.input
            else fetch(args.login, datetime.now(UTC))
        )
        if data["user"].lower() != args.login.lower():
            raise ValueError("Le relevé ne correspond pas au profil demandé.")
        publish_local(data, args.output)
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + "\n")
    print("Calendrier de contributions actualisé : " + args.login)


if __name__ == "__main__":
    main()
