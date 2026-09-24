"""
Write link-fixes.csv: each broken link's path in the built sites, by the language of the pages that link to it, and
a proposed target to review.

    uv run scripts/propose_link_fixes.py

Build the sites first. A target is a path on the linking pages' site (the "from" column), or a URL. It is proposed:

- if the links' text is the title of exactly one non-empty page on that site;
- else, if the linking pages' other versions (English for a Spanish or French page, and Spanish and French for an
  English page, as matched by translations.py) link to the same page's version at the same place in the page;
- else, for an English path, if the English versions of the Spanish and French pages that link to it link to the
  same page at the same place.

Rows already in link-fixes.csv keep their targets, unless no target was proposed. import_pages.py redirects each path
with a target from its own site, and relinks the links to it from other sites. The file has a UTF-8 byte order mark,
so that spreadsheets read it as UTF-8.
"""

import collections
import csv
import difflib
import glob
import html
import json
import re
import urllib.parse
from pathlib import Path

import translations
from check_links import DOMAINS, SITE, broken_links

ROOT = Path(__file__).resolve().parent.parent
CRAWL = ROOT / ".crawl"
FIXES = ROOT / "link-fixes.csv"
HEADER = [
    "from",
    "site",
    "path",
    "target",
    "proposed because",
    "link texts",
    "linked from",
]
# Domains on which the sites' pages have been served, including misspellings in links.
HOSTS = {
    **DOMAINS,
    "openspp.super.site": "en",
    "esp.super.site": "es",
    "fr.super.site": "fr",
    "sustainability.open-contracting.org": "en",
    "sustainable.open-contractring.org": "en",
}


def title_key(title):
    return " ".join(title.split()).casefold()


class Build:
    """The built sites' pages and redirects."""

    def __init__(self):
        self.redirects = {}
        for lang in DOMAINS.values():
            lines = (SITE / lang / "_redirects").read_text().splitlines()
            self.redirects[lang] = dict(
                line.split()[:2] for line in lines if line.startswith("/")
            )

    def exists(self, lang, path):
        file = SITE / lang / path.lstrip("/")
        return (
            path == "/"
            or file.with_name(file.name + ".html").is_file()
            or (file / "index.html").is_file()
        )

    def resolve(self, lang, path):
        """Return the (site, path) of the page that a path serves, following redirects, or None."""
        for _ in range(6):
            if self.exists(lang, path):
                return lang, path
            target = self.redirects[lang].get(path)
            if target is None:
                return None
            url = urllib.parse.urlsplit(target)
            if url.scheme:
                if url.netloc not in DOMAINS:
                    return None
                lang = DOMAINS[url.netloc]
            path = urllib.parse.unquote(url.path).rstrip("/") or "/"
        return None


def crawled_links(url):
    """Return the links in a crawled page's article, in order, as (site, path) or the link itself."""
    parsed = urllib.parse.urlsplit(url)
    file = CRAWL / parsed.netloc / ((parsed.path.strip("/") or "index") + ".html")
    text = file.read_text()
    text = text[text.find("<article") : text.rfind("</article>")]
    lang = DOMAINS[parsed.netloc]
    links = []
    for href in re.findall(r'<a [^>]*href="([^"]*)"', text):
        href = html.unescape(href)
        url = urllib.parse.urlsplit(href)
        if url.scheme in ("http", "https") and url.netloc.lower() in HOSTS:
            site = HOSTS[url.netloc.lower()]
        elif href.startswith("/") and not href.startswith("//"):
            site = lang
        elif url.netloc in ("notion.so", "www.notion.so") and (
            notion_id := re.search(r"([0-9a-f]{32})$", url.path)
        ):
            links.append((lang, "/" + notion_id.group(1)))
            continue
        else:
            links.append(href)
            continue
        links.append((site, urllib.parse.unquote(url.path).rstrip("/") or "/"))
    return links


