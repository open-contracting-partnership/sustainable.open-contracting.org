"""
List problems with the pages and the built sites, and exit with 1 if any.

    uv run scripts/check_pages.py

Build the sites with scripts/build.sh first. It reports:

- pages whose permalink isn't their file's path, or isn't unique, or that have no title
- covers and icons in front matter that aren't files
- references to /assets/ in the built pages that aren't files
- files in /assets/ that no site's pages, stylesheets or templates refer to
- URLs in the sitemap that aren't built pages
- a search index that doesn't have every page that it should (those with data-pagefind-body)
"""

import json
import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
LANGUAGES = ("en", "es", "fr")
# A path, or a URL on one of the sites' domains, like a social media image.
ASSET = re.compile(
    r"""(?:src|href|content)=["'](?:https://(?:sustainable|sostenibilidad|achatdurable)\.open-contracting\.org)?(/assets/[^"'#?]+)"""
)


def front_matter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    return m[1] if m else None


def value(front, key):
    m = re.search(rf"^{key}: *(.*)$", front, re.MULTILINE)
    return m[1].strip().strip("\"'") if m else None


def built(lang, url_path):
    path = SITE / lang / urllib.parse.unquote(url_path).lstrip("/")
    return any(p.is_file() for p in (path, path.with_name(path.name + ".html"), path / "index.html"))


def stylesheet_references(site):
    """Return the paths of the files that a built site's stylesheets refer to, including their sourcemaps."""
    for css in (site / "assets").rglob("*.css"):
        text = css.read_text()
        for match in [*re.findall(r"url\(([^)]+)\)", text), *re.findall(r"sourceMappingURL=(\S+)", text)]:
            url = match.strip("\"'")
            if not url.startswith(("data:", "http", "#")):
                yield "/" + str((css.parent / url).resolve().relative_to(site.resolve()))


def main():
    problems = []
    # Templates' references count, like analytics.js, which only production builds use.
    used = {ref for path in ROOT.glob("_[il]*/*.html") for ref in ASSET.findall(path.read_text())}
    assets = set()
    for lang in LANGUAGES:
        permalinks = {}
        for path in sorted((ROOT / lang).rglob("*.md")):
            relative = path.relative_to(ROOT)
            front = front_matter(path.read_text())
            if front is None:
                problems.append(f"{relative}: no front matter")
                continue
            permalink = value(front, "permalink")
            expected = "/" + str(path.relative_to(ROOT / lang).with_suffix(""))
            expected = "/" if expected == "/index" else expected
            if permalink != expected:
                problems.append(f"{relative}: permalink {permalink} isn't {expected}")
            if permalink in permalinks:
                problems.append(f"{relative}: permalink {permalink} is also {permalinks[permalink]}'s")
            permalinks[permalink] = relative
            if not value(front, "title"):
                problems.append(f"{relative}: no title")
            # An icon can also be an emoji.
            problems.extend(
                f"{relative}: {key} {asset} isn't a file"
                for key in ("cover", "icon")
                if (asset := value(front, key))
                and asset.startswith("/")
                and not (ROOT / urllib.parse.unquote(asset).lstrip("/")).is_file()
            )

        site = SITE / lang
        if not site.is_dir():
            problems.append(f"_site/{lang}: not built")
            continue
        missing = set()
        searchable = 0
        for page in site.rglob("*.html"):
            html = page.read_text()
            searchable += "data-pagefind-body" in html
            for ref in ASSET.findall(html):
                used.add(urllib.parse.unquote(ref))
                if not (site / urllib.parse.unquote(ref).lstrip("/")).is_file():
                    missing.add((ref, str(page.relative_to(SITE))))
        used.update(stylesheet_references(site))
        assets.update("/" + str(path.relative_to(site)) for path in (site / "assets").rglob("*") if path.is_file())
        for ref, page in sorted(missing):
            problems.append(f"{page}: {ref} isn't a file")
        problems.extend(
            f"_site/{lang}/sitemap.xml: {loc} isn't a page"
            for loc in re.findall(r"<loc>([^<]+)</loc>", (site / "sitemap.xml").read_text())
            if not built(lang, urllib.parse.urlparse(loc).path)
        )
        entry = site / "pagefind" / "pagefind-entry.json"
        if not entry.is_file():
            problems.append(f"_site/{lang}: no search index (build with scripts/build.sh)")
        else:
            count = sum(language["page_count"] for language in json.loads(entry.read_text())["languages"].values())
            if count != searchable or not count:
                problems.append(f"_site/{lang}: the search index has {count} pages, not {searchable}")

    problems.extend(f"_site: {asset} isn't used by any site" for asset in sorted(assets - used))

    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
