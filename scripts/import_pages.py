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
import translations

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
NOTION_IMAGE = re.compile(
    r"https://app\.notion\.com/image/https%3A%2F%2Fs3-us-west-2\.amazonaws\.com%2Fsecure\.notion-static\.com%2F"
    r"[0-9a-f-]+%2F([^?\"%]+(?:%20[^?\"%]+)*)\?[^\"]*"
)
SUPER_ASSET = re.compile(r"https://assets\.super\.so/")
MAIN = re.compile(r'<main id="([^"]*)" class="([^"]*)">(.*)</main>', re.S)
STYLE = re.compile(r"<style>(.*?)</style>", re.S)
HREF = re.compile(r'href="([^"]*)"')
# Empty paragraphs and headings, which Notion uses for spacing.
SPACER = re.compile(
    r'<div (?:id="[^"]*" )?class="notion-text(?: color-\w+)?"></div>'
    r'|<p (?:id="[^"]*" )?class="notion-text notion-text__content notion-semantic-string"></p>'
    r'|<(h[1-3]) (?:id="[^"]*" )?class="notion-heading notion-semantic-string"></\1>'
)
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


def notion_image(match):
    """Return the local image with the same name as an image hosted by Notion (whose links no longer work)."""
    path = f"assets/images/{urllib.parse.unquote(match.group(1))}"
    return f"/{urllib.parse.quote(path)}" if (ROOT / path).exists() else match.group(0)


def localize(text):
    text = NEXT_IMAGE.sub(lambda m: urllib.parse.unquote(m.group(1)), text)
    text = NOTION_IMAGE.sub(notion_image, text)
    text = IMAGE.sub(image_path, text)
    return SUPER_ASSET.sub("/assets/super/", text)


def resolve_suspense(document):
    """Put content that React streamed after the page (e.g. code blocks' code) where its script would put it."""
    while match := re.search(r'<div hidden id="S:(\d+)">', document):
        end = element_end(document, match.start())
        content = document[match.end() : end - len("</div>")]
        document = document[: match.start()] + document[end:]
        document = re.sub(
            rf'<!--\$\?--><template id="B:{match.group(1)}"></template>.*?<!--/\$-->',
            lambda _: content,
            document,
            count=1,
            flags=re.S,
        )
    return document


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
    # Remove databases' anchors (to IDs that no longer exist) and view switchers (to views that weren't crawled).
    text = re.sub(r'<a class="notion-anchor" href="#[^"]*"></a>', "", text)
    text = re.sub(r' collection-[0-9a-f]{32}(?=")', "", text)
    # Remove properties' classes, which no stylesheet uses.
    text = re.sub(r' property-[0-9a-f]{8}(?=[ "])', "", text)
    while (start := text.find('<div class="notion-dropdown">')) != -1:
        text = text[:start] + text[element_end(text, start) :]
    # Move newlines at the end of links' text after the links.
    text = re.sub(r"(\n+)</a>", r"</a>\1", text)
    # Remove whitespace at the start of text blocks, and newlines at the end.
    inline_start = r"(?:<(?:strong|em|a|span)\b[^>]*>)*"
    text = re.sub(
        rf'(<(?:p|li|h[1-6]|span|div)\b[^>]*class="[^"]*notion-semantic-string[^"]*">{inline_start})[\n \xa0]+',
        r"\1",
        text,
    )
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


def parse_properties(content):
    """
    Return a database item's properties and the rest of its content, or None and the content.

    Pills are a mapping of values to colors, attachments and URLs are a list of mappings of text to URLs, numbers are
    numbers, and dates and text are strings.
    """
    nodes = markdown.parse(content)
    if (
        not nodes
        or isinstance(nodes[0], str)
        or nodes[0].attrs != {"class": "notion-page__properties"}
    ):
        return None, content
    block = nodes[0]
    children = markdown.elements(block)
    if not children or children[-1].cls != "notion-divider" or children[-1].children:
        return None, content
    properties = {}
    for child in children[:-1]:
        parts = markdown.elements(child)
        if (
            child.attrs != {"class": "notion-page__property"}
            or not parts
            or len(parts) > 2
        ):
            return None, content
        name = re.fullmatch(
            r'<div class="notion-page__property-name-wrapper"><div class="notion-page__property-name"><span>([^<]*)</span></div></div>',
            content[parts[0].start : parts[0].end],
        )
        if not name or html.unescape(name.group(1)) in properties:
            return None, content
        value = property_value(parts[1], content) if len(parts) == 2 else (None,)
        if value is False:
            return None, content
        properties[html.unescape(name.group(1))] = value[0]
    return properties, content[block.end :]


