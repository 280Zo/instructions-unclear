"""Render the README hero image (light and dark SVG) for agents/generate.py.

Style: the diagram-design skill's default editorial tokens, except the accent,
which is deep teal (user choice, 2026-10-26; orange and blue were rejected).
In light mode the small label uses a darker teal so it passes WCAG AA. Text
uses the skill's "system" font stacks, because GitHub shows README SVGs as
images that can't load web fonts. Coordinates sit on a 4 px grid.
"""

from html import escape

THEMES = {
    "light": {
        "paper": "#f5f5f5", "card": "#ffffff", "ink": "#2d3142", "muted": "#4f5d75", "soft": "#5a6580",
        "rule": "rgba(45,49,66,0.12)", "border": "rgba(45,49,66,0.22)", "dots": "rgba(45,49,66,0.10)",
        "accent": "#0f766e", "tint": "rgba(15,118,110,0.14)", "label": "#115e59",
    },
    "dark": {
        "paper": "#2d3142", "card": "#393e53", "ink": "#f5f5f5", "muted": "#bfc0c0", "soft": "#949eb2",
        "rule": "rgba(245,245,245,0.12)", "border": "rgba(191,192,192,0.25)", "dots": "rgba(245,245,245,0.08)",
        "accent": "#5eead4", "tint": "rgba(94,234,212,0.16)",
    },
}
SERIF = "'Instrument Serif', Georgia, 'Times New Roman', serif"
SANS = "'Geist', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "'Geist Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

WIDTH, HEIGHT = 1200, 600
RADIUS = 16  # rounded image corners; the README background shows outside them
LEFT, CARD_W, CARD_GAP, CARD_Y, CARD_H = 28, 120, 8, 276, 160
BUS_Y = 252
TOOLS = ["OpenCode", "Claude Code", "Codex", "Copilot", "Cursor"]


def text(x, y, content, size, color, family=SANS, weight=None, anchor=None, spacing=None):
    attrs = [f'x="{x}"', f'y="{y}"', f'fill="{color}"', f'font-size="{size}"', f'font-family="{family}"']
    if weight:
        attrs.append(f'font-weight="{weight}"')
    if anchor:
        attrs.append(f'text-anchor="{anchor}"')
    if spacing:
        attrs.append(f'letter-spacing="{spacing}"')
    return f'<text {" ".join(attrs)}>{escape(content)}</text>'


def name_lines(name):
    if len(name) > 14 and "-" in name:
        head, tail = name.split("-", 1)
        return [head + "-", tail]
    return [name]


