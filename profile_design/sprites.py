"""Original pixel sprites and decorative chases; never alter activity data."""

from math import atan2, pi

from .svg import CYAN, INK, LIME, PINK, SURFACE, box

# All process icons share a 13×13 grid and a three-pixel display scale.
PATTERNS = {
    "needs": [
        "0000000000000",
        "0111111111110",
        "0122222222210",
        "0122222222210",
        "0121121121210",
        "0121121121210",
        "0122222222210",
        "0111111111110",
        "0001100000000",
        "0011000000000",
        "0110000000000",
        "0100000000000",
        "0000000000000",
    ],
    "brief": [
        "0111111111110",
        "0100000000010",
        "0101101111010",
        "0100000000010",
        "0101101111010",
        "0100000003310",
        "0100000033010",
        "0103300330010",
        "0100333300010",
        "0100033000010",
        "0100000000010",
        "0111111111110",
        "0000000000000",
    ],
    "window": [
        "0111111111110",
        "0122222222210",
        "0111111111110",
        "0100000000010",
        "0101101110010",
        "0101101110010",
        "0100000000010",
        "0101111110010",
        "0101000010010",
        "0101111110010",
        "0100000000010",
        "0111111111110",
        "0000000000000",
    ],
    "agent": [
        "0000011000000",
        "0000011000000",
        "0011111111100",
        "0122222222210",
        "0124422442210",
        "0121122112210",
        "0122222222210",
        "0121111112210",
        "0111111111110",
        "0001000010000",
        "0111000011100",
        "0000000000000",
        "0000000000000",
    ],
    "network": [
        "0110000011000",
        "0121000121000",
        "0110000011000",
        "0010000010000",
        "0011111110000",
        "0000010000000",
        "0000010000000",
        "0001111100000",
        "0001222100000",
        "0001111100000",
        "0000000000000",
        "0000000000000",
        "0000000000000",
    ],
}


def icon(name, x, y, color=INK, scale=3):
    palette = {"1": color, "2": CYAN, "3": LIME, "4": SURFACE}
    return "".join(
        box(x + j * scale, y + i * scale, scale, scale, palette[pixel])
        for i, row in enumerate(PATTERNS[name])
        for j, pixel in enumerate(row)
        if pixel != "0"
    )


def pacman(x, y, color=LIME, opening=pi / 5):
    """21×21 circular silhouette, outlined mouth and a two-pixel eye."""
    pixels = []
    for row in range(21):
        for col in range(21):
            radius = (col - 10) ** 2 + (row - 10) ** 2
            angle = abs(atan2(row - 10, col - 10))
            if radius > 100 or (col >= 10 and angle < opening):
                continue
            edge = radius > 81 or (col >= 10 and abs(angle - opening) < 0.13)
            eye = col in (11, 12) and row in (4, 5)
            pixels.append(box(x + col * 2, y + row * 2, 2, 2, INK if edge or eye else color))
    return "".join(pixels)


def ghost(x, y, color):
    silhouette = set()
    for row in range(21):
        for col in range(21):
            dome = row <= 10 and (col - 10) ** 2 + (row - 10) ** 2 <= 100
            body = 10 < row < 18
            feet = row >= 18 and (col < 5 or 8 <= col < 13 or col >= 16)
            if dome or body or feet:
                silhouette.add((col, row))
    pixels = []
    for col, row in sorted(silhouette, key=lambda point: (point[1], point[0])):
        edge = any(
            (col + dx, row + dy) not in silhouette for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]
        )
        fill = INK if edge else color
        if row in range(6, 12) and (4 <= col < 8 or 13 <= col < 17):
            fill = SURFACE
        if row in (8, 9, 10) and col in (6, 7, 15, 16):
            fill = INK
        pixels.append(box(x + col * 2, y + row * 2, 2, 2, fill))
    return "".join(pixels)


def chase(y, name, *, reverse=False, hunting=False):
    """Namespaced animation: movement, clips and dots cannot collide across scenes."""
    color = CYAN if hunting else LIME
    mirror = ' transform="translate(1000 0) scale(-1 1)"' if reverse else ""
    css = f"""
    .{name}-move{{animation:{name}-travel 12s linear infinite}}
    .{name}-open{{animation:game-chomp .4s steps(1) infinite}}
    .{name}-closed{{animation:game-chomp .4s steps(1) -.2s infinite}}
    .{name}-ghost{{animation:game-bob .8s steps(2,end) infinite}}
    @keyframes {name}-travel{{0%{{opacity:1;transform:translateX(0)}}88%{{opacity:1;transform:translateX(824px)}}90%{{opacity:0;transform:translateX(824px)}}94%,100%{{opacity:0;transform:translateX(0)}}}}
    @keyframes game-chomp{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
    @keyframes game-bob{{50%{{transform:translateY(-2px)}}}}
    @media(prefers-reduced-motion:reduce){{.{name}-move,.{name}-open,.{name}-closed,.{name}-ghost,.{name}-dot{{animation:none!important}}.{name}-closed{{opacity:0!important}}}}
    """
    parts = [
        f'<g{mirror}><defs><clipPath id="{name}-clip"><rect x="54" y="{y - 6}" width="892" height="56"/></clipPath></defs>'
    ]
    for index in range(28):
        x = 112 + index * 29
        eat = max(0.2, min(87, (x - 106) / 824 * 88))
        css += f"@keyframes {name}-eat-{index}{{0%,{eat - 0.1:.3f}%{{opacity:1}}{eat:.3f}%,90%{{opacity:0}}94%,100%{{opacity:1}}}}"
        parts.append(
            f'<rect class="{name}-dot" x="{x}" y="{y + 18}" width="5" height="5" fill="{INK}" style="animation:{name}-eat-{index} 12s linear infinite"/>'
        )
    ghost_positions = (146, 208) if hunting else (-18, -80)
    parts.extend(
        [
            f'<g clip-path="url(#{name}-clip)"><g class="{name}-move">',
            f'<g class="{name}-open">{pacman(64, y, color)}</g>',
            f'<g class="game-mouth-closed {name}-closed">{pacman(64, y, color, pi / 18)}</g>',
            f'<g class="{name}-ghost">{ghost(ghost_positions[0], y, PINK)}{ghost(ghost_positions[1], y, CYAN if not hunting else LIME)}</g>',
            "</g></g></g>",
        ]
    )
    return "".join(parts), css
