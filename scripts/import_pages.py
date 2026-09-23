"""Convert the crawled Super.so pages in .crawl/ into Jekyll pages in en/, es/ and fr/."""

import collections
import csv
import html
import json
import re
import shutil
import urllib.parse
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
CRAWL = ROOT / ".crawl"
IMAGES = json.loads((CRAWL / "images.json").read_text())
SITES = {
    "sustainable.open-contracting.org": "en",
    "sostenibilidad.open-contracting.org": "es",
    "achatdurable.open-contracting.org": "fr",
}

IMAGE = re.compile(
    r"https://images\.spr\.so/cdn-cgi/imagedelivery/[^/]+/([^/]+)/[^/\"\s]+/[^\"\s]*"
)
NEXT_IMAGE = re.compile(r"/_next/image\?url=([^&\"]+)(?:&amp;|&)w=\d+(?:&amp;|&)q=\d+")
SUPER_ASSET = re.compile(r"https://assets\.super\.so/")
MAIN = re.compile(r'<main id="([^"]*)" class="([^"]*)">(.*)</main>', re.S)
STYLE = re.compile(r"<style>(.*?)</style>", re.S)
HREF = re.compile(r'href="([^"]*)"')
SPACER = re.compile(r'<div (?:id="[^"]*" )?class="notion-text"></div>')
# Domains on which the sites' pages have been served, including misspellings in links.
LINK_HOSTS = {
    **SITES,
    "openspp.super.site": "en",
    "esp.super.site": "es",
    "fr.super.site": "fr",
    "sustainability.open-contracting.org": "en",
    "sustainable.open-contractring.org": "en",
}
DOMAINS = {lang: host for host, lang in SITES.items()}
SIDEBAR = re.compile(r'<div id="[^"]*" class="notion-column"(?: style="[^"]*")?>')


def crawled_path(url):
    parsed = urllib.parse.urlparse(url)
    return CRAWL / parsed.netloc / ((parsed.path.strip("/") or "index") + ".html")


def image_path(match):
    return urllib.parse.quote(IMAGES[match.group(1)])


def localize(text):
    text = NEXT_IMAGE.sub(lambda m: urllib.parse.unquote(m.group(1)), text)
    text = IMAGE.sub(image_path, text)
    return SUPER_ASSET.sub("/assets/super/", text)


