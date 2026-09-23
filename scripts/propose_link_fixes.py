"""
Write link-fixes.csv: each broken link's path in the built sites, and a proposed target to review.

    uv run scripts/propose_link_fixes.py

Build the sites first. A target is proposed if the links' text is the title of exactly one non-empty page on the
same site. Rows already in link-fixes.csv keep their targets. import_pages.py redirects each path with a target, and
relinks its links.
"""

import collections
import csv
import glob
import html
import re
import urllib.parse
from pathlib import Path

from check_links import DOMAINS, SITE, broken_links

ROOT = Path(__file__).resolve().parent.parent
FIXES = ROOT / "link-fixes.csv"
HEADER = ["site", "path", "target", "proposed because", "link texts", "linked from"]


def title_key(title):
    return " ".join(title.split()).casefold()


def main():
    titles = collections.defaultdict(set)
    for file in glob.glob(str(ROOT / "[efs][nsr]" / "**" / "*.md"), recursive=True):
        front_matter, body = Path(file).read_text().split("\n---\n", 1)
        # Empty pages are placeholders for database items.
        if not body.strip():
            continue
        title = re.search(r"^title: (.*)$", front_matter, re.M).group(1)
        title = html.unescape(title.strip('"'))
        permalink = re.search(r"^permalink: (.*)$", front_matter, re.M).group(1)
        titles[(Path(file).relative_to(ROOT).parts[0], title_key(title))].add(permalink)

    # Pages that Super.so lists, by Notion ID, to describe links to Notion IDs.
    super_pages = {}
    with (ROOT / ".crawl" / "super-so-pages.csv").open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            super_pages[row["notion_page_id"].replace("-", "")] = row

    existing = {}
    if FIXES.exists():
        with FIXES.open() as f:
            existing = {(row["site"], row["path"]): row for row in csv.DictReader(f)}

    texts = collections.defaultdict(set)
    for lang in DOMAINS.values():
        for file in sorted((SITE / lang).rglob("*.html")):
            for match in re.finditer(
                r'<a href="([^"]*)"[^>]*>(.*?)</a>', file.read_text(), re.S
            ):
                url = urllib.parse.urlsplit(html.unescape(match.group(1)))
                target = DOMAINS.get(url.netloc) if url.scheme else lang
                if target:
                    path = urllib.parse.unquote(url.path).rstrip("/") or "/"
                    text = html.unescape(re.sub(r"<[^>]*>", "", match.group(2))).strip()
                    if text:
                        texts[(target, path)].add(text)

    broken = broken_links()
    # Reviewed fixes are kept, including those whose links are no longer broken.
    rows = [
        [row[key] for key in HEADER]
        for key, row in existing.items()
        if row["target"] and key not in broken
    ]
    for (lang, path), pages in sorted(broken.items()):
        link_texts = sorted(texts[(lang, path)])
        matches = set().union(
            *(titles.get((lang, title_key(text)), set()) for text in link_texts)
        )
        target, because = "", ""
        if len(matches) == 1:
            target = matches.pop()
            because = "link text is its title"
        elif notion_id := re.fullmatch(r"/([0-9a-f]{32})", path):
            row = super_pages.get(notion_id.group(1))
            because = (
                f"no target: Notion ID of {DOMAINS[row['domain']]} /{row['path']} (renders on Super.so: "
                f"{row['renders_on_super']})"
                if row
                else "no target: Notion ID unknown to Super.so"
            )
        else:
            because = (
                f"no target: {len(matches)} pages have the link text as their title"
            )
        if (lang, path) in existing:
            target = existing[(lang, path)]["target"]
            because = existing[(lang, path)]["proposed because"]
        rows.append(
            [
                lang,
                path,
                target,
                because,
                " | ".join(link_texts),
                " ".join(sorted(pages)),
            ]
        )

    with FIXES.open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(sorted(rows))
    print(
        f"{sum(bool(row[2]) for row in rows)} of {len(rows)} broken links have a target"
    )


if __name__ == "__main__":
    main()