class Translations:
    """Propose targets from the other versions of the linking pages."""

    def __init__(self, build):
        self.build = build
        self.versions = translations.matches()
        self.english = {
            lang: {
                path: (english, score) for english, (path, score) in versions.items()
            }
            for lang, versions in self.versions.items()
        }
        results = json.loads((CRAWL / "results.json").read_text())
        urls = {
            (DOMAINS[urllib.parse.urlsplit(r["url"]).netloc], r["pageId"]): r["url"]
            for r in results
            if r["status"] == 200 and r["final"].rstrip("/") == r["url"].rstrip("/")
        }
        # Each page's crawled URL, by its site and path.
        self.urls = {}
        for file in glob.glob(str(ROOT / "[efs][nsr]" / "**" / "*.md"), recursive=True):
            front_matter = Path(file).read_text().split("\n---\n", 1)[0]
            lang = Path(file).relative_to(ROOT).parts[0]
            permalink = re.search(r"^permalink: (.*)$", front_matter, re.M).group(1)
            notion_id = re.search(r'^notion_id: "?([0-9a-f]{32})', front_matter, re.M)
            if notion_id and (lang, notion_id.group(1)) in urls:
                self.urls[(lang, permalink)] = urls[(lang, notion_id.group(1))]

    def key(self, link, broken=None):
        """Return a link as its English page, for comparison, or as the broken link."""
        if not isinstance(link, tuple):
            return link
        if link == broken:
            return "broken"
        page = self.build.resolve(*link)
        if page is None:
            return ("missing", *link)
        lang, path = page
        if lang != "en" and path in self.english.get(lang, {}):
            return ("en", self.english[lang][path][0])
        return page

    def version(self, lang, page, other):
        """Return a page's version in another language, with its match's score, or None."""
        if lang == "en":
            return self.versions[other].get(page)
        if other == "en":
            return self.english[lang].get(page)
        return None

    def propose(self, lang, site, path, page):
        """
        Return the target that the other versions of a page imply for its broken link, with the reason, or None.

        The English version is compared with a Spanish or French page, and the Spanish and French versions with an
        English page.
        """
        broken = (site, path)
        if (lang, page) not in self.urls:
            return None
        ours = [
            self.key(link, broken) for link in crawled_links(self.urls[(lang, page)])
        ]
        if "broken" not in ours:
            return None
        proposals = set()
        for other in ["en"] if lang != "en" else ["es", "fr"]:
            version = self.version(lang, page, other)
            if version is None or (other, version[0]) not in self.urls:
                continue
            other_page, page_score = version
            theirs = [
                self.key(link) for link in crawled_links(self.urls[(other, other_page)])
            ]
            # The other version's link at the same place, among the links that the versions share. Links are
            # compared as their English pages.
            target = None
            matcher = difflib.SequenceMatcher(None, ours, theirs, autojunk=False)
            for op, i1, i2, j1, j2 in matcher.get_opcodes():
                if (
                    op in ("equal", "replace")
                    and i2 - i1 == j2 - j1
                    and "broken" in ours[i1:i2]
                ):
                    target = theirs[j1 + ours[i1:i2].index("broken")]
                    break
            if not isinstance(target, tuple) or target[0] != "en":
                continue
            if lang == "en":
                translated, target_score = target[1], None
            elif target[1] in self.versions[lang]:
                translated, target_score = self.versions[lang][target[1]]
            else:
                continue
            scores = [
                score for score in (page_score, target_score) if score is not None
            ]
            confidence = (
                "" if min(scores) >= translations.CONFIDENT else ", check the versions"
            )
            name = {"en": "English", "es": "Spanish", "fr": "French"}[other]
            reason = f"{name} version {other_page} (score {page_score}) links to the version of {translated} here"
            if target_score is not None:
                reason = (
                    f"{name} version {other_page} (score {page_score}) links to {target[1]} here, "
                    f"whose version is {translated} (score {target_score})"
                )
            proposals.add((translated, reason + confidence, target[1]))
        # The versions must agree.
        if len({target for target, _, _ in proposals}) == 1:
            return sorted(proposals)[0]
        return None


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
    with (CRAWL / "super-so-pages.csv").open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            super_pages[row["notion_page_id"].replace("-", "")] = row

    existing = {}
    if FIXES.exists():
        with FIXES.open(encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                row.setdefault("from", row["site"])
                existing[(row["from"], row["site"], row["path"])] = row

    # Links' texts, by the linking page's site and the link's site and path.
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
                        texts[(lang, target, path)].add(text)

    broken = collections.defaultdict(set)
    for (site, path), pages in broken_links().items():
        for page in pages:
            lang, _, page_path = page.partition(":")
            broken[(lang, site, path)].add(page_path)

    build = Build()
    versions = Translations(build)

    # Reviewed fixes are kept, including those whose links are no longer broken.
    rows = [
        [row[key] for key in HEADER]
        for key, row in existing.items()
        if row["target"] and key not in broken
    ]
    proposals = {
        key: {versions.propose(*key, page) for page in pages} - {None}
        for key, pages in broken.items()
    }
    # The English pages that Spanish and French pages' broken links to English paths imply, by path, including links
    # that are fixed (the crawl has the original links).
    english_targets = collections.defaultdict(set)
    linking = {key: pages for key, pages in broken.items()}
    for key, row in existing.items():
        linking.setdefault(key, set(row["linked from"].split()))
    for (lang, site, path), pages in linking.items():
        if lang != "en" and site == "en":
            implied = {versions.propose(lang, site, path, page) for page in pages} - {
                None
            }
            english_targets[path].update(english for _, _, english in implied)

    for key, pages in sorted(broken.items()):
        lang, site, path = key
        link_texts = sorted(texts[key])
        matches = set().union(
            *(titles.get((lang, title_key(text)), set()) for text in link_texts)
        )
        target, because = "", ""
        # The other versions' links are better evidence than a title, which a placeholder can have.
        if len({target for target, _, _ in proposals[key]}) == 1:
            target, because, _ = sorted(proposals[key])[0]
        elif len(matches) == 1:
            target = matches.pop()
            because = "link text is its title"
        elif lang == site == "en" and len(english_targets[path]) == 1:
            target = next(iter(english_targets[path]))
            because = "the English versions of Spanish or French pages with this link link to this target instead"
        elif notion_id := re.fullmatch(r"/([0-9a-f]{32})", path):
            row = super_pages.get(notion_id.group(1))
            because = (
                f"no target: Notion ID of {DOMAINS[row['domain']]} /{row['path']} (renders on Super.so: "
                f"{row['renders_on_super']})"
                if row
                else "no target: Notion ID unknown to Super.so"
            )
        elif proposals[key]:
            because = (
                "no target: the linking pages' English versions imply different targets"
            )
        else:
            because = (
                f"no target: {len(matches)} pages have the link text as their title"
            )
        # A row without a target keeps it, unless no target was proposed (so a cleared proposal stays cleared).
        if key in existing and (
            existing[key]["target"]
            or not existing[key]["proposed because"].startswith("no target")
        ):
            target = existing[key]["target"]
            because = existing[key]["proposed because"]
        rows.append(
            [
                lang,
                site,
                path,
                target,
                because,
                " | ".join(link_texts),
                " ".join(sorted(pages)),
            ]
        )

    with FIXES.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(sorted(rows))
    print(
        f"{sum(bool(row[3]) for row in rows)} of {len(rows)} broken links have a target"
    )


if __name__ == "__main__":
    main()
