"""
Match each English page to its likely Spanish and French versions.

Notion doesn't record which page translates which, so pages are matched by what translations share: their titles
(for database items, whose titles aren't translated), icons, covers, images, external links, numbers, the blocks they
use and their order, and the pages they link to (as matched by a first pass without them). Each page matches at most
one page, best scores first. Scores below CONFIDENT are uncertain, since similar sibling pages can be confused.
"""

import difflib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIDENT = 6
# Pages with lower scores aren't matched.
MINIMUM = 3
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
LINK = re.compile(r"https?://(?!(?:sustainable|sostenibilidad|achatdurable)\.open-contracting\.org)[^\s\"')>\]|]+")
NUMBER = re.compile(r"(?<![\w/.-])\d+(?:[.,]\d+)*(?![\w/-])")
# Links to pages on the same site: Markdown links, page tags, gallery cards, table views' items and HTML links.
INTERNAL = re.compile(
    r"\]\((/[^)\s]*)\)|\{% page (/\S*)|^\s*link: \"?(/[^\"\s]*)|^\s+- (/\S*)$|href=\"(/(?!assets/)[^\"#?]*)",
    re.MULTILINE,
)


def order(body):
    """Return the kinds of a page's blocks, in order, with consecutive paragraphs and list items as one."""
    kinds = []
    code = False
    for raw in body.splitlines():
        line = raw.strip()
        if line.startswith("```"):
            code = not code
            if code:
                kinds.append("code")
            continue
        if code or not line:
            continue
        if match := re.match(r"\{% (\w+)", line):
            kind = match.group(1)
            if kind.startswith("end") or kind == "column":
                continue
        elif match := re.match(r"(#+) ", line):
            kind = "h" + str(len(match.group(1)))
        elif line.startswith("- [ ]"):
            kind = "todo"
        elif re.match(r"(?:[-*]|\d+\.) ", line):
            kind = "list"
        elif line == "---":
            kind = "divider"
        elif line.startswith("<"):
            kind = "html"
        else:
            kind = "text"
        if not kinds or kinds[-1] != kind or kind in ("toggle", "callout", "image", "page"):
            kinds.append(kind)
    return kinds


def features(file):
    """Return a page's features, from its Markdown file."""
    front_matter, body = file.read_text().split("\n---\n", 1)

    def get(key):
        match = re.search(rf"^{key}: (.*)$", front_matter, re.MULTILINE)
        return match and match.group(1).strip('"')

    text = re.sub(r"\{%.*?%\}|\(http[^)]*\)|<[^>]+>", " ", body)
    return {
        "path": get("permalink"),
        "title": get("title"),
        "icon": get("icon"),
        "cover": get("cover"),
        "empty": not body.strip(),
        "images": set(re.findall(r"/assets/(?:images|files)/[^\s\"')]+", body)),
        "links": set(LINK.findall(body)),
        "numbers": set(NUMBER.findall(text)),
        "blocks": [body.count(block) for block in BLOCKS],
        "order": order(body),
        "internal": {(next(group for group in match if group).rstrip("/") or "/") for match in INTERNAL.findall(body)},
    }


def jaccard(a, b):
    return len(a & b) / len(a | b) if a or b else 0


def score(a, b, english=None):
    """
    Return how likely two pages are translations of each other.

    ``english`` maps the second page's language's paths to their English versions, to compare the pages' links.
    """
    total = 0.0
    if a["title"] and a["title"].casefold() == (b["title"] or "").casefold():
        total += 3
    total += 1.5 * (a["icon"] is not None and a["icon"] == b["icon"])
    # Many pages share the default background cover.
    total += 0.5 * (a["cover"] is not None and a["cover"] == b["cover"] and "background" not in a["cover"])
    total += 3 * jaccard(a["images"], b["images"])
    total += 3 * jaccard(a["links"], b["links"])
    total += 3 * jaccard(a["numbers"], b["numbers"])
    if any(a["blocks"]) or any(b["blocks"]):
        difference = sum(abs(x - y) for x, y in zip(a["blocks"], b["blocks"], strict=True))
        total += 1 - difference / (sum(a["blocks"]) + sum(b["blocks"]))
    if len(a["order"]) > 1 and len(b["order"]) > 1:
        total += 1.5 * difflib.SequenceMatcher(None, a["order"], b["order"], autojunk=False).ratio()
    if english is not None:
        total += 3 * jaccard(a["internal"], {english.get(path, path) for path in b["internal"]})
    return total


def matches():
    """Return each language's versions of English pages, as {lang: {english path: (path, score)}}."""
    pages = {lang: [features(file) for file in sorted((ROOT / lang).rglob("*.md"))] for lang in ("en", "es", "fr")}
    result = {}
    for lang in ("es", "fr"):
        english = None
        # The second pass compares the pages' links, as matched by the first.
        for _ in range(2):
            candidates = sorted(
                ((score(a, b, english), a["path"], b["path"]) for a in pages["en"] for b in pages[lang]),
                reverse=True,
            )
            matched, used = {}, set()
            for value, path, other in candidates:
                if value >= MINIMUM and path not in matched and other not in used:
                    matched[path] = (other, round(value, 2))
                    used.add(other)
            english = {other: path for path, (other, _) in matched.items()}
        result[lang] = matched
    return result
