"""Facet hero using the validated twelve-second astronaut animation."""

from .svg import CYAN, INK, LIME, RED, SURFACE, box, document, nested, text


def render_hero(root):
    actor = (root / "assets/astronaut.svg").read_text(encoding="utf-8")
    parts = [
        '<defs><pattern id="hero-grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#0a0a0a" stroke-opacity=".045"/></pattern></defs>',
        box(32, 24, 936, 44, INK),
        text(48, 53, "SJ / SOUPHIANE JENDER", 18, True, True, SURFACE),
        text(662, 52, "PÉDAGOGIE · DEV · IA", 14, mono=True, color=CYAN),
        box(32, 92, 936, 449, SURFACE, INK, 7),
        box(32, 92, 936, 449, "url(#hero-grid)"),
        box(56, 109, 510, 29, LIME, INK),
        text(
            67,
            129,
            "APPLICATION MÉTIER · SIMPLIFIER DES PROCESS ET ACTIONS · AGENTS IA",
            10,
            True,
            True,
        ),
        text(58, 194, "COMPRENDRE", 46, True),
        text(58, 250, "ET COLLABORER", 46, True, color=RED),
        text(58, 306, "POUR CONCEVOIR", 46, True),
        text(58, 362, "DES SOLUTIONS", 46, True),
        box(56, 385, 510, 62, CYAN, INK),
        text(68, 430, "FACILES À ADOPTER", 38, True),
        nested(actor, 594, 153, 360, 352, "0 0 93 91"),
    ]
    return document(
        "".join(parts),
        574,
        "Comprendre et collaborer pour concevoir des solutions faciles à adopter",
    )