def property_value(node, content):
    """Return a property's value as a 1-tuple, or False."""
    cls = re.sub(r" property-[0-9a-f]+", "", node.cls)
    text = content[node.start + len(node.tag) : node.end - len(f"</{node.name}>")]
    if cls == "notion-property notion-property__select wrap":
        pills = re.findall(
            r'<span class="notion-pill pill-(\w+)(?: first)?">([^<]*)</span>', text
        )
        values = {html.unescape(value): color for color, value in pills}
        if "".join(re.findall(r"<span .*?</span>", text)) != text or len(values) != len(
            pills
        ):
            return False
        return (values,)
    if cls in (
        "notion-property notion-property__number notion-semantic-string",
    ) and re.fullmatch(r"-?\d+(\.\d+)?", text):
        return (float(text) if "." in text else int(text),)
    if (
        cls
        in (
            "notion-property notion-property__text notion-semantic-string",
            "notion-property notion-property__date notion-semantic-string",
        )
        and "<" not in text
    ):
        return (html.unescape(text),)
    if cls in (
        "notion-property notion-property__file",
        "notion-property notion-property__url notion-semantic-string",
    ):
        links = re.findall(
            r'<a (?:class="notion-link link" )?href="([^"]*)"[^>]*>([^<]*)</a>', text
        )
        return ([{html.unescape(label): html.unescape(href)} for href, label in links],)
    return False


def table_view(view, text, items):
    """
    Return a database's table view's columns, whether its rows are clickable, and its items' paths and properties.

    ``items`` maps paths to titles (for rows that aren't clickable, which are found by title). Return None if the view
    isn't regular.
    """
    parts = markdown.elements(view)
    table = parts[0] if parts and len(parts) == 1 else None
    sections = (
        markdown.elements(table)
        if table and table.attrs == {"class": "notion-collection-table"}
        else None
    )
    if not sections or len(sections) != 2:
        return None
    thead, tbody = sections
    head = markdown.elements(thead)
    if (
        thead.attrs != {"class": "notion-collection-table__head"}
        or not head
        or len(head) != 1
    ):
        return None
    columns = []
    for th in markdown.elements(head[0]) or []:
        kind = re.fullmatch(r"notion-collection-table__head-cell (\w+)", th.cls)
        width = re.fullmatch(r"width:(\d+)px", th.attrs.get("style", ""))
        name = re.fullmatch(
            r'<div class="notion-collection-table__head-cell-content">([^<]*)</div>',
            text[th.start + len(th.tag) : th.end - len("</th>")],
        )
        if not kind or not name or ("style" in th.attrs and not width):
            return None
        column = {"name": html.unescape(name.group(1)), "type": kind.group(1)}
        if width:
            column["width"] = int(width.group(1))
        columns.append(column)
    if (
        not columns
        or columns[0]["type"] != "title"
        or tbody.attrs != {"class": "notion-collection-table__body"}
    ):
        return None
    titles = {}
    for path, title in items.items():
        titles.setdefault(title, []).append(path)
    clickable = set()
    rows = []
    for tr in markdown.elements(tbody) or []:
        cells = markdown.elements(tr)
        if not cells or len(cells) != len(columns):
            return None
        cell = text[cells[0].start : cells[0].end]
        link = re.fullmatch(
            r'<td class="notion-collection-table__cell title"><div><a href="([^"]*)" class="notion-link">'
            r'<div class="notion-property notion-property__title notion-semantic-string">([^<]*)</div></a></div></td>',
            cell,
        )
        no_link = re.fullmatch(
            r'<td class="notion-collection-table__cell title no-click"><div>'
            r'<div class="notion-property notion-property__title notion-semantic-string">([^<]*)</div></div></td>',
            cell,
        )
        if link:
            path, title = html.unescape(link.group(1)), html.unescape(link.group(2))
        elif no_link and len(titles.get(html.unescape(no_link.group(1)), [])) == 1:
            title = html.unescape(no_link.group(1))
            path = titles[title][0]
        else:
            return None
        if items.get(path) != title:
            return None
        clickable.add(bool(link))
        properties = {}
        for column, td in zip(columns[1:], cells[1:]):
            values = markdown.elements(td)
            if (
                td.cls != f"notion-collection-table__cell {column['type']}"
                or values is None
                or len(values) > 1
            ):
                return None
            value = property_value(values[0], text) if values else (None,)
            if value is False:
                return None
            properties[column["name"]] = value[0]
        rows.append((path, properties))
    if len(clickable) != 1:
        return None
    return columns, clickable.pop(), rows


