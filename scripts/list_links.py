"""
Write .crawl/links.csv: each link between the sites' pages, with its text, its context and its target's text.

    uv run scripts/list_links.py

Build the sites first. The context is the text of the block (paragraph, list item, table cell, callout, card, etc.)
that contains the link. The target is the page that the link serves, following redirects, with its title,
description and headings. Links in the navbar, breadcrumbs and sidebars are omitted, since they are generated.
"""

import csv
import html
import re
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path

from check_links import DOMAINS, SITE

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".crawl" / "links.csv"
BLOCKS = {"p", "li", "td", "th", "h1", "h2", "h3", "summary", "figcaption"}
# Classes of elements whose text is a block's (callouts' and toggles' texts, and cards).
BLOCK_CLASSES = re.compile(r"\bnotion-(?:callout__content|toggle__summary|collection-card|to-do__title|page)\b")
VOID = {
    "br",
    "img",
    "input",
    "hr",
    "meta",
    "link",
    "path",
    "circle",
    "rect",
    "line",
    "source",
    "wbr",
    "col",
}
SKIP_CLASSES = re.compile(r"\bnotion-(?:navbar|breadcrumb)\b")
HEADER = [
    "site",
    "page",
    "page title",
    "link text",
    "context",
    "href",
    "target site",
    "target",
    "target title",
    "target description",
    "target headings",
]


class Links(HTMLParser):
    """Collect the links in a page's <main>, with the texts of the blocks that contain them."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []  # [tag, is a block, is skipped]
        self.blocks = []  # [texts, links] of open blocks
        self.link = None  # [href, texts] of the open link
        self.links = []
        self.main = False

    def skipping(self):
        return any(skipped for _, _, skipped in self.stack)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "main":
            self.main = True
        if self.main and tag == "br" and self.blocks:
            self.blocks[-1][0].append(" ")
        if not self.main or tag in VOID:
            return
        cls = attrs.get("class") or ""
        skipped = bool(SKIP_CLASSES.search(cls)) or "data-pagefind-ignore" in attrs
        block = tag in BLOCKS or bool(BLOCK_CLASSES.search(cls))
        self.stack.append([tag, block, skipped])
        if block:
            self.blocks.append([[], []])
        if tag == "a" and attrs.get("href") and not self.skipping():
            self.link = [attrs["href"], []]

    def handle_endtag(self, tag):
        if not self.main or tag in VOID:
            return
        if tag == "main":
            self.main = False
            return
        while self.stack:
            open_tag, block, _ = self.stack.pop()
            if open_tag == "a" and self.link:
                href, texts = self.link
                record = {"href": href, "link text": " ".join("".join(texts).split())}
                if self.blocks:
                    self.blocks[-1][1].append(record)
                else:
                    record["context"] = record["link text"]
                    self.links.append(record)
                self.link = None
            if block:
                texts, links = self.blocks.pop()
                context = " ".join("".join(texts).split())
                for record in links:
                    record["context"] = context
                    self.links.append(record)
                # The block's text is also its parent block's.
                if self.blocks:
                    self.blocks[-1][0].extend(texts)
            if open_tag == tag:
                break

    def handle_data(self, data):
        if not self.main or self.skipping():
            return
        if self.blocks:
            self.blocks[-1][0].append(data)
        if self.link:
            self.link[1].append(data)


def pages():
    """Return each page's title, description and headings, by site and path."""
    result = {}
    for lang in DOMAINS.values():
        for file in (ROOT / lang).rglob("*.md"):
            front_matter, body = file.read_text().split("\n---\n", 1)

            def get(key, front_matter=front_matter):
                match = re.search(rf"^{key}: (.*)$", front_matter, re.MULTILINE)
                return html.unescape(match.group(1).strip('"')) if match else ""

            headings = [
                re.sub(r"[*_`]", "", line.lstrip("#").strip())
                for line in body.splitlines()
                if re.match(r"#{1,3} ", line)
            ]
            result[(lang, get("permalink"))] = (
                get("title"),
                get("description"),
                " | ".join(headings),
            )
    return result


def main():
    redirects = {}
    for lang in DOMAINS.values():
        lines = (SITE / lang / "_redirects").read_text().splitlines()
        redirects[lang] = dict(line.split()[:2] for line in lines if line.startswith("/"))
    info = pages()

    def resolve(lang, path):
        for _ in range(6):
            if (lang, path) in info:
                return lang, path
            target = redirects[lang].get(path)
            if target is None:
                return None
            url = urllib.parse.urlsplit(target)
            if url.scheme:
                if url.netloc not in DOMAINS:
                    return None
                lang = DOMAINS[url.netloc]
            path = urllib.parse.unquote(url.path).rstrip("/") or "/"
        return None

    rows = []
    for lang in DOMAINS.values():
        for file in sorted((SITE / lang).rglob("*.html")):
            if "pagefind" in file.parts or file.name == "404.html":
                continue
            page = "/" + str(file.relative_to(SITE / lang).with_suffix("")).removesuffix("index")
            page = page.rstrip("/") or "/"
            parser = Links()
            parser.feed(file.read_text())
            for record in parser.links:
                url = urllib.parse.urlsplit(html.unescape(record["href"]))
                if url.scheme in ("http", "https") and url.netloc in DOMAINS:
                    site = DOMAINS[url.netloc]
                elif record["href"].startswith("/") and not record["href"].startswith(("//", "/assets/")):
                    site = lang
                else:
                    continue
                path = urllib.parse.unquote(url.path).rstrip("/") or "/"
                target = resolve(site, path)
                title, description, headings = info.get(target, ("", "", "")) if target else ("", "", "")
                rows.append(
                    [
                        lang,
                        page,
                        info.get((lang, page), ("",))[0],
                        record["link text"],
                        record["context"],
                        record["href"],
                        target[0] if target else site,
                        target[1] if target else f"(broken) {path}",
                        title,
                        description,
                        headings,
                    ]
                )

    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(rows)
    print(len(rows), "links written to", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
