"""Render the README hero image (light and dark SVG) for agents/generate.py.

Three tiers, read top to bottom: the repo's totals, the install groups (global
first, then per folder), and in each group's row the agents it brings. A chip's
number is how many skills only that agent may load; agents without one work
through shared skills or tools. Rows come from groups/*.jsonc and chips wrap,
so a new group adds a row and a new agent adds a chip.

Style: the diagram-design skill's default editorial tokens, except the accent,
which is deep teal. In light mode the small label uses a darker teal so it
passes WCAG AA. Text uses the skill's "system" font stacks, because GitHub shows
README SVGs as images that can't load web fonts. Coordinates sit on a 4 px grid.
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

WIDTH = 1200
RADIUS = 16  # rounded image corners; the README background shows outside them
LEFT = 40
NAME_X, SUMMARY_X, CHIP_X = 40, 232, 384  # columns of a group row
ROW_H, CHIP_H, CHIP_GAP, WRAP_H = 40, 24, 8, 32
SCOPES = {
    "global": ("GLOBAL", "installs for every project · pick one"),
    "folder": ("PER FOLDER", "installs into one folder you choose · add any"),
}


def text(x, y, content, size, color, family=SANS, weight=None, anchor=None, spacing=None):
    attrs = [f'x="{x}"', f'y="{y}"', f'fill="{color}"', f'font-size="{size}"', f'font-family="{family}"']
    if weight:
        attrs.append(f'font-weight="{weight}"')
    if anchor:
        attrs.append(f'text-anchor="{anchor}"')
    if spacing:
        attrs.append(f'letter-spacing="{spacing}"')
    return f'<text {" ".join(attrs)}>{escape(content)}</text>'


def grid(value):
    return (int(value) + 3) // 4 * 4


def chip_width(name, own):
    return grid(len(name) * 7.2 + 20 + (len(str(own)) * 7 + 14 if own else 0))


def summary(group):
    return f"{group['skills']} skills" + (f" · {group['mcp']} MCP" if group["mcp"] else "")


def describe(data):
    repo = data["repo"]
    rows = "; ".join(f"{g['name']} ({summary(g)}): " + (", ".join(a for a, _n in g["agents"]) or "no agents")
                     for g in data["groups"])
    return (f"The repo has {repo['skills']} skills, {repo['agents']} agents you pick, {repo['helpers']} helper agents, "
            f"{repo['mcp']} MCP servers and {repo['plugin_skills']} plugin skills. Groups and the agents they bring: {rows}.")


def render(theme, data):
    t = THEMES[theme]
    label = t.get("label", t["accent"])
    body = []

    # Tier 1: the repo.
    repo = data["repo"]
    body.append(f'<rect x="{LEFT}" y="112" width="{WIDTH - 2 * LEFT}" height="88" rx="8" fill="{t["tint"]}" '
                f'stroke="{t["accent"]}" stroke-width="1.2"/>')
    body.append(text(LEFT + 20, 136, "THE REPO", 10, label, MONO, 500, spacing="0.18em"))
    x = LEFT + 20
    for number, name in [(repo["skills"], "skills"), (repo["agents"], "agents you pick"),
                         (repo["helpers"], "helper agents"), (repo["mcp"], "MCP servers"),
                         (repo["plugin_skills"], "plugin skills")]:
        body.append(text(x, 168, str(number), 28, t["ink"], SERIF))
        x += grid(len(str(number)) * 14 + 8)
        body.append(text(x, 168, name, 12, t["muted"], MONO))
        x += grid(len(name) * 7.4 + 32)
    plugins = " · ".join(f"{title} {count} ({owner})" for title, count, owner in data["plugins"])
    body.append(text(LEFT + 20, 188, f"Plugins install separately: {plugins}", 11, t["muted"], MONO))

    # Tiers 2 and 3: groups, each row with the agents it brings.
    y = 240
    for scope in ("global", "folder"):
        groups = [g for g in data["groups"] if g["scope"] == scope]
        if not groups:
            continue
        caption, sub = SCOPES[scope]
        body.append(text(LEFT, y, caption, 10, label, MONO, 500, spacing="0.18em"))
        body.append(text(LEFT + grid(len(caption) * 9.6 + 12), y, sub, 12, t["muted"]))
        y += 12
        for i, group in enumerate(groups):
            if i:
                body.append(f'<line x1="{LEFT}" y1="{y}" x2="{WIDTH - LEFT}" y2="{y}" stroke="{t["rule"]}" stroke-width="1"/>')
            body.append(text(NAME_X, y + 25, group["name"], 15, t["ink"], MONO, 600))
            body.append(text(SUMMARY_X, y + 25, summary(group), 12, t["muted"], MONO))
            cx, cy = CHIP_X, y + 8
            for name, own in group["agents"]:
                w = chip_width(name, own)
                if cx + w > WIDTH - LEFT:
                    cx, cy = CHIP_X, cy + WRAP_H
                body.append(f'<rect x="{cx}" y="{cy}" width="{w}" height="{CHIP_H}" rx="4" fill="{t["card"]}" '
                            f'stroke="{t["border"]}" stroke-width="1"/>')
                body.append(text(cx + 10, cy + 16, name, 12, t["ink"], SANS, 600))
                if own:
                    body.append(text(cx + w - 10, cy + 16, str(own), 11, label, MONO, 600, anchor="end"))
                cx += w + CHIP_GAP
            if not group["agents"]:
                body.append(text(CHIP_X, cy + 16, "skills only, no agent", 11, t["soft"], MONO))
            y = cy - 8 + ROW_H
        y += 32

    # Key and notes.
    key_w = chip_width("name", "n")
    body.append(f'<rect x="{LEFT}" y="{y - 16}" width="{key_w}" height="{CHIP_H}" rx="4" fill="{t["card"]}" '
                f'stroke="{t["border"]}" stroke-width="1"/>')
    body.append(text(LEFT + 10, y, "name", 12, t["ink"], SANS, 600))
    body.append(text(LEFT + key_w - 10, y, "n", 11, label, MONO, 600, anchor="end"))
    body.append(text(LEFT + key_w + 12, y, "An agent and the skills only it loads. No number: it works through shared "
                     "skills or tools.", 11, t["muted"], MONO))
    y += 28
    body.append(text(LEFT, y, "OpenCode enforces each agent's skill list; other tools get the agent's instructions "
                     "without the filter.", 11, t["soft"], MONO))
    height = grid(y + 28)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}" '
        'role="img" aria-labelledby="hero-title hero-desc">',
        '<title id="hero-title">Pick the groups you want. Each agent brings its own skills.</title>',
        f'<desc id="hero-desc">{escape(describe(data))}</desc>',
        "<defs>",
        f'<pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="0.9" fill="{t["dots"]}"/></pattern>',
        "</defs>",
        f'<rect width="{WIDTH}" height="{height}" rx="{RADIUS}" fill="{t["paper"]}"/>',
        f'<rect width="{WIDTH}" height="{height}" rx="{RADIUS}" fill="url(#dots)" opacity="0.6"/>',
        text(LEFT, 44, "INSTRUCTIONS-UNCLEAR · CONTEXT FILES FOR AI CODING TOOLS", 11, t["soft"], MONO, 500, spacing="0.18em"),
        text(LEFT, 88, "Pick the groups you want. Each agent brings its own skills.", 40, t["ink"], SERIF),
        *body,
        "</svg>",
    ]
    return "\n".join(out) + "\n"