COLUMN_TAG = re.compile(r"\{% (end)?(columns|column)\b([^%]*)%\}")


def lift_sidebar(text, lang):
    """
    Return the column widths and the content column's content, if the page is a sidebar and a content column.

    The layout renders the sidebar. Return None if the page isn't only a sidebar, content and empty columns.
    """
    if not text.startswith("{% columns %}\n"):
        return None
    depth = 0
    columns = []
    for match in COLUMN_TAG.finditer(text):
        if match.group(2) == "columns":
            depth += -1 if match.group(1) else 1
            if depth == 0:
                if text[match.end() :].strip():
                    return None
                break
        elif depth == 1:
            if match.group(1):
                columns[-1][2] = match.start()
            else:
                columns.append([match.group(3).split(), match.end(), None])
    if len(columns) not in (2, 3):
        return None
    (sidebar_arguments, sidebar_start, sidebar_end), (arguments, start, end) = columns[
        :2
    ]
    if text[
        sidebar_start:sidebar_end
    ].strip() != f"{{% include sidebar-{lang}.html %}}" or sidebar_arguments[1:] != [
        "html"
    ]:
        return None
    if len(columns) == 3 and text[columns[2][1] : columns[2][2]].strip():
        return None
    body = text[start:end].strip()
    if arguments[1:] == ["html"]:
        body = "{::nomarkdown}\n" + body + "\n{:/nomarkdown}"
    return [float(column[0][0]) for column in columns], body


def sidebar(content):
    """Return the content of the first column, if it starts with a link to the homepage."""
    match = SIDEBAR.search(content)
    if match and re.match(r'<a (?:id="[^"]*" )?href="/"', content[match.end() :]):
        return content[
            match.end() : element_end(content, match.start()) - len("</div>")
        ]
    return None


def body_key(content):
    """Return a page's content without its sidebar, IDs and spacers, to compare pages, or "" if it has no content."""
    if column := sidebar(content):
        content = content.replace(column, "")
    content = SPACER.sub("", re.sub(r' id="[^"]*"', "", content))
    if not re.sub(r"<[^>]*>", "", content).strip() and "<img" not in content:
        return ""
    return content


def canonical_paths(paths):
    """
    Return new paths for paths with segments that end in a number that Super.so added (e.g. "-1"), without it.

    A parent's new path is its children's, and a path whose new path is another page's (or year's) is kept.
    """
    taken = set(paths)
    renamed = {}
    for path in sorted(paths, key=lambda path: (path.count("/"), path)):
        parent, _, segment = path.rpartition("/")
        parent = renamed.get(parent, parent)
        stripped = re.sub(r"-\d+$", "", segment)
        new = f"{parent}/{stripped}"
        if (
            stripped == segment
            or re.search(r"-(?:19|20)\d\d$", segment)
            or new in taken
        ):
            new = f"{parent}/{segment}"
        if new != path:
            taken.add(new)
            renamed[path] = new
    return renamed


