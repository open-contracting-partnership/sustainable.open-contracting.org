"""
List links in the built sites to pages that don't exist, as CSV on standard output.

    python3 scripts/check_links.py > broken-links.csv

Build the sites first. Links to the three sites' domains are checked against their builds.
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


def exists(lang, path, redirects):
    if path in redirects[lang]:
        return True
    file = SITE / lang / path.lstrip("/")
    return any(
        candidate.is_file()
        for candidate in (
            file,
            file.with_name(file.name + ".html"),
            file / "index.html",
        )
    )


def main():
    redirects = {}
    for lang in DOMAINS.values():
        redirects[lang] = {
            line.split()[0]
            for line in (SITE / lang / "_redirects").read_text().splitlines()
            if line
        }

    broken = collections.defaultdict(set)
    for lang in DOMAINS.values():
        for file in sorted((SITE / lang).rglob("*.html")):
            page = "/" + str(
                file.relative_to(SITE / lang).with_suffix("")
            ).removesuffix("index")
            for href in re.findall(r'href="([^"]*)"', file.read_text()):
                url = urllib.parse.urlsplit(html.unescape(href))
                if url.scheme in ("http", "https") and url.netloc in DOMAINS:
                    target = DOMAINS[url.netloc]
                elif href.startswith("/") and not href.startswith("//"):
                    target = lang
                else:
                    continue
                path = urllib.parse.unquote(url.path).rstrip("/") or "/"
                if not exists(target, path, redirects):
                    broken[(target, path)].add(f"{lang}:{page}")

    writer = csv.writer(sys.stdout)
    writer.writerow(["site", "path", "linked from"])
    for (lang, path), pages in sorted(broken.items()):
        writer.writerow([lang, path, " ".join(sorted(pages))])


if __name__ == "__main__":
    main()
