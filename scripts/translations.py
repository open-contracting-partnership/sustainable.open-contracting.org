"""
Match each English page to its likely Spanish and French versions.

Notion doesn't record which page translates which, so pages are matched by what translations share: their titles
(for database items, whose titles aren't translated), icons, covers, images, external links, numbers and the blocks
they use. Each page matches at most one page, best scores first. Scores below CONFIDENT are uncertain, since similar
sibling pages can be confused.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIDENT = 6
BLOCKS = (
    "{% toggle",
    "{% callout",
    "{% table",
    "{% image",
    "{% gallery",
    "{% database",
    "```",
    "{% columns",
)
LINK = re.compile(
    r"https?://(?!(?:sustainable|sostenibilidad|achatdurable)\.open-contracting\.org)[^\s\"')>\]|]+"
)
NUMBER = re.compile(r"(?<![\w/.-])\d+(?:[.,]\d+)*(?![\w/-])")


def features(file):
    """Return a page's features, from its Markdown file."""
    front_matter, body = file.read_text().split("\n---\n", 1)

    def get(key):
        match = re.search(rf"^{key}: (.*)$", front_matter, re.M)
        return match and match.group(1).strip('"')

    text = re.sub(r"\{%.*?%\}|\(http[^)]*\)|<[^>]+>", " ", body)
    return {
        "path": get("permalink"),
        "title": get("title"),
        "icon": get("icon"),
        "cover": get("cover"),
        "empty": not body.strip(),
        "images": set(re.findall(r"/assets/(?:images|super)/[^\s\"')]+", body)),
        "links": set(LINK.findall(body)),
        "numbers": set(NUMBER.findall(text)),
        "blocks": [body.count(block) for block in BLOCKS],
    }


def jaccard(a, b):
    return len(a & b) / len(a | b) if a or b else 0


def score(a, b):
    """Return how likely two pages are translations of each other."""
    total = 0.0
    if a["title"] and a["title"].casefold() == (b["title"] or "").casefold():
        total += 3
    total += 1.5 * (a["icon"] is not None and a["icon"] == b["icon"])
    # Many pages share the default background cover.
    total += 0.5 * (
        a["cover"] is not None
        and a["cover"] == b["cover"]
        and "background" not in a["cover"]
    )
    total += 3 * jaccard(a["images"], b["images"])
    total += 3 * jaccard(a["links"], b["links"])
    total += 3 * jaccard(a["numbers"], b["numbers"])
    if any(a["blocks"]) or any(b["blocks"]):
        difference = sum(abs(x - y) for x, y in zip(a["blocks"], b["blocks"]))
        total += 1 - difference / (sum(a["blocks"]) + sum(b["blocks"]))
    return total


def matches():
    """Return each language's versions of English pages, as {lang: {english path: (path, score)}}."""
    pages = {
        lang: [features(file) for file in sorted((ROOT / lang).rglob("*.md"))]
        for lang in ("en", "es", "fr")
    }
    result = {}
    for lang in ("es", "fr"):
        candidates = sorted(
            (
                (score(a, b), a["path"], b["path"])
                for a in pages["en"]
                for b in pages[lang]
            ),
            reverse=True,
        )
        matched, used = {}, set()
        for value, english, other in candidates:
            if value >= 3 and english not in matched and other not in used:
                matched[english] = (other, round(value, 2))
                used.add(other)
        result[lang] = matched
    return result
