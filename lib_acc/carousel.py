"""The preset picker: a carousel of icon cards with category chips.

Plain HTML. javascript/acc_carousel.js handles the clicks in the browser:
chips filter, arrows scroll, and a card writes "name|nonce" into a hidden
textbox, whose change event applies the preset on the Python side. The nonce
makes picking the same preset again (after Reset or a manual edit) count.

Icons come from preset_icons.jpg, one sprite, indexed by preset_icons.json;
a preset without an icon gets a lettered tile instead.
"""

import html
import json
import os

from .reference import _url

SPRITE = "preset_icons.jpg"
SIZE = 72                     # icon size on screen, CSS px (the sprite is 2x)


def _sprite(root):
    path = os.path.join(root, SPRITE)
    try:
        with open(os.path.splitext(path)[0] + ".json", encoding="utf-8") as fh:
            index = json.load(fh)
    except (OSError, ValueError):
        return None, {}
    if not os.path.isfile(path):
        return None, {}
    return _url(path), index


def parse_pick(value):
    """'name|nonce' -> name; '' or anything else -> None."""
    name = (value or "").rsplit("|", 1)[0].strip()
    return name or None


def carousel_html(root, prefix, tab, names, categories, descriptions, display=lambda n: n):
    p = prefix
    url, index = _sprite(root)
    icons = index.get("icons", {})
    cols, rows = index.get("cols", 1), index.get("rows", 1)
    esc = lambda s: html.escape(str(s), quote=True)  # noqa: E731

    cats = list(dict.fromkeys(categories.get(n, "") for n in names))
    chips = [f'<button type="button" class="{p}-chip {p}-on" data-cat="*">All</button>']
    chips += [f'<button type="button" class="{p}-chip" data-cat="{esc(c)}">{esc(c)}</button>' for c in cats if c]

    cards = []
    for n in names:
        label = display(n)
        if url and n in icons:
            i = icons[n]
            style = (f"background-image:url('{esc(url)}');background-size:{cols * SIZE}px {rows * SIZE}px;"
                     f"background-position:-{(i % cols) * SIZE}px -{(i // cols) * SIZE}px")
            icon = f'<span class="{p}-icon" style="{style}"></span>'
        else:
            letters = "".join(w[0] for w in label.split()[:2]).upper() or "?"
            icon = f'<span class="{p}-icon {p}-letters">{esc(letters)}</span>'
        cards.append(
            f'<button type="button" class="{p}-card" data-name="{esc(n)}" data-cat="{esc(categories.get(n, ""))}" '
            f'title="{esc(label)}: {esc(descriptions.get(n, ""))}">{icon}'
            f'<span class="{p}-name">{esc(label)}</span></button>')

    return (
        f'<div class="{p}-car" data-target="{p}_preset_pick_{tab}" data-tab="{tab}">'
        f'<div class="{p}-chips">{"".join(chips)}</div>'
        f'<div class="{p}-row">'
        f'<button type="button" class="{p}-nav" data-dir="-1" aria-label="Previous presets">&#8249;</button>'
        f'<div class="{p}-track">{"".join(cards)}</div>'
        f'<button type="button" class="{p}-nav" data-dir="1" aria-label="More presets">&#8250;</button>'
        f'</div></div>'
    )
