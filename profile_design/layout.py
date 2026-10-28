"""Continuous Facet layout: editorial content, project dossiers and real activity."""

import re

from .calendar import HEIGHT as CALENDAR_HEIGHT
from .calendar import render_calendar
from .hero import render_hero
from .sprites import chase, icon
from .svg import (
    CYAN,
    INK,
    LIME,
    PINK,
    SURFACE,
    box,
    document,
    line,
    nested,
    paragraph,
    plain,
    text,
)


def render_profile(root, snapshot, source, impact):
    parts = re.split(r"^## (.+)\n", source, flags=re.M)
    entries = dict(zip(parts[1::2], parts[2::2], strict=True))
    intro = [block.strip() for block in parts[0].split("\n\n") if block.strip()]
    hero_nested = nested(render_hero(root), 0, 0, 1000, 574, "0 0 1000 574")
    out = [hero_nested]
    y = 596
    out += [
        text(54, y, "INGÉNIEUR PÉDAGOGIQUE,", 27, True),
        text(54, y + 36, "CHEF DE PROJET ET DÉVELOPPEUR", 27, True),
        box(54, y + 51, 105, 6, LIME),
    ]
    y += 94
    for p in intro[1:]:
        h, y = paragraph(p, 54, y, 82, 22, bold=p.startswith("**"))
        out.append(h)
        y += 15
    # A contrasting open field note, not another framed card.
    y += 8
    out += [
        box(54, y, 6, 130, CYAN),
        text(79, y + 22, "CONCEVOIR AVEC LES ÉQUIPES", 18, True, True),
    ]
    y += 61
    for p in entries["Concevoir avec les équipes"].strip().split("\n\n"):
        h, y = paragraph(p, 79, y, 78, 22, bold=p.startswith("**"))
        out.append(h)
        y += 15
    # Compact process path gives a pixel-game rhythm without invented achievements.
    y += 10
    for i, (name, label) in enumerate(
        [("needs", "BESOINS"), ("brief", "CADRAGE"), ("window", "PROTOTYPES"), ("agent", "RETOURS")]
    ):
        x = 56 + i * 239
        out += [icon(name, x, y, INK, 3), text(x + 54, y + 24, label, 14, True, True)]
        if i < 3:
            out += [line(x + 170, y + 13, x + 215, y + 13, INK, "3 4")]
    y += 64
    game, game_css = chase(y, "process-game", reverse=True, hunting=True)
    out.append(game)
    y += 94
    out += [text(54, y, "RÉALISATIONS", 31, True)]
    y += 38
    projects = re.split(r"^### (.+)\n", entries["Projets phares"], flags=re.M)
    projects = list(zip(projects[1::2], projects[2::2], strict=True))
    for i, (title, content) in enumerate(projects):
        color = [CYAN, LIME, PINK, CYAN][i]
        blocks = [b.strip() for b in content.strip().split("\n\n")]
        # All four project dossiers share a colored left strip.
        begin = y
        inner_y = y + 82
        body = []
        name, _, subtitle = title.partition(" · ")
        body += [
            text(120, y + 33, name, 29, True),
            text(120, y + 61, subtitle.upper(), 13, True, True),
        ]
        for block in blocks:
            h, inner_y = paragraph(block, 120, inner_y + 12, 74, 21, leading=30)
            body.append(h)
            inner_y += 9
        end = inner_y + 16
        out += [
            box(104, begin - 3, 842, end - begin + 8, SURFACE, INK, 6),
            box(104, begin - 3, 8, end - begin + 8, color),
        ]
        out += [
            box(44, begin + 8, 44, 44, color, INK),
            text(51, begin + 38, f"{i + 1:02}", 22, True, True),
            *body,
        ]
        if i < 3:
            out += [line(66, begin + 57, 66, end + 40, INK, "5 7")]
        y = end + 44
    # Three small tool vignettes form one shared shelf, not three boxed cards.
    out += [text(54, y, "AUSSI DANS L’ATELIER", 19, True, True), line(54, y + 16, 946, y + 16)]
    y += 50
    extras = [
        x[2:] for x in entries["Aussi dans l’atelier"].strip().splitlines() if x.startswith("- ")
    ]
    end = y
    for i, entry in enumerate(extras):
        x = 54 + i * 305
        name, _, body = plain(entry).partition(" : ")
        out += [icon(["agent", "network", "window"][i], x, y, [PINK, CYAN, INK][i], 4)]
        h, z = paragraph(name, x, y + 76, 25, 20, bold=True, leading=28)
        out.append(h)
        z += 8
        h, z = paragraph(body, x, z, 25, 20, leading=28)
        out.append(h)
        end = max(end, z)
    y = end + 52
    case_top = y
    case_background = len(out)
    out += [
        box(48, y, 904, 350, INK),
        text(76, y + 41, "CAS CONCRET / L’ESPACE INTERVENANT", 21, True, True, CYAN),
    ]
    metrics = [
        (76, str(impact["active_contributors"]), "INTERVENANTS ACTIFS"),
        (
            380,
            "~ " + format(impact["teaching_hours_approximate"], ",").replace(",", " ") + " h",
            "HEURES DE COURS",
        ),
        (710, str(impact["months_since_launch"]) + " mois", "EN PRODUCTION"),
    ]
    for x, value, label in metrics:
        out += [
            text(x, y + 104, value, 37, True, color=SURFACE),
            text(x, y + 132, label, 11, True, True, LIME),
        ]
    z = y + 181
    for block in entries["Cas concret · L’espace intervenant"].strip().split("\n\n"):
        h, z = paragraph(block, 76, z, 79, 21, color=SURFACE, leading=31)
        out.append(h)
        z += 15
    out[case_background] = box(48, case_top, 904, max(350, z - case_top + 12), INK)
    y = max(case_top + 350, z + 12) + 48
    out += [
        text(54, y, "OUTILS DE CONSTRUCTION", 17, True, True),
        box(54, y + 15, 135, 5, LIME),
        text(54, y + 58, "Python · TypeScript · PHP · SQL", 23, True),
        text(54, y + 94, "Next.js · FastAPI · MongoDB", 22),
        text(54, y + 128, "REST · SOAP · MCP · Microsoft Graph", 21),
    ]
    y += 186

    calendar = render_calendar(snapshot)
    out.append(nested(calendar, 0, y, 1000, CALENDAR_HEIGHT, f"0 0 1000 {CALENDAR_HEIGHT}"))
    y += CALENDAR_HEIGHT
    out += [
        box(32, y, 936, 58, INK),
        text(
            52,
            y + 36,
            "COMPRENDRE LES USAGES. CONCEVOIR AVEC LES ÉQUIPES. FAIRE ÉVOLUER LES OUTILS.",
            14,
            True,
            True,
            SURFACE,
        ),
    ]
    height = y + 84
    return document(
        "".join(out),
        height,
        "Souphiane Jender — ingénieur pédagogique, chef de projet et développeur",
        game_css,
    )
