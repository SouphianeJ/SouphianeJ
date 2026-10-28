"""Real contribution counts displayed as pixel tiles, with a decorative chase."""

from datetime import date, timedelta

from .sprites import chase
from .svg import INK, MUTED, box, document, text

HEIGHT = 486


def render_calendar(data):
    days = {date.fromisoformat(entry["date"]): entry["count"] for entry in data["days"]}
    start, end = min(days), max(days)
    origin = start - timedelta(days=(start.weekday() + 1) % 7)
    totals = [
        data["total_contributions"],
        sum(value > 0 for value in days.values()),
        data["restricted_contributions"],
    ]
    maximum = max(days.values()) or 1
    cuts = [max(1, maximum * 0.1), max(2, maximum * 0.3), max(3, maximum * 0.6)]
    colors = ["#e7e3d8", "#b7eeee", "#62dce6", "#00c4db", INK]
    active = [day for day, value in days.items() if value]
    last_active = max(active) if active else None
    note = (
        "Contributions privées partagées anonymement incluses."
        if data["restricted_contributions"]
        else "Activité visible au jeton de lecture."
    )
    parts = [
        "<desc>" + note + "</desc>",
        text(54, 32, "CARTE D’ACTIVITÉ", 29, True),
        text(54, 63, "UNE TUILE = UN JOUR · DONNÉES RÉELLES GITHUB", 12, True, True),
    ]
    for index, (count, label) in enumerate(
        zip(totals, ["CONTRIBUTIONS", "JOURS ACTIFS", "ANONYMISÉES"], strict=True)
    ):
        x = 54 + index * 307
        parts.extend(
            [
                text(x, 116, f"{count:,}".replace(",", " "), 35, True),
                text(x, 143, label, 11, True, True),
            ]
        )
    months = ["JAN", "FÉV", "MAR", "AVR", "MAI", "JUIN", "JUIL", "AOÛT", "SEP", "OCT", "NOV", "DÉC"]
    for day, count in days.items():
        col, row = (day - origin).days // 7, (day.weekday() + 1) % 7
        x, y = 62 + col * 16.5, 178 + row * 18
        level = 0 if not count else 1 + sum(count > cut for cut in cuts)
        parts.extend(
            [
                f'<g class="calendar-day" style="animation-delay:{col * 0.018:.3f}s">',
                box(x + 1, y + 2, 13, 13, "#c3c0b6" if not count else INK),
                f'<rect data-date="{day}" x="{x}" y="{y}" width="13" height="13" fill="{colors[level]}"><title>{day} : {count} contributions</title></rect>',
                "</g>",
            ]
        )
        if day == last_active:
            parts.append(
                f'<rect class="calendar-pulse" x="{x - 2}" y="{y - 2}" width="17" height="17" fill="none" stroke="#ff3b1f" stroke-width="2"/>'
            )
        if day.day == 1:
            parts.append(text(x, 166, months[day.month - 1], 9, mono=True, color=MUTED))
    game, game_css = chase(324, "calendar-game")
    parts.extend([game, text(54, 390, f"{start:%d/%m/%Y} → {end:%d/%m/%Y}", 13, True, True)])
    css = """.calendar-day{animation:calendar-in .7s ease-out backwards}.calendar-pulse{animation:calendar-pulse 3s ease-in-out infinite}@keyframes calendar-in{from{opacity:.25;transform:translateY(3px)}}@keyframes calendar-pulse{50%{opacity:.3}}@media(prefers-reduced-motion:reduce){.calendar-day,.calendar-pulse{animation:none!important}}"""
    return document("".join(parts), HEIGHT, "Activité GitHub — " + data["user"], css + game_css)
