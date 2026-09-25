# /// script
# dependencies = []
# ///
"""
List problems in each site's _redirects, and exit with 1 if any.

    uv run scripts/check_redirects.py

It reports lines that aren't "SOURCE TARGET 301", duplicate sources, sources that are pages (which Cloudflare Pages
serves instead), targets that are redirects (chains and loops) or that aren't pages, and more rules than Cloudflare
Pages allows.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGUAGES = ("en", "es", "fr")
# Cloudflare Pages' limit on static redirects.
LIMIT = 2000


def permalinks(lang):
    paths = set()
    for path in (ROOT / lang).rglob("*.md"):
        if m := re.search(r"^permalink: (.*)$", path.read_text(), re.MULTILINE):
            paths.add(m[1])
    return paths


def main():
    count = 0

    def report(lang, number, message):
        nonlocal count
        count += 1
        print(f"{lang}/_redirects:{number}: {message}")

    for lang in LANGUAGES:
        pages = permalinks(lang)
        text = (ROOT / lang / "_redirects").read_text()
        _, front_matter, body = text.split("---\n", 2)
        offset = front_matter.count("\n") + 2
        rules = {}
        for number, line in enumerate(body.splitlines(), offset + 1):
            if not line.strip():
                continue
            match line.split():
                case [source, target, "301"] if source.startswith("/"):
                    pass
                case _:
                    report(lang, number, f"not SOURCE TARGET 301: {line!r}")
                    continue
            if source in rules:
                report(lang, number, f"duplicate source: {source}")
            if source in pages:
                report(lang, number, f"source is a page: {source}")
            rules[source] = (target, number)
        if len(rules) > LIMIT:
            report(lang, len(rules), f"{len(rules)} rules, more than {LIMIT}")
        for source, (target, number) in rules.items():
            if target.startswith(("http://", "https://")):
                continue
            path = target.split("#", 1)[0].split("?", 1)[0]
            if path in rules:
                report(
                    lang,
                    number,
                    f"redirect to a redirect: {source} -> {target} -> {rules[path][0]}",
                )
            elif path not in pages:
                report(lang, number, f"target isn't a page: {source} -> {target}")
    return 1 if count else 0


if __name__ == "__main__":
    sys.exit(main())