def clean(text):
    """Remove markup that only Super.so's JavaScript uses."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(
        r' (?:data-server-link|data-link-uri|data-full-size|data-lightbox-src|data-nimg|decoding)="[^"]*"',
        "",
        text,
    )
    text = re.sub(r'<span style="display:contents">(<img [^>]*>)</span>', r"\1", text)
    text = re.sub(r'<span class="notion-heading__anchor" id="[^"]*"></span>', "", text)
    text = re.sub(r"<img [^>]*>", clean_image, text)
    # Remove newlines at the end of text blocks.
    inline_end = r"(?:</(?:strong|em|a|span)>)*"
    text = re.sub(rf"\n+({inline_end}</(?:p|li|h[1-6])>)", r"\1", text)
    text = re.sub(
        rf"\n+({inline_end}</span>)(?=</div>|<(?:div|p|ul|ol|h[1-6])[ >])", r"\1", text
    )
    return text


def fix_spaces(text, lang):
    """Replace non-breaking spaces with spaces, except where typography requires them (in numbers and in French)."""

    def replace(match):
        before = text[match.start() - 1 : match.start()]
        after = text[match.end() : match.end() + 1]
        if before.isdigit() and after.isdigit():
            return match.group(0)
        if lang == "fr" and (
            after in ":;!?»" or before == "«" or (before.isdigit() and after.isalpha())
        ):
            return match.group(0)
        return " "

    text = re.sub(" ? + ?", lambda m: m.group(0) if m.group(0) == " " else " ", text)
    return re.sub(" ", replace, text)


def fix_text_spaces(content, lang):
    """Apply ``fix_spaces`` to the text of HTML, not its tags."""
    return "".join(
        token if token.startswith("<") else fix_spaces(token, lang)
        for token in TOKEN.findall(content)
    )


def clean_image(match):
    tag = match.group(0)
    src = re.search(r' src="([^"]*)"', tag).group(1)
    srcset = re.search(r' srcSet="([^"]*)"', tag)
    if srcset and all(
        entry.split(" ")[0] == src for entry in srcset.group(1).split(", ")
    ):
        tag = re.sub(r' (?:srcSet|sizes)="[^"]*"', "", tag)
    tag = re.sub(r"color:transparent;?", "", tag)
    return tag.replace(' style=""', "")


BLOCK = {
    "article",
    "aside",
    "blockquote",
    "details",
    "div",
    "figcaption",
    "figure",
    "h1",
    "h2",
    "h3",
    "h4",
    "hr",
    "iframe",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "summary",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
}
VOID = {"br", "hr", "img", "input", "meta", "link", "source", "col", "wbr"}
# Elements in which whitespace is significant (white-space: pre or pre-wrap), or not worth indenting.
PRESERVE = re.compile(
    r'^<(?:pre|code|svg)\b|class="[^"]*\b(?:notion-semantic-string|notion-header__title|notion-code)\b'
)
TOKEN = re.compile(r"<[^>]*>|[^<]+")
# Inline elements that the stylesheets display as blocks (a.notion-page is display: flex).
BLOCK_CLASS = re.compile(r'class="[^"]*\bnotion-page\b(?!_)')


def indent(text):
    """Put block elements on their own lines, without changing whitespace that renders."""
    output = []
    stack = []  # [preserve whitespace, has a child on its own line]
    for token in TOKEN.findall(text):
        preserving = bool(stack) and stack[-1][0]
        if token.startswith("</"):
            element = stack.pop()
            if element[1]:
                output.append("\n" + "  " * len(stack))
            output.append(token)
        elif token.startswith("<"):
            name = re.match(r"<([a-zA-Z0-9]+)", token).group(1).lower()
            if (name in BLOCK or BLOCK_CLASS.search(token)) and not preserving:
                output.append("\n" + "  " * len(stack))
                if stack:
                    stack[-1][1] = True
            output.append(token)
            if name not in VOID and not token.endswith("/>"):
                stack.append([preserving or bool(PRESERVE.search(token)), False])
        else:
            output.append(token)
    return "".join(output).strip()


def element_end(text, start):
    """Return the index after the end of the element that starts at ``start``."""
    name = re.match(r"<([a-z0-9]+)", text[start:]).group(1)
    depth = 0
    for match in re.compile(rf"<(/?){name}\b[^>]*>").finditer(text, start):
        depth += -1 if match.group(1) else 1
        if depth == 0:
            return match.end()
    raise ValueError(f"unclosed <{name}>")


def parse_page(content):
    """Move the navbar, header and article element into front matter, and return it and the article's content."""
    content = content[
        element_end(content, content.index('<nav class="notion-navbar">')) :
    ]

    start = content.index('<div class="notion-header ')
    header = content[start : element_end(content, start)]
    data = {}
    if cover := re.search(
        r'class="notion-header__cover-image" style="[^"]*object-position:center ([^;"]*)%;?" src="([^"]*)"',
        header,
    ):
        data["cover"] = cover.group(2)
        if (position := round(float(cover.group(1)), 2)) != 50:
            data["cover_position"] = position
    if icon := re.search(r'class="notion-header__icon" [^>]*src="([^"]*)"', header):
        data["icon"] = icon.group(1)

    article = re.search(r'<article [^>]*class="notion-root ([^" ]+)[^"]*">', content)
    if article.group(1) == "full-width":
        data["full_width"] = True
    if 'class="notion-header collection"' in header:
        data["collection"] = True
    start = article.start()
    end = element_end(content, start)
    return data, content[article.end() : end - len("</article>")]


def sidebar(content):
    """Return the content of the first column, if it starts with a link to the homepage."""
    match = SIDEBAR.search(content)
    if match and re.match(r'<a (?:id="[^"]*" )?href="/"', content[match.end() :]):
        return content[
            match.end() : element_end(content, match.start()) - len("</div>")
        ]
    return None


