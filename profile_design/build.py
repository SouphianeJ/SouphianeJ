"""Build the public profile from versioned content, assets and aggregate data."""

import argparse
import json
import xml.etree.ElementTree as ET
from datetime import UTC, date
from pathlib import Path
from tempfile import TemporaryDirectory

from . import activity
from .calendar import render_calendar
from .layout import render_profile
from .svg import static_version

ROOT = Path(__file__).resolve().parents[1]


def load_content(root):
    impact = json.loads((root / "content/impact.json").read_text(encoding="utf-8"))
    for value in impact.values():
        if type(value) is not int or value <= 0:
            raise ValueError("Les indicateurs du cas concret doivent être des entiers positifs.")
    if impact["temporary_lecturers"] + impact["self_employed"] > impact["active_contributors"]:
        raise ValueError("Les catégories ne peuvent pas dépasser le total des intervenants.")
    summary = (
        f"Sur les {impact['months_since_launch']} premiers mois de mise en production, "
        f"l’espace intervenant gère l’onboarding et la rémunération de **{impact['active_contributors']} intervenants actifs**, "
        f"dont **{impact['temporary_lecturers']} vacataires** et **{impact['self_employed']} auto-entrepreneurs**, "
        f"pour environ **{format(impact['teaching_hours_approximate'], ',').replace(',', ' ')} heures de cours**."
    )
    source = (root / "content/profile.md").read_text(encoding="utf-8")
    if source.count("{{impact_summary}}") != 1:
        raise ValueError("Le contenu doit inclure une fois {{impact_summary}}.")
    return source.replace("{{impact_summary}}", summary), impact


def validate_snapshot(snapshot):
    # Reuse transport validation: missing or duplicate dates must never become zeros.
    raw = {
        "collection": {
            "startedAt": snapshot["period"]["from"],
            "endedAt": snapshot["period"]["to"],
            "restrictedContributionsCount": snapshot["restricted_contributions"],
            "hasAnyRestrictedContributions": snapshot["restricted_contributions"] > 0,
            "contributionCalendar": {
                "totalContributions": snapshot["total_contributions"],
                "weeks": [
                    {
                        "contributionDays": [
                            {"date": d["date"], "contributionCount": d["count"]}
                            for d in snapshot["days"]
                        ]
                    }
                ],
            },
        }
    }
    activity.validate(raw)
    date.fromisoformat(snapshot["fetched_at"][:10])


def artifacts(root):
    snapshot = json.loads((root / "assets/activity.json").read_text(encoding="utf-8"))
    validate_snapshot(snapshot)
    source, impact = load_content(root)
    svg = render_profile(root, snapshot, source, impact)
    static = static_version(svg)
    for content in [svg, static]:
        ET.fromstring(content)
    readme = (
        """<picture>
  <source media="(prefers-reduced-motion: reduce)" srcset="assets/profile-static.svg">
  <img src="assets/profile.svg" width="100%" alt="Souphiane Jender — Comprendre et collaborer pour concevoir des solutions faciles à adopter. Ingénieur pédagogique, chef de projet et développeur.">
</picture>

<details>
<summary>Lire la version texte</summary>

"""
        + source
        + "\n</details>\n"
    )
    return {
        "assets/profile.svg": svg,
        "assets/profile-static.svg": static,
        "assets/activity.svg": render_calendar(snapshot),
        "README.md": readme,
    }


def build(root=ROOT, check=False):
    files = artifacts(root)
    if check:
        dirty = [
            name
            for name, content in files.items()
            if not (root / name).exists() or (root / name).read_text(encoding="utf-8") != content
        ]
        if dirty:
            raise ValueError("Fichiers à régénérer : " + ", ".join(dirty))
        return
    with TemporaryDirectory(prefix=".profile-build-", dir=root) as temporary:
        temporary = Path(temporary)
        for index, content in enumerate(files.values()):
            path = temporary / str(index)
            path.write_text(content, encoding="utf-8")
            # SVGs are already validated; publish only once every render succeeds.
        for index, name in enumerate(files):
            target = root / name
            (temporary / str(index)).replace(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh", action="store_true", help="Relire les contributions GitHub avant génération."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Vérifier la reproductibilité sans modifier les fichiers.",
    )
    args = parser.parse_args()
    if args.refresh and args.check:
        parser.error("--refresh et --check sont exclusifs.")
    try:
        if args.refresh:
            from datetime import datetime

            data = activity.fetch("SouphianeJ", datetime.now(UTC))
            activity.publish_local(data, ROOT / "assets")
        build(check=args.check)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, str(error) + "\n")
    print("Fiche vérifiée." if args.check else "Fiche générée.")


if __name__ == "__main__":
    main()