# Links to the other sites' pages, in Markdown, HTML and YAML.
CROSS_SITE = re.compile(
    r"https://(sustainable|sostenibilidad|achatdurable)\.open-contracting\.org(/[^\s\"')\]#?]*)?([#?][^\s\"')\]]*)?"
)
# The lowest score of the translations' matches that link_versions() uses. The matches were reviewed.
VERSION_SCORE = 5.5


def link_versions():
    """
    Link the pages' links to another site's page to that page's version on their own site, if it has one.

    Links to another site's homepage are kept, since they switch languages. Return the links that changed.
    """
    versions = translations.matches()
    english = {
        lang: {other: (path, score) for path, (other, score) in matched.items()}
        for lang, matched in versions.items()
    }

    def version(lang, other, path):
        scores = []
        if other != "en":
            if path not in english[other]:
                return None
            path, score = english[other][path]
            scores.append(score)
        if lang != "en":
            if path not in versions[lang]:
                return None
            path, score = versions[lang][path]
            scores.append(score)
        return path, min(scores)

    changed = []
    for lang in SITES.values():
        for file in sorted((ROOT / lang).rglob("*.md")):
            text = file.read_text()

            def replace(match):
                other = LINK_HOSTS[f"{match.group(1)}.open-contracting.org"]
                path = urllib.parse.unquote(match.group(2) or "/").rstrip("/") or "/"
                if other == lang or path == "/":
                    return match.group(0)
                found = version(lang, other, path)
                if found is None or found[1] < VERSION_SCORE:
                    return match.group(0)
                changed.append((lang, str(file.relative_to(ROOT)), match.group(0), found[0], found[1]))
                return urllib.parse.quote(found[0]) + (match.group(3) or "")

            new = CROSS_SITE.sub(replace, text)
            if new != text:
                file.write_text(new)
    return changed


def title_key(data):
    """Return a page's title, ignoring case and spacing."""
    return " ".join(data["title"].split()).casefold()


def duplicates(pages, live_paths):
    """
    Return the pages that duplicate other pages, mapped to those pages, by language.

    - A copy has the same title and content as other pages. The page with the most incoming links is kept.
    - A placeholder is a database item that Super.so publishes for a gallery card: empty, or with the same content
      as pages with other titles. It duplicates its "super:Link" property's page, else the only other page with its
      title. Items in table views are kept, since their properties are the views' cells.
    """
    table_items = set()
    for lang, _, _, content in pages:
        for match in re.finditer(
            r'<div class="notion-collection-table__wrapper">', content
        ):
            block = content[match.start() : element_end(content, match.start())]
            table_items.update((lang, href) for href in HREF.findall(block))

    keys = {(lang, path): body_key(content) for lang, path, _, content in pages}
    titles = collections.defaultdict(set)
    for lang, path, data, _ in pages:
        titles[(lang, keys[(lang, path)])].add(title_key(data))
    placeholders = {
        (lang, path)
        for lang, path, data, _ in pages
        if not keys[(lang, path)] or len(titles[(lang, keys[(lang, path)])]) > 1
    }

    moved = {lang: {} for lang in SITES.values()}
    copies = collections.defaultdict(list)
    by_title = collections.defaultdict(list)
    for lang, path, data, _ in pages:
        if (lang, path) in placeholders:
            continue
        copies[(lang, title_key(data), keys[(lang, path)])].append(path)
        by_title[(lang, title_key(data))].append(path)
    for (lang, _, _), paths in copies.items():
        kept = max(paths, key=lambda path: (live_paths[lang][path], -len(path), path))
        moved[lang].update({path: kept for path in paths if path != kept})
    for lang, path, data, _ in pages:
        if (lang, path) not in placeholders or (lang, path) in table_items:
            continue
        links = [
            href
            for link in data.get("properties", {}).get("super:Link", [])
            for href in link.values()
        ]
        candidates = [
            href for href in links if href in live_paths[lang] and href != path
        ] or by_title[(lang, title_key(data))]
        if len(candidates) == 1:
            target = candidates[0]
            moved[lang][path] = moved[lang].get(target, target)
    return moved