def rewrite_link(match, lang, live, redirects, counter):
    """
    Make a link to a site's page relative (or absolute to its domain), skipping any redirect.

    Add a redirect for a link to a page that doesn't exist, if a live page clearly replaces it.
    """
    href = html.unescape(match.group(1))
    url = urllib.parse.urlsplit(href)
    if url.scheme in ("http", "https") and url.netloc.lower() in LINK_HOSTS:
        target = LINK_HOSTS[url.netloc.lower()]
        kind = "absolute"
    elif href.startswith("/") and not href.startswith(("//", "/assets/")):
        target = lang
        kind = "relative"
    else:
        return match.group(0)
    path = urllib.parse.unquote(url.path).rstrip("/") or "/"
    path = redirects[target].get(path, path)
    if path not in live[target] and (moved := moved_to(path, live[target])):
        redirects[target][path] = moved
        path = moved
    new = urllib.parse.urlunsplit(
        ("", "", urllib.parse.quote(path), url.query, url.fragment)
    )
    if target != lang:
        new = f"https://{DOMAINS[target]}{new}"
    if new != href:
        counter[
            f"{kind} {'to another site' if target != lang else 'made relative' if kind == 'absolute' else 'redirected'}"
        ] += 1
    return f'href="{html.escape(new)}"'


def moved_to(source, live):
    """
    Return the live page with the same final path segment (ignoring case) as a missing page, if clear.

    Prefer the page that shares more of the path, then the only page with incoming links, since the others are
    unlinked duplicates (``live`` maps paths to numbers of incoming links).
    """
    segments = set(source.lower().split("/")[:-1])
    ranked = sorted(
        (
            (len(segments & set(path.split("/")[:-1])), bool(incoming), path)
            for path, incoming in live.items()
            if path.split("/")[-1] == source.split("/")[-1].lower()
        ),
        reverse=True,
    )
    if len(ranked) == 1 or (len(ranked) > 1 and ranked[0][:2] != ranked[1][:2]):
        return ranked[0][2]
    return None


def meta(head, attribute, name):
    match = re.search(rf'<meta {attribute}="{name}" content="([^"]*)"', head)
    return match and html.unescape(match.group(1))


def front_matter(data):
    return (
        "---\n"
        + "".join(
            f"{key}: {json.dumps(value, ensure_ascii=False)}\n"
            for key, value in data.items()
        )
        + "---\n"
    )


