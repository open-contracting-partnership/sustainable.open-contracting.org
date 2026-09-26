"""
List broken links in the built sites, as CSV on standard output, and exit with 1 if any.

    uv run scripts/check_links.py > broken-links.csv

Build the sites first. A link is broken if its page doesn't exist, or if its fragment isn't an ID on its page. Links to
the three sites' domains are checked against their builds.
"""

import collections
import csv
import html
import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
DOMAINS = {
    "sustainable.open-contracting.org": "en",
    "sostenibilidad.open-contracting.org": "es",
    "achatdurable.open-contracting.org": "fr",
}


def page_file(lang, path):
    """Return the built file of a page, if it exists."""
    file = SITE / lang / path.lstrip("/")
    return next(
        (
            candidate
            for candidate in (file, file.with_name(file.name + ".html"), file / "index.html")
            if candidate.is_file()
        ),
        None,
    )


def broken_links():
    """Return the paths of broken links, by site and path, mapped to the pages that link to them."""
    redirects = {}
    for lang in DOMAINS.values():
        redirects[lang] = {line.split()[0] for line in (SITE / lang / "_redirects").read_text().splitlines() if line}

    broken = collections.defaultdict(set)
    for lang in DOMAINS.values():
        for file in sorted((SITE / lang).rglob("*.html")):
            page = "/" + str(file.relative_to(SITE / lang).with_suffix("")).removesuffix("index")
            for href in re.findall(r'href="([^"]*)"', file.read_text()):
                url = urllib.parse.urlsplit(html.unescape(href))
                if url.scheme in ("http", "https") and url.netloc in DOMAINS:
                    target = DOMAINS[url.netloc]
                elif href.startswith("/") and not href.startswith("//"):
                    target = lang
                else:
                    continue
                path = urllib.parse.unquote(url.path).rstrip("/") or "/"
                if path in redirects[target]:
                    continue
                if not (target_file := page_file(target, path)):
                    broken[(target, path)].add(f"{lang}:{page}")
                # A fragment is an element's ID on the target page, like a heading's.
                elif url.fragment and f'id="{url.fragment}"' not in target_file.read_text():
                    broken[(target, f"{path}#{url.fragment}")].add(f"{lang}:{page}")
    return broken


def main():
    links = broken_links()
    writer = csv.writer(sys.stdout)
    writer.writerow(["site", "path", "linked from"])
    for (lang, path), pages in sorted(links.items()):
        writer.writerow([lang, path, " ".join(sorted(pages))])
    return 1 if links else 0


if __name__ == "__main__":
    sys.exit(main())