def rewrite_link(match, lang, live, redirects, fixes, counter):
    """
    Make a link to a site's page relative (or absolute to its domain), skipping any redirect.

    Add a redirect for a link to a page that doesn't exist, if a live page clearly replaces it. A link from another
    language's site to a page that doesn't exist links to its fix's target, on this page's site (or a URL).
    """
    href = html.unescape(match.group(1))
    url = urllib.parse.urlsplit(href)
    if url.scheme in ("http", "https") and url.netloc.lower() in LINK_HOSTS:
        target = LINK_HOSTS[url.netloc.lower()]
        kind = "absolute"
    elif href.startswith("/") and not href.startswith(("//", "/assets/")):
        target = lang
        kind = "relative"
    elif url.netloc in ("notion.so", "www.notion.so") and (
        notion_id := re.search(r"([0-9a-f]{32})$", url.path)
    ):
        # A link to a Notion page, which Super.so serves at its ID.
        target = lang
        kind = "absolute"
        url = urllib.parse.urlsplit(f"/{notion_id.group(1)}")
    else:
        return match.group(0)
    path = urllib.parse.unquote(url.path).rstrip("/") or "/"
    if fixed := fixes.get((lang, target, path)):
        counter["fixed from another site"] += 1
        return f'href="{html.escape(fixed if fixed.startswith("https://") else urllib.parse.quote(fixed))}"'
    # A fix for links from the path's own site doesn't apply to links from other sites, which stay broken.
    if target != lang and (target, path) in fixes:
        return f'href="{html.escape(f"https://{DOMAINS[target]}{urllib.parse.quote(path)}")}"'
    path = redirects[target].get(path, path)
    if path.startswith("https://"):
        counter["fixed to another site"] += 1
        return f'href="{html.escape(path)}"'
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


def yaml(value, depth=0):
    """Return a value as YAML, in block style for mappings and lists."""
    pad = "  " * depth
    if isinstance(value, dict) and value:
        lines = []
        for key, item in value.items():
            separator = "" if isinstance(item, (dict, list)) and item else " "
            lines.append(
                f"\n{pad}{markdown.scalar(key)}:{separator}{yaml(item, depth + 1)}"
            )
        return "".join(lines)
    if isinstance(value, list) and value:
        return "".join(f"\n{pad}- {yaml(item, depth + 1).lstrip()}" for item in value)
    return markdown.scalar(value)