def main():
    results = json.loads((CRAWL / "results.json").read_text())
    ok = [
        r
        for r in results
        if r["status"] == 200 and r["pageId"] and r["url"].startswith("https://")
    ]
    canonical = [r for r in ok if r["final"].rstrip("/") == r["url"].rstrip("/")]

    for lang in SITES.values():
        shutil.rmtree(ROOT / lang, ignore_errors=True)

    slugs = {}
    for r in canonical:
        lang = SITES[urllib.parse.urlparse(r["url"]).netloc]
        slugs[(lang, r["pageId"])] = (
            urllib.parse.urlparse(r["url"]).path.rstrip("/") or "/"
        )

    # Each live page's number of incoming links on its site, other than breadcrumbs (from itself and its descendants).
    live_paths = {lang: {} for lang in SITES.values()}
    for (lang, _), path in slugs.items():
        live_paths[lang][path] = 0
    for r in canonical:
        lang = SITES[urllib.parse.urlparse(r["url"]).netloc]
        source = urllib.parse.urlparse(r["url"]).path.rstrip("/") or "/"
        for link in r["links"]:
            url = urllib.parse.urlsplit(link)
            if url.netloc in ("", DOMAINS[lang]):
                path = url.path.rstrip("/") or "/"
                if path in live_paths[lang] and not (source + "/").startswith(
                    path.rstrip("/") + "/"
                ):
                    live_paths[lang][path] += 1

    # Super.so lists pages that it no longer renders, from super-so-pages.csv (exported from its dashboard).
    stale = {lang: [] for lang in SITES.values()}
    with (CRAWL / "super-so-pages.csv").open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["renders_on_super"] == "no" and row["path"]:
                stale[SITES[row["domain"]]].append("/" + row["path"])

    # Super.so serves each page at its Notion ID, and some pages at other capitalizations, and redirects to the slug.
    redirects = {}
    for lang in SITES.values():
        rules = {
            f"/{page_id}": path
            for (language, page_id), path in slugs.items()
            if language == lang
        }
        for r in ok:
            if (
                r not in canonical
                and SITES[urllib.parse.urlparse(r["url"]).netloc] == lang
            ):
                source = urllib.parse.urlparse(r["url"]).path
                if source not in ("", "/"):
                    rules[source] = urllib.parse.urlparse(r["final"]).path
        for source in stale[lang]:
            if target := moved_to(source, live_paths[lang]):
                rules.setdefault(source, target)
        redirects[lang] = {
            source: target for source, target in rules.items() if source != target
        }

    links = collections.Counter()
    pages = []
    for r in canonical:
        lang = SITES[urllib.parse.urlparse(r["url"]).netloc]
        path = slugs[(lang, r["pageId"])]
        document = crawled_path(r["url"]).read_text()
        head = document[: document.index("<body")]
        content = MAIN.search(document).group(3)
        content = re.sub(r"<script.*?</script>", "", content, flags=re.S)
        content = fix_text_spaces(clean(localize(content)), lang)
        content = HREF.sub(
            lambda m: rewrite_link(m, lang, live_paths, redirects, links), content
        )
        data, content = parse_page(content)
        data = {
            "permalink": path,
            "title": fix_spaces(
                html.unescape(re.search(r"<title>([^<]*)</title>", head).group(1)), lang
            ),
            "description": fix_spaces(meta(head, "name", "description") or "", lang)
            or None,
            **data,
            "notion_id": r["pageId"],
        }
        data = {key: value for key, value in data.items() if value is not None}
        pages.append((lang, path, data, content))

    # Each language's sidebar is the most common content of a column that starts with a link to the homepage.
    sidebars = {}
    for lang in SITES.values():
        columns = collections.Counter(
            re.sub(r' id="[^"]*"', "", column)
            for language, _, _, content in pages
            if language == lang and (column := sidebar(content))
        )
        sidebars[lang] = columns.most_common(1)[0][0]
        (ROOT / "_includes" / f"sidebar-{lang}.html").write_text(
            indent(sidebars[lang]) + "\n"
        )

    contents = []
    for lang, path, data, content in pages:
        if column := sidebar(content):
            normalized = re.sub(r' id="[^"]*"', "", column)
            if normalized.startswith(sidebars[lang]):
                start = content.index(column)
                content = (
                    content[:start]
                    + f"{{% include sidebar-{lang}.html %}}"
                    + normalized[len(sidebars[lang]) :]
                    + content[start + len(column) :]
                )
        # Remove empty paragraphs, which Notion uses for spacing (the sidebar's separate its groups of links).
        content = SPACER.sub("", content)
        # Join the bulleted lists that the empty paragraphs separated (Markdown would join them as a "loose" list).
        content = content.replace('</ul><ul class="notion-bulleted-list">', "")
        contents.append(content)

    markdowns, (converted, candidates, tagged) = markdown.to_markdown(contents, indent)
    for (lang, path, data, _), content, text in zip(pages, contents, markdowns):
        extension = ".html" if text is None else ".md"
        filename = ROOT / lang / ((path.strip("/") or "index") + extension)
        filename.parent.mkdir(parents=True, exist_ok=True)
        body = indent(markdown.strip_ids(content)) if text is None else text
        filename.write_text(front_matter(data) + body + "\n")
    print(
        f"{converted} of {candidates} blocks and {sum(t is not None for t in markdowns)} of {len(pages)} pages "
        f"converted to Markdown, {tagged} pages with Liquid tags"
    )

    print("links:", dict(links))

    for lang in SITES.values():
        lines = [
            f"{source} {target} 301"
            for source, target in sorted(redirects[lang].items())
        ]
        (ROOT / lang / "_redirects").write_text(
            front_matter({"permalink": "/_redirects", "layout": None})
            + "\n".join(lines)
            + "\n"
        )

    # The <style> blocks after <main> are identical on every page of a site.
    for host, lang in SITES.items():
        document = crawled_path(f"https://{host}/").read_text()
        body = document[document.index("<body") :]
        (ROOT / "assets" / "css" / f"theme-{lang}.css").write_text(
            "\n".join(style.strip() for style in STYLE.findall(body)) + "\n"
        )

    print(len(canonical), "pages")


if __name__ == "__main__":
    main()