def render(theme, agents, total_skills, mcp_count, shared):
    """agents: list of (name, kind, skills_in_view, tag)."""
    t = THEMES[theme]
    centers = [LEFT + i * (CARD_W + CARD_GAP) + CARD_W // 2 for i in range(len(agents))]
    names = ", ".join(f"{a[0]} ({a[2]})" for a in agents)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}" '
        'role="img" aria-labelledby="hero-title hero-desc">',
        '<title id="hero-title">Install once. Each agent sees only its own skills.</title>',
        f'<desc id="hero-desc">{escape(f"One shared install of {total_skills} skills and {mcp_count} MCP servers feeds nine agents. Skills each agent can see: {names}. Installs into " + ", ".join(TOOLS) + " and about 40 more tools with rulesync.")}</desc>',
        "<defs>",
        f'<pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="0.9" fill="{t["dots"]}"/></pattern>',
        f'<marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{t["muted"]}"/></marker>',
        "</defs>",
        f'<rect width="{WIDTH}" height="{HEIGHT}" rx="{RADIUS}" fill="{t["paper"]}"/>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" rx="{RADIUS}" fill="url(#dots)" opacity="0.6"/>',
        text(LEFT, 44, "INSTRUCTIONS-UNCLEAR · CONTEXT FILES FOR AI CODING TOOLS", 11, t["soft"], MONO, 500, spacing="0.18em"),
        text(LEFT, 96, "Install once. Each agent sees only its own skills.", 44, t["ink"], SERIF),
        text(LEFT, 132, "Rules, agents, skills and MCP servers for every assistant. Specialist agents keep everything else "
             "out of the request, so context stays small.", 15, t["muted"]),
    ]

    # Shared install band: the one focal element.
    band_w = WIDTH - 2 * LEFT
    out += [
        f'<rect x="{LEFT}" y="156" width="{band_w}" height="72" rx="8" fill="{t["tint"]}" stroke="{t["accent"]}" stroke-width="1.2"/>',
        text(LEFT + 20, 180, "SHARED INSTALL", 10, t.get("label", t["accent"]), MONO, 500, spacing="0.18em"),
        text(LEFT + 20, 212, f"{total_skills} skills · {mcp_count} MCP servers · one rules file", 28, t["ink"], SERIF),
        text(WIDTH - LEFT - 20, 188, "Every agent also gets", 11, t["muted"], MONO, anchor="end"),
        text(WIDTH - LEFT - 20, 206, shared, 11, t["ink"], MONO, anchor="end"),
    ]

    # Connectors before cards (z-order): trunk, bus, one drop per card.
    first, last = centers[0], centers[-1]
    out.append(f'<path d="M {WIDTH // 2},228 V {BUS_Y}" fill="none" stroke="{t["muted"]}" stroke-width="1"/>')
    out.append(f'<path d="M {first + 8},{BUS_Y} H {last - 8}" fill="none" stroke="{t["muted"]}" stroke-width="1"/>')
    for i, cx in enumerate(centers):
        if i == 0:
            d = f"M {cx + 8},{BUS_Y} Q {cx},{BUS_Y} {cx},{BUS_Y + 8} V {CARD_Y - 2}"
        elif i == len(centers) - 1:
            d = f"M {cx - 8},{BUS_Y} Q {cx},{BUS_Y} {cx},{BUS_Y + 8} V {CARD_Y - 2}"
        else:
            d = f"M {cx},{BUS_Y} V {CARD_Y - 2}"
        out.append(f'<path d="{d}" fill="none" stroke="{t["muted"]}" stroke-width="1" marker-end="url(#arrow)"/>')

    # Agent cards.
    for (name, kind, count, tag), cx in zip(agents, centers):
        x = cx - CARD_W // 2
        bar = max(4, round(96 * count / total_skills / 4) * 4)
        out.append(f'<rect x="{x}" y="{CARD_Y}" width="{CARD_W}" height="{CARD_H}" rx="6" fill="{t["card"]}" stroke="{t["border"]}" stroke-width="1"/>')
        out.append(text(x + 12, CARD_Y + 20, kind.upper(), 8, t["soft"], MONO, 500, spacing="0.16em"))
        for j, line in enumerate(name_lines(name)):
            out.append(text(x + 12, CARD_Y + 40 + 16 * j, line, 13, t["ink"], SANS, 600))
        out.append(text(x + 12, CARD_Y + 104, str(count), 44, t["ink"], SERIF))
        out.append(f'<rect x="{x + 12}" y="{CARD_Y + 112}" width="96" height="4" rx="2" fill="{t["rule"]}"/>')
        out.append(f'<rect x="{x + 12}" y="{CARD_Y + 112}" width="{bar}" height="4" rx="2" fill="{t["muted"]}"/>')
        out.append(text(x + 12, CARD_Y + 132, f"of {total_skills} skills", 9, t["muted"], MONO))
        out.append(text(x + 12, CARD_Y + 148, tag, 9, t["soft"], MONO))

    # Tool strip.
    out.append(f'<line x1="{LEFT}" y1="464" x2="{WIDTH - LEFT}" y2="464" stroke="{t["rule"]}" stroke-width="1"/>')
    out.append(text(LEFT, 496, "INSTALLS INTO", 10, t["soft"], MONO, 500, spacing="0.18em"))
    x = 148
    for tool in TOOLS:
        w = (len(tool) * 7 + 24 + 3) // 4 * 4
        out.append(f'<rect x="{x}" y="480" width="{w}" height="24" rx="4" fill="{t["card"]}" stroke="{t["border"]}" stroke-width="1"/>')
        out.append(text(x + w // 2, 496, tool, 12, t["ink"], SANS, 500, anchor="middle"))
        x += w + 8
    out.append(text(x + 4, 496, "and about 40 more, each in its own format, via rulesync", 12, t["muted"]))
    out.append(text(LEFT, 536, "Per-agent filtering is enforced where the tool supports it: skills, MCP servers and subagents in OpenCode, "
                    "MCP servers in Claude Code.", 12, t["muted"]))
    out.append(text(LEFT, 556, "Other tools get each agent's instructions; install specialist skills there with a folder group.", 12, t["muted"]))
    out.append(text(LEFT, 584, "Counts are skills the model can see, from the default group · generated by agents/generate.py", 10, t["soft"], MONO))
    out.append("</svg>")
    return "\n".join(out) + "\n"
