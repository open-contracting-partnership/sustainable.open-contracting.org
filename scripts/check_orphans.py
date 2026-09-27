"""
List the built sites' pages that no link reaches from the home page, and exit with 1 if any isn't an exception.

    uv run scripts/check_orphans.py

Build the sites first. Links are followed within each site, including links to its domain and its redirects. It also
reports exceptions that match no page, or that match a page that is reachable, so that the list stays current.
"""

import fnmatch
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
# Paths, or patterns of paths, of pages that are unreachable on purpose, until their issues are resolved.
EXCEPTIONS = {
    "en": [],
    "es": [],
    "fr": [
        # The four enabling environment pages to translate (#6).
        "/mise-en-place/accords-cadres",
        "/mise-en-place/interaction-ouverte-avec-les-acteurs-du-march-et-dialogue-comptitif",
        "/mise-en-place/objectifs-spcifiques-et-marchs-rservs",
        "/mise-en-place/seuils-et-secteurs-soumis-une-rglementation-distincte",
    ],
}


def pages(site):
    """Return the site's pages, as {path: file}."""
    result = {}
    for file in site.rglob("*.html"):
        if "pagefind" in file.parts or file.name == "404.html":
            continue
        path = "/" + str(file.relative_to(site).with_suffix("")).removesuffix("index")
        result[path.rstrip("/") or "/"] = file
    return result


def reachable(lang, files):
    """Return the paths of the pages that links reach from the home page."""
    # Each rule is "SOURCE TARGET 301".
    rules = (SITE / lang / "_redirects").read_text().splitlines()
    redirects = dict(line.split()[:2] for line in rules if line.strip())

    seen, todo = {"/"}, ["/"]
    while todo:
        for href in re.findall(r'<a [^>]*href="([^"]+)"', files[todo.pop()].read_text()):
            url = urllib.parse.urlsplit(html.unescape(href))
            if url.scheme in ("http", "https"):
                if DOMAINS.get(url.netloc) != lang:
                    continue
            elif not href.startswith("/") or href.startswith("//"):
                continue
            path = urllib.parse.unquote(url.path).rstrip("/") or "/"
            path = redirects.get(path, path)
            if path in files and path not in seen:
                seen.add(path)
                todo.append(path)
    return seen


def main():
    problems = []
    for lang, exceptions in EXCEPTIONS.items():
        files = pages(SITE / lang)
        seen = reachable(lang, files)
        for pattern in exceptions:
            matched = fnmatch.filter(files, pattern)
            if not matched:
                problems.append(f"{lang}: exception {pattern} matches no page")
            problems.extend(
                f"{lang}: exception {pattern} matches {path}, which is reachable" for path in matched if path in seen
            )
        problems.extend(
            f"{lang}: {path} is unreachable"
            for path in sorted(set(files) - seen)
            if not any(fnmatch.fnmatch(path, pattern) for pattern in exceptions)
        )

    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