def front_matter(data):
    lines = []
    for key, value in data.items():
        separator = "" if isinstance(value, (dict, list)) and value else " "
        lines.append(f"{key}:{separator}{yaml(value, 1)}\n")
    return "---\n" + "".join(lines) + "---\n"


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
    renamed = {
        lang: canonical_paths(
            [path for (language, _), path in slugs.items() if language == lang]
        )
        for lang in SITES.values()
    }
    slugs = {
        (lang, page_id): renamed[lang].get(path, path)
        for (lang, page_id), path in slugs.items()
    }

    # Each live page's number of incoming links on its site, other than breadcrumbs (from itself and its descendants).
    live_paths = {lang: {} for lang in SITES.values()}
    for (lang, _), path in slugs.items():
        live_paths[lang][path] = 0
    for r in canonical:
        lang = SITES[urllib.parse.urlparse(r["url"]).netloc]
        source = urllib.parse.urlparse(r["url"]).path.rstrip("/") or "/"
        source = renamed[lang].get(source, source)
        for link in r["links"]:
            url = urllib.parse.urlsplit(link)
            if url.netloc in ("", DOMAINS[lang]):
                path = url.path.rstrip("/") or "/"
                path = renamed[lang].get(path, path)
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
                    final = urllib.parse.urlparse(r["final"]).path.rstrip("/") or "/"
                    rules[source] = renamed[lang].get(final, final)
        # Pages' paths on Super.so redirect to their new paths.
        rules.update(renamed[lang])
        for source in stale[lang]:
            if target := moved_to(source, live_paths[lang]):
                rules.setdefault(source, target)
        redirects[lang] = {
            source: target for source, target in rules.items() if source != target
        }

    # Broken links' reviewed targets (a path on the linking pages' site, or a URL), from link-fixes.csv. A fix for
    # links from the broken link's own site is a redirect, and a fix for links from another site is a link.
    fixes = {}
    if (ROOT / "link-fixes.csv").exists():
        with (ROOT / "link-fixes.csv").open(encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                # A path can be a page again, if its page's path was canonicalized.
                if row["target"] and row["path"] not in live_paths[row["site"]]:
                    target = renamed[row["from"]].get(row["target"], row["target"])
                    if row["from"] == row["site"]:
                        redirects[row["site"]][row["path"]] = target
                        fixes[(row["site"], row["path"])] = target
                    else:
                        fixes[(row["from"], row["site"], row["path"])] = target

    links = collections.Counter()
    pages = []
    for r in canonical:
        lang = SITES[urllib.parse.urlparse(r["url"]).netloc]
        path = slugs[(lang, r["pageId"])]
        document = resolve_suspense(crawled_path(r["url"]).read_text())
        head = document[: document.index("<body")]
        content = MAIN.search(document).group(3)
        content = re.sub(r"<script.*?</script>", "", content, flags=re.S)
        content = fix_text_spaces(clean(localize(content)), lang)
        content = HREF.sub(
            lambda m: rewrite_link(m, lang, live_paths, redirects, fixes, links),
            content,
        )

        # A link whose text is its original URL (like an attachment) has its new URL as its text.
        def retext(match):
            text = html.unescape(match.group(2))
            rewritten = rewrite_link(
                re.match(HREF, f'href="{html.escape(text)}"'),
                lang,
                live_paths,
                redirects,
                fixes,
                collections.Counter(),
            )
            if text != match.group(1) and rewritten == f'href="{match.group(1)}"':
                return match.group(0).replace(
                    f">{match.group(2)}</a>", f">{match.group(1)}</a>"
                )
            return match.group(0)

        content = re.sub(
            r'<a [^>]*href="(https://[^"]*)"[^>]*>(https?://[^<]*)</a>', retext, content
        )
        data, content = parse_page(content)
        properties, content = parse_properties(content)
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
        if properties is not None:
            data["properties"] = properties
        pages.append((lang, path, data, content))

    # Pages that duplicate other pages redirect to them, and links to them link to those pages.
    moved = duplicates(pages, live_paths)
    for lang, sources in moved.items():
        for target in sources.values():
            assert target not in sources, target
        redirects[lang] = {
            source: sources.get(target, target)
            for source, target in redirects[lang].items()
        }
        redirects[lang].update(sources)
        for source in sources:
            del live_paths[lang][source]
    href = re.compile(r'href="(https://[^/"]+)?(/[^"#?]*)')

    def relink(lang, text):
        def replace(match):
            host = match.group(1)
            target = SITES.get(urllib.parse.urlsplit(host).netloc) if host else lang
            path = urllib.parse.unquote(match.group(2))
            if path not in moved.get(target, {}):
                return match.group(0)
            links["duplicate relinked"] += 1
            return f'href="{host or ""}{html.escape(urllib.parse.quote(moved[target][path]))}'

        return href.sub(replace, text) if isinstance(text, str) else text

    def relink_properties(lang, value):
        if isinstance(value, dict):
            return {k: relink_properties(lang, v) for k, v in value.items()}
        if isinstance(value, list):
            return [relink_properties(lang, v) for v in value]
        if isinstance(value, str) and value.startswith("/"):
            return moved[lang].get(value, value)
        return value

    pages = [
        (
            lang,
            path,
            {**data, "properties": relink_properties(lang, data["properties"])}
            if "properties" in data
            else data,
            relink(lang, content),
        )
        for lang, path, data, content in pages
        if path not in moved[lang]
    ]
    print("duplicates:", {lang: len(sources) for lang, sources in moved.items()})
    (CRAWL / "duplicates.json").write_text(
        json.dumps(moved, indent=2, ensure_ascii=False) + "\n"
    )

    # Databases' table views become {% database_table %} tags, and their cells become their items' properties.
    by_path = {(lang, path): data for lang, path, data, _ in pages}
    items = collections.defaultdict(dict)
    for lang, path, data, _ in pages:
        items[lang][path] = data["title"]
    views = collections.Counter()
    for lang, _, _, content in pages:
        text = markdown.strip_ids(content)
        stack = markdown.parse(text)
        while stack:
            node = stack.pop()
            if isinstance(node, str):
                continue
            if node.cls != "notion-collection-table__wrapper":
                stack.extend(node.children)
                continue
            view = table_view(node, text, items[lang])
            if view is None:
                views["kept as HTML"] += 1
                continue
            columns, clickable, rows = view
            consistent = True
            for path, properties in rows:
                existing = by_path[(lang, path)].get("properties")
                if existing is not None and any(
                    existing.get(k, v) != v for k, v in properties.items()
                ):
                    consistent = False
            if not consistent:
                views["inconsistent with items"] += 1
                continue
            for path, properties in rows:
                data = by_path[(lang, path)]
                data["properties"] = {**data.get("properties", {}), **properties}
            body = (
                "columns:"
                + yaml(columns, 1)
                + "\nitems:"
                + yaml([path for path, _ in rows], 1)
            )
            argument = "" if clickable else " no-click"
            markdown.VIEWS[text[node.start : node.end]] = (
                f"{{% database_table{argument} %}}\n{body}\n{{% enddatabase_table %}}"
            )
            views["converted"] += 1
    print("table views:", dict(views))

    # Each language's sidebar is the most common content of a column that starts with a link to the homepage.
    sidebars = {}
    for lang in SITES.values():
        columns = collections.Counter(
            re.sub(r' id="[^"]*"', "", column)
            for language, _, _, content in pages
            if language == lang and (column := sidebar(content))
        )
        sidebars[lang] = columns.most_common(1)[0][0]
        markdown.INCLUDES[f"sidebar-{lang}.html"] = sidebars[lang]
        # Links to pages are {% page %} tags, which render the pages' icons and titles.
        markdown.PAGES.clear()
        markdown.PAGES.update(
            {
                path: data
                for (language, path), data in by_path.items()
                if language == lang
            }
        )
        lines = []
        for node in markdown.parse(sidebars[lang]):
            raw = sidebars[lang][node.start : node.end]
            lines.append(markdown.page_link(raw, " html") or indent(raw))
        (ROOT / "_includes" / f"sidebar-{lang}.html").write_text(
            "\n".join(lines) + "\n"
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

    front_matter_by_language = collections.defaultdict(dict)
    for lang, path, data, _ in pages:
        front_matter_by_language[lang][path] = data
    markdowns, (converted, candidates, tagged) = markdown.to_markdown(
        contents, indent, [lang for lang, _, _, _ in pages], front_matter_by_language
    )
    for (lang, path, data, _), content, text in zip(pages, contents, markdowns):
        extension = ".html" if text is None else ".md"
        filename = ROOT / lang / ((path.strip("/") or "index") + extension)
        filename.parent.mkdir(parents=True, exist_ok=True)
        body = indent(markdown.strip_ids(content)) if text is None else text
        if text is not None and (lifted := lift_sidebar(text, lang)):
            _, body = lifted
            data["sidebar"] = True
        filename.write_text(front_matter(data) + body + "\n")
    print(
        f"{converted} of {candidates} blocks and {sum(t is not None for t in markdowns)} of {len(pages)} pages "
        f"converted to Markdown, {tagged} pages with Liquid tags"
    )

    print("links:", dict(links))

    changed = link_versions()
    (CRAWL / "versions-relinked.json").write_text(json.dumps(changed, indent=1, ensure_ascii=False) + "\n")
    print(len(changed), "links to other sites linked to their pages' versions")

    for lang in SITES.values():
        lines = [
            f"{source} {target} 301"
            for source, target in sorted(redirects[lang].items())
            if source != target
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
