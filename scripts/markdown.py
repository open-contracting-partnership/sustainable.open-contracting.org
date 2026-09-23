"""
Convert Notion's HTML to Markdown, where the site's Markdown converter renders the same HTML.

Paragraphs, headings and flat lists become Markdown, in columns, toggles and at the top level. Other blocks stay HTML.
"""

import html
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TOKEN = re.compile(r"<!--.*?-->|<[^>]*>|[^<]+", re.S)
ATTRIBUTE = re.compile(r'([^\s=/]+)(?:="([^"]*)")?')
VOID = {
    "br",
    "hr",
    "img",
    "input",
    "meta",
    "link",
    "source",
    "col",
    "wbr",
    "path",
    "circle",
    "rect",
    "line",
}
# Tags that kramdown parses as the start of an HTML block (a span-level tag would be wrapped in a paragraph).
BLOCK = {
    "article",
    "aside",
    "blockquote",
    "details",
    "div",
    "figure",
    "h1",
    "h2",
    "h3",
    "h4",
    "hr",
    "iframe",
    "ol",
    "p",
    "table",
    "ul",
}
# Elements in which whitespace is significant (white-space: pre-wrap).
PRESERVE = re.compile(
    r"\b(?:notion-semantic-string|notion-header__title|notion-code)\b"
)

PARAGRAPH = "notion-text notion-text__content notion-semantic-string"
HEADING = "notion-heading notion-semantic-string"
LIST_ITEM = "notion-list-item notion-semantic-string"
LINK = "notion-link link"
LEVELS = ("minimal", "common", "all")
# Containers of blocks, in which Markdown is enabled.
CONTAINERS = {"notion-column", "notion-toggle__content"}


REPORT = {
    "unconverted containers": [],
    "unconverted blocks": [],
    "unconverted pages": [],
}


class Element:
    def __init__(self, tag, start):
        self.tag = tag
        self.start = start
        self.name = re.match(r"<([a-zA-Z0-9]+)", tag).group(1).lower()
        self.attrs = dict(
            (k, v)
            for k, v in ATTRIBUTE.findall(tag[len(self.name) + 1 : -1].rstrip("/"))
        )
        self.children = []
        self.end = None

    @property
    def cls(self):
        return self.attrs.get("class", "")


def parse(text):
    """Return the elements and text of an HTML fragment, as a list of Element and str."""
    root = Element("<root>", 0)
    stack = [root]
    for match in TOKEN.finditer(text):
        token = match.group(0)
        if token.startswith("<!--"):
            continue
        if token.startswith("</"):
            if token[2:-1].strip().lower() in VOID:  # e.g. <circle ...></circle>
                continue
            element = stack.pop()
            element.end = match.end()
        elif token.startswith("<"):
            element = Element(token, match.start())
            stack[-1].children.append(element)
            if element.name in VOID or token.endswith("/>"):
                element.end = match.end()
            else:
                stack.append(element)
        else:
            stack[-1].children.append(token)
    return root.children


def escape(text, start_of_line, level):
    """
    Escape text for Markdown, at a level of ``LEVELS``.

    The lowest level that renders the same HTML is used, to avoid unnecessary backslashes.
    """
    text = re.sub(r"&(?=#?\w+;)", "&amp;", text)
    if level == "minimal":
        return re.sub(r"\\|<(?=[a-zA-Z/!?])", r"\\\g<0>", text)
    if level == "common":
        text = re.sub(r"([\\`*_\[\]<])", r"\\\1", text)
    else:
        text = re.sub(r"([\\`*_\[\]<>|{}$])", r"\\\1", text)
    if start_of_line:
        text = re.sub(r"^([#>:=+-])", r"\\\1", text)
        text = re.sub(r"^(\d+)([.)])", r"\1\\\2", text)
    return text


def merge(nodes):
    """Merge consecutive bold (or italic) elements, which Notion sometimes splits."""
    merged = []
    for node in nodes:
        previous = merged[-1] if merged else None
        if (
            isinstance(node, Element)
            and isinstance(previous, Element)
            and node.name in ("strong", "em")
            and node.name == previous.name
            and not node.attrs
            and not previous.attrs
        ):
            combined = Element(previous.tag, previous.start)
            combined.children = previous.children + node.children
            combined.end = node.end
            merged[-1] = combined
        else:
            merged.append(node)
    return merged


def inline(nodes, level, start_of_line=True):
    """Return the Markdown for inline content, or None."""
    output = []
    for node in merge(nodes):
        at_start = (
            start_of_line and not output or (output and output[-1].endswith("\n"))
        )
        if isinstance(node, str):
            text = html.unescape(node)
            # A newline is a line break (white-space: pre-wrap), but a blank line would end the paragraph.
            lines = text.split("\n")
            parts = []
            for i, line in enumerate(lines):
                # Spaces before a line break don't render, and two would be a hard line break in Markdown.
                if i < len(lines) - 1:
                    line = line.rstrip(" ")
                parts.append(escape(line, at_start if i == 0 else True, level))
            # A line break is a newline, unless the previous line is empty, in which case it's a <br>.
            markdown = parts[0]
            for part in parts[1:]:
                previous = "".join(output) + markdown
                markdown += (
                    "<br>" if not previous or previous.endswith("\n") else "\n"
                ) + part
            output.append(markdown)
        elif node.name in ("strong", "em") and not node.attrs:
            # Bold that is bold again, as in some Notion headings.
            while (
                len(node.children) == 1
                and not isinstance(node.children[0], str)
                and node.children[0].name == node.name
                and not node.children[0].attrs
            ):
                node = node.children[0]
            content = inline(node.children, level, at_start)
            if content is None:
                return None
            marker = "**" if node.name == "strong" else "*"
            stripped = content.strip(" ")
            if stripped and "\n" not in content and "<br>" not in content:
                # Spaces at the edges of bold or italic text are moved outside it.
                leading = content[: len(content) - len(content.lstrip(" "))]
                trailing = content[len(content.rstrip(" ")) :]
                output.append(f"{leading}{marker}{stripped}{marker}{trailing}")
            else:
                output.append(f"<{node.name}>{content}</{node.name}>")
        elif (
            node.name == "a"
            and node.attrs.get("class") == LINK
            and set(node.attrs) <= {"href", "class", "target", "rel"}
        ):
            content = inline(node.children, level, False)
            href = html.unescape(node.attrs.get("href", ""))
            if (
                content is None
                or not content
                or "\n" in content
                or re.search(r"[\s<>]", href)
            ):
                return None
            if re.search(r"[()]", href):
                href = f"<{href}>"
            output.append(f"[{content}]({href})")
        else:
            return None
    return "".join(output)


def code_block(node):
    """Return a Notion code block as a fenced code block, or None."""
    children = elements(node)
    if (
        node.attrs != {"class": "notion-code no-wrap"}
        or not children
        or len(children) != 3
    ):
        return None
    button, pre, caption = children
    if (
        button.cls != "notion-code__copy-button"
        or pre.name != "pre"
        or caption.children
    ):
        return None
    codes = elements(pre)
    if (
        not codes
        or len(codes) != 1
        or codes[0].name != "code"
        or codes[0].attrs != pre.attrs
    ):
        return None
    if not all(isinstance(child, str) for child in codes[0].children):
        return None
    language = pre.attrs.get("class", "").removeprefix("language-")
    code = html.unescape("".join(codes[0].children))
    fence = "```"
    while fence in code:
        fence += "`"
    return f"{fence}{language}\n{code}\n{fence}"


TODO = re.compile(
    r'<div class="notion-to-do"><div class="notion-to-do__content"><div class="notion-to-do__icon">'
    r'<div class="notion-checkbox"><svg viewBox="0 0 16 16"><path d="[^"]*"></path></svg></div></div>'
    r'<div class="notion-to-do__title">(<span class="notion-semantic-string">.*</span>)</div></div></div>',
    re.S,
)


def todo(node, level, raw):
    """Return a Notion to-do as a Markdown task list item, or None."""
    m = TODO.fullmatch(raw)
    spans = parse(m.group(1)) if m else None
    content = inline(spans[0].children, level) if spans and len(spans) == 1 else None
    if not content or content != content.strip() or "\n" in content:
        return None
    return f"- [ ] {content}"


def block(node, level, raw=""):
    """Return the Markdown for a paragraph, heading, list, to-do or code block, or None."""
    if node.name == "div" and node.cls == "notion-code no-wrap":
        return code_block(node)
    if node.name == "div" and node.cls == "notion-to-do":
        return todo(node, level, raw)
    if node.cls == PARAGRAPH and node.name == "p":
        content = inline(node.children, level)
        if not content or content.startswith((" ", "\t")):
            return None
        # Markdown would drop a trailing newline.
        return content[:-1] + "<br>" if content.endswith("\n") else content
    if node.name in ("h1", "h2", "h3") and node.cls == HEADING:
        content = inline(node.children, level)
        if (
            content
            and "\n" not in content
            and "<br>" not in content
            and not content.startswith(" ")
        ):
            return "#" * int(node.name[1]) + " " + content
        return None
    if node.name in ("ul", "ol") and node.cls in (
        "notion-bulleted-list",
        "notion-numbered-list",
    ):
        if node.name == "ol" and node.attrs != {
            "type": "1",
            "class": "notion-numbered-list",
        }:
            return None
        items = []
        for i, item in enumerate(
            child
            for child in node.children
            if not (isinstance(child, str) and not child.strip())
        ):
            if (
                isinstance(item, str)
                or item.name != "li"
                or item.cls != LIST_ITEM
                or set(item.attrs) - {"id", "class"}
            ):
                return None
            content = inline(item.children, level)
            if not content or content.startswith(" "):
                return None
            # Markdown would drop a trailing newline, and continuation lines are indented.
            if content.endswith("\n"):
                content = content[:-1] + "<br>"
            marker = "- " if node.name == "ul" else f"{i + 1}. "
            items.append(marker + content.replace("\n", "\n" + " " * len(marker)))
        return "\n".join(items)
    return None


def strip_ids(text):
    return re.sub(r' id="block-[^"]*"', "", text)


def elements(node):
    """Return an element's child elements, or None if it has text other than whitespace."""
    if any(isinstance(child, str) and child.strip() for child in node.children):
        return None
    return [child for child in node.children if not isinstance(child, str)]


def inner(node, text):
    return text[node.start + len(node.tag) : node.end - len(f"</{node.name}>")]


def summary_text(span):
    """Return the Markdown for a span's text, for a tag, or None."""
    if (
        not span
        or span.name != "span"
        or span.attrs != {"class": "notion-semantic-string"}
    ):
        return None
    content = inline(span.children, "common")
    if not content or content != content.lstrip() or "%}" in content:
        return None
    return content


def callout_tag(node, text, indent, candidates):
    """Return a callout as a {% callout %} tag, or None."""
    match = re.fullmatch(r"notion-callout(?: bg-(\w+)-light)? border", node.cls)
    children = elements(node)
    if (
        not match
        or not children
        or len(children) != 2
        or children[0].cls != "notion-callout__icon"
    ):
        return None
    icon = elements(children[0])
    expected = {
        "alt": "icon",
        "loading": "lazy",
        "width": "20",
        "height": "20",
        "class": "notion-icon",
        "style": "object-fit:contain;object-position:center",
    }
    if (
        not icon
        or len(icon) != 1
        or icon[0].name != "img"
        or {k: v for k, v in icon[0].attrs.items() if k != "src"} != expected
    ):
        return None
    content = children[1]
    blocks = elements(content)
    if content.attrs != {"class": "notion-callout__content"} or not blocks:
        return None
    body = summary_text(blocks[0])
    if body is None or "\n\n" in body:
        return None
    # Markdown would drop a trailing newline.
    if body.endswith("\n"):
        body = body[:-1] + "<br>"
    rest = text[blocks[0].end : content.end - len("</div>")]
    markdown = convert(rest, indent, candidates, tags=True) if rest.strip() else ""
    if markdown is None:
        return None
    color = match.group(1) or "default"
    body = f"{body}\n\n{markdown}" if markdown else body
    return f"{{% callout {color} {icon[0].attrs['src']} %}}\n{body}\n{{% endcallout %}}"


def toggle_tag(node, text, indent, candidates):
    """Return a toggle as a {% toggle %} tag, or None."""
    children = elements(node)
    if (
        not children
        or len(children) != 2
        or node.attrs != {"class": "notion-toggle closed"}
    ):
        return None
    summary, content = children
    parts = elements(summary)
    if (
        summary.attrs != {"class": "notion-toggle__summary"}
        or not parts
        or len(parts) != 2
    ):
        return None
    if strip_ids(text[parts[0].start : parts[0].end]) != (
        '<div class="notion-toggle__trigger"><div class="notion-toggle__trigger_icon"><span>‣</span></div></div>'
    ):
        return None
    title = summary_text(parts[1])
    if title is None or "\n" in title or "<br>" in title:
        return None
    if content.attrs != {"class": "notion-toggle__content", "style": "display:none"}:
        return None
    markdown = convert(inner(content, text), indent, candidates, tags=True)
    if markdown is None:
        return None
    return f"{{% toggle {title} %}}\n\n{markdown}\n\n{{% endtoggle %}}"


def width(value):
    """Round a column's width, e.g. 0.2500000000000001 to 0.25."""
    return f"{round(float(value), 4):g}"


def columns_tag(node, text, indent, candidates):
    """Return a column list as {% columns %} and {% column %} tags, or None."""
    columns = elements(node)
    if not columns or node.attrs != {"class": "notion-column-list"}:
        return None
    output = ["{% columns %}"]
    for index, column in enumerate(columns):
        match = re.fullmatch(
            r"width:calc\(\(100% - var\(--column-spacing\) \* (\d+)\) \* ([\d.]+)\)(;margin-inline-start:var\(--column-spacing\))?",
            column.attrs.get("style", ""),
        )
        if (
            column.name != "div"
            or set(column.attrs) != {"class", "style"}
            or column.cls != "notion-column"
            or not match
            or int(match.group(1)) != len(columns) - 1
            or bool(match.group(3)) != (index > 0)
        ):
            return None
        content = inner(column, text)
        markdown = (
            None if "{%" in content else convert(content, indent, candidates, tags=True)
        )
        if markdown is None:
            output.append(
                f"{{% column {width(match.group(2))} html %}}\n{indent(strip_ids(content))}\n{{% endcolumn %}}"
            )
        else:
            output.append(
                f"{{% column {width(match.group(2))} %}}\n\n{markdown}\n\n{{% endcolumn %}}"
            )
    output.append("{% endcolumns %}")
    return "\n".join(output)


def table_tag(node, text, indent, candidates):
    """Return a Notion table as a {% table %} tag, or None."""
    wrapper = elements(node)
    if (
        node.attrs != {"class": "notion-table__wrapper"}
        or not wrapper
        or len(wrapper) != 1
    ):
        return None
    table = wrapper[0]
    match = re.fullmatch(r"notion-table((?: col-header| row-header)*)", table.cls)
    bodies = elements(table)
    if (
        table.name != "table"
        or not match
        or set(table.attrs) != {"class"}
        or not bodies
        or len(bodies) != 1
    ):
        return None
    lines = []
    widths = None
    for tr in elements(bodies[0]) or []:
        style = tr.attrs.get("style")
        row = re.fullmatch(r"background:var\(--color-bg-(\w+)\)", style or "")
        if (
            tr.name != "tr"
            or set(tr.attrs) != {"style"}
            or not (row or style == "color:var(--color-text-default)")
        ):
            return None
        cells = []
        row_widths = []
        for td in elements(tr) or [None]:
            cell = re.fullmatch(
                r"min-width:([\d.]+)px;max-width:\1px(?:;background:var\(--color-(?:bg-(\w+)|color-(default))\))?",
                td.attrs.get("style", "") if td else "",
            )
            contents = elements(td) if td and cell else None
            if not contents or len(contents) != 1 or set(td.attrs) != {"style"}:
                return None
            row_widths.append(cell.group(1))
            color = cell.group(2) or cell.group(3)
            if (
                contents[0].attrs == {"class": "notion-table__empty-cell"}
                and not contents[0].children
            ):
                content = ""
            elif contents[0].attrs == {"class": "notion-table__cell"}:
                spans = elements(contents[0])
                content = summary_text(spans[0]) if spans and len(spans) == 1 else None
                if not content:
                    return None
                content = content.replace("\n", "<br>").replace("|", "\\|")
                if content.startswith("{"):
                    content = "\\" + content
            else:
                return None
            cells.append((f"{{{color}}} " if color else "") + content)
        if widths is None:
            widths = row_widths
        elif row_widths != widths:
            return None
        lines.append(
            (f"{{{row.group(1)}}} " if row else "") + "| " + " | ".join(cells) + " |"
        )
        if len(lines) == 1:
            lines.append("|" + "---|" * len(cells))
    if not widths:
        return None
    arguments = " ".join(
        f"{round(float(width), 2):g}" for width in widths
    ) + match.group(1)
    return f"{{% table {arguments} %}}\n" + "\n".join(lines) + "\n{% endtable %}"


def scalar(value):
    """Return a scalar as YAML, quoting strings (as JSON) only if necessary."""
    if (
        isinstance(value, str)
        and re.fullmatch(r"(?:[^\W\d_]|/)[^:#\n\"'{}\[\],&*!|>%@`]*", value)
        and value == value.strip()
        and value.lower()
        not in ("true", "false", "yes", "no", "on", "off", "null", "y", "n")
    ):
        return value
    return json.dumps(value, ensure_ascii=False)


CARD = re.compile(
    r'<div class="notion-collection-card gallery( no-click)?">'
    r'(?:<a href="(?P<link>[^"]*)" class="notion-link notion-collection-card__anchor">(?P<anchor>[^<]*)</a>)?'
    r'(?:<img alt="(?P<alt>[^"]*)" loading="lazy" width="(?:780|960)" height="200" '
    r'class="notion-collection-card__cover (?:medium|large)(?P<only> only-cover)?" '
    r'style="object-fit:cover;object-position:center (?P<position>[\d.]+)%" src="(?P<cover>[^"]*)"/>)?'
    r'(?:<div class="notion-collection-card__content notion-collection-card__property-list">'
    r'<div class="notion-property notion-property__title notion-collection-card__property title notion-semantic-string">'
    r'<div class="notion-property__title__icon-wrapper">'
    r'(?:<img alt="" loading="lazy" width="16" height="16" class="notion-icon" '
    r'style="object-fit:contain;object-position:center" src="(?P<icon>[^"]*)"/>|<svg class="notion-icon notion-icon__page"'
    r' viewBox="0 0 16 16" width="18" height="18" style="width:16px;[^"]*">.*?</svg>)'
    r"</div>(?P<title>[^<]*)</div></div>)?</div>",
    re.S,
)


def gallery_tag(node, text, indent, candidates):
    """Return a Notion gallery as a {% gallery %} tag, or None."""
    match = re.fullmatch(r"notion-collection-gallery (medium|large)", node.cls)
    cards = elements(node)
    if not match or set(node.attrs) != {"class"} or cards is None:
        return None
    items = []
    for card in cards:
        m = CARD.fullmatch(text[card.start : card.end])
        if not m or (m.group("title") is None) == (m.group("only") is None):
            return None
        title = m.group("title") if m.group("title") is not None else m.group("alt")
        if (m.group("anchor") is not None and m.group("anchor") != title) or (
            m.group("alt") is not None and m.group("alt") != title
        ):
            return None
        if bool(m.group(1)) == (m.group("link") is not None):
            return None
        item = {"title": html.unescape(title)}
        if m.group("link") is not None:
            item["link"] = html.unescape(m.group("link"))
        if m.group("icon"):
            item["icon"] = html.unescape(m.group("icon"))
        if m.group("cover"):
            item["cover"] = html.unescape(m.group("cover"))
            if (position := round(float(m.group("position")), 2)) != 50:
                item["cover_position"] = position
            if m.group("only"):
                item["cover_only"] = True
        items.append(
            "- " + "\n  ".join(f"{key}: {scalar(value)}" for key, value in item.items())
        )
    return (
        f"{{% gallery {match.group(1)} %}}\n" + "\n".join(items) + "\n{% endgallery %}"
    )


def database_tag(node, text, indent, candidates):
    """Return an inline Notion database as a {% database %} tag, or None."""
    children = elements(node)
    if (
        node.attrs != {"class": "notion-collection inline"}
        or not children
        or len(children) < 2
    ):
        return None
    header = elements(children[0])
    if (
        children[0].attrs != {"class": "notion-collection__header-wrapper"}
        or not header
        or len(header) != 1
    ):
        return None
    spans = elements(header[0])
    if (
        header[0].attrs != {"class": "notion-collection__header"}
        or not spans
        or len(spans) != 1
    ):
        return None
    title = "" if not spans[0].children else summary_text(spans[0])
    if title is None or "\n" in title or "<br>" in title:
        return None
    views = []
    for view in children[1:]:
        tag = TAGS.get(view.cls.split(" ")[0])
        markdown = tag(view, text, indent, candidates) if tag else None
        views.append(
            markdown
            if markdown is not None
            else indent(strip_ids(text[view.start : view.end]))
        )
    return f"{{% database {title} %}}\n" + "\n".join(views) + "\n{% enddatabase %}"


IMAGE = re.compile(
    r'<div class="notion-image(?P<align> align-start)? (?P<size>page-width|normal)"><img alt="image" loading="lazy" '
    r'width="(?P<width>[\d.]+)" height="(?P<height>[\d.]+)" style="(?P<style>[^"]*)" src="(?P<src>[^" ]*)"/></div>'
)


def image_tag(node, text, indent, candidates):
    """Return a Notion image block as an {% image %} tag, or None."""
    m = IMAGE.fullmatch(text[node.start : node.end])
    normal = m and m.group("size") == "normal"
    if not m or m.group("style") != (
        "height:auto"
        if normal
        else "object-fit:contain;object-position:center;height:auto"
    ):
        return None
    options = (" align-start" if m.group("align") else "") + (
        " normal" if normal else ""
    )
    width, height = (
        f"{round(float(m.group(key)), 2):g}" for key in ("width", "height")
    )
    return f"{{% image {html.unescape(m.group('src'))} {width} {height}{options} %}}"


# The front matter of the pages of the language of the page being converted, by permalink.
PAGES = {}
PAGE_LINK = re.compile(
    r'<a href="(?P<href>[^"]*)" class="notion-link notion-page"><span class="notion-page__icon">'
    r'<img alt="(?P<alt>[^"]*)" loading="lazy" class="notion-icon" style="position:absolute;height:100%;width:100%;'
    r'left:0;top:0;right:0;bottom:0;object-fit:cover;object-position:center;" src="(?P<src>[^"]*)"/></span>'
    r'<span class="notion-page__title notion-semantic-string">(?P<title>[^<]*)</span></a>'
)


def page_link(raw, argument=""):
    """Return a link to a page, with the page's icon and title, as a {% page %} tag, or None."""
    m = PAGE_LINK.fullmatch(raw)
    page = PAGES.get(html.unescape(m.group("href"))) if m else None
    if (
        not page
        or page.get("title") != html.unescape(m.group("title"))
        or m.group("alt") != m.group("title")
        or page.get("icon") != html.unescape(m.group("src"))
        or " " in m.group("href")
    ):
        return None
    return f"{{% page {html.unescape(m.group('href'))}{argument} %}}"


# Databases' table views' HTML (without IDs), mapped to {% database_table %} tags by import_pages.py, which also
# moves the views' cells into the items' front matter.
VIEWS = {}


def database_table_tag(node, text, indent, candidates):
    """Return a database's table view as a {% database_table %} tag, or None."""
    return VIEWS.get(text[node.start : node.end])


TAGS = {
    "notion-collection": database_tag,
    "notion-collection-gallery": gallery_tag,
    "notion-collection-table__wrapper": database_table_tag,
    "notion-callout": callout_tag,
    "notion-toggle": toggle_tag,
    "notion-column-list": columns_tag,
    "notion-table__wrapper": table_tag,
    "notion-image": image_tag,
}


def convert(text, indent, candidates, tags=False):
    """
    Return Markdown for a sequence of blocks, adding (Markdown, HTML) pairs to verify to ``candidates``.

    Each block's Markdown is a placeholder, replaced once verified. If ``tags``, use Liquid tags for complex blocks.
    """
    nodes = parse(text)
    output = []
    previous_list = None
    for node in nodes:
        if isinstance(node, str):
            if node.strip():
                REPORT["unconverted containers"].append(f"text: {node.strip()[:80]}")
                return None
            continue
        raw = text[node.start : node.end]
        if tags and (link := page_link(raw)):
            output.append(link)
            continue
        if node.name not in BLOCK:
            REPORT["unconverted containers"].append(f"inline element: {node.tag[:120]}")
            return None
        markdowns = [block(node, level, raw) for level in LEVELS]
        tag = TAGS.get(node.cls.split(" ")[0]) if tags and node.name == "div" else None
        if markdowns[-1] is not None:
            # Markdown would join adjacent lists of different kinds (to-dos and bulleted lists), unless separated by
            # an end-of-block marker, directly after the first list (after a blank line, the list would be loose).
            kind = "to-do" if node.cls == "notion-to-do" else node.name
            if kind in ("to-do", "ul", "ol") and previous_list not in (None, kind):
                output[-1] += "\n^"
            previous_list = kind if kind in ("to-do", "ul", "ol") else None
            key = f"\x00{len(candidates)}\x00"
            candidates.append((markdowns, strip_ids(raw), indent(strip_ids(raw))))
            output.append(key)
            continue
        previous_list = None
        if tag and (markdown := tag(node, text, indent, candidates)) is not None:
            output.append(markdown)
        elif node.name == "div" and (
            node.cls in CONTAINERS
            or node.cls in ("notion-column-list", "notion-toggle closed")
        ):
            output.append(container(node, text, indent, candidates))
        else:
            output.append(indent(strip_ids(raw)))
    return "\n\n".join(output)


def container(node, text, indent, candidates):
    """Return the HTML for a container, with Markdown enabled in columns and toggle contents where possible."""
    open_tag = strip_ids(node.tag)
    close_tag = f"</{node.name}>"
    inner = text[len(node.tag) + node.start : node.end - len(close_tag)]
    if node.cls in CONTAINERS and "{%" not in inner:
        markdown = convert(inner, indent, candidates)
        if markdown is not None:
            return f'{open_tag[:-1]} markdown="1">\n\n{markdown}\n\n{close_tag}'
    parts = []
    for child in node.children:
        if isinstance(child, str):
            parts.append(child.strip() and child)
        elif child.name == "div" and (
            child.cls in CONTAINERS
            or child.cls in ("notion-column-list", "notion-toggle closed")
        ):
            parts.append(container(child, text, indent, candidates))
        else:
            parts.append(indent(strip_ids(text[child.start : child.end])))
    return (
        open_tag + "\n" + "\n".join(part for part in parts if part) + "\n" + close_tag
    )


def render(markdowns, languages=None, pages=None):
    """Render Markdown with the site's Liquid tags and Markdown converter, given pages' front matter by language."""
    documents = [
        {"content": markdown, "lang": languages[i] if languages else "en"}
        for i, markdown in enumerate(markdowns)
    ]
    result = subprocess.run(
        ["bundle", "exec", "ruby", "scripts/render_markdown.rb"],
        input=json.dumps({"documents": documents, "pages": pages or {}}),
        capture_output=True,
        text=True,
        check=True,
        cwd=ROOT,
    )
    return json.loads(result.stdout)


def normalize(text):
    """Return a canonical form of HTML, ignoring differences that don't render (in pre-wrap, a newline is a <br>)."""
    output = []
    stack = [False]
    for token in TOKEN.findall(text):
        if token.startswith("<!--"):
            continue
        if token.startswith("</"):
            name = token[2:-1].strip().lower()
            if name not in VOID:
                stack.pop()
                output.append(f"</{name}>")
        elif token.startswith("<"):
            element = Element(token, 0)
            if element.name == "br":
                output.append("\n")
                continue
            attrs = {
                k: v
                for k, v in element.attrs.items()
                if k not in ("target", "rel", "markdown")
            }
            output.append(
                f"<{element.name} "
                + " ".join(
                    f"{k}={html.unescape(v)!r}" for k, v in sorted(attrs.items())
                )
                + ">"
            )
            if element.name not in VOID and not token.endswith("/>"):
                stack.append(stack[-1] or bool(PRESERVE.search(element.cls)))
        elif stack[-1]:
            output.append(html.unescape(token))
        elif token.strip():
            output.append(html.unescape(token.strip()))
    text = "".join(output)
    # Images' dimensions are rounded.
    text = re.sub(
        r"\b(width|height)='([\d.]+)'",
        lambda m: f"{m.group(1)}='{round(float(m.group(2)), 2):g}'",
        text,
    )
    # Cover positions are rounded.
    text = re.sub(
        r"object-position:center ([\d.]+)%",
        lambda m: f"object-position:center {round(float(m.group(1)), 2):g}%",
        text,
    )
    # Table cells' widths are rounded to pixels.
    text = re.sub(
        r"(min|max)-width:([\d.]+)px",
        lambda m: f"{m.group(1)}-width:{round(float(m.group(2)), 2):g}px",
        text,
    )
    # Column widths are rounded.
    text = re.sub(r"\* ([\d.]{7,})\)", lambda m: f"* {width(m.group(1))})", text)
    # Spaces before a line break don't render (white-space: pre-wrap).
    text = re.sub(r" +\n", "\n", text)
    # Spaces at the edges of bold or italic text are moved outside it. Nested or consecutive bold (or italic) is
    # bold, and the order of nested bold and italic doesn't matter.
    previous = None
    while previous != text:
        previous = text
        text = re.sub(r"<(strong|em) >( +)", r"\2<\1 >", text)
        text = re.sub(r"( +)</(strong|em)>", r"</\2>\1", text)
        text = re.sub(
            r"<(strong|em) ><\1 >((?:(?!</?\1 ).)*)</\1></\1>", r"<\1 >\2</\1>", text
        )
        text = re.sub(
            r"<em ><strong >((?:(?!</?(?:em|strong) ).)*)</strong></em>",
            r"<strong ><em >\1</em></strong>",
            text,
        )
        text = re.sub(r"</(strong|em)>( *)<\1 >", r"\2", text)
        text = re.sub(r" +\n", "\n", text)
    # Trailing spaces in a block don't render (white-space: pre-wrap), and Markdown drops them.
    text = re.sub(r" +(</(?:p|li|h1|h2|h3)>)", r"\1", text)
    return re.sub(
        r" +(</span>)(?=</div>|</h[1-6]>|<(?:div|p|ul|ol|h[1-6]) |<a class='notion-link notion-page')",
        r"\1",
        text,
    )


# The HTML that includes render, by filename, for includes that contain Liquid tags.
INCLUDES = {}


def expand_includes(text):
    """Replace {% include %} tags with the included files' HTML, to compare with rendered Liquid."""
    return re.sub(
        r"\{% include ([\w.-]+) %\}",
        lambda m: (
            INCLUDES.get(m.group(1)) or (ROOT / "_includes" / m.group(1)).read_text()
        ),
        text,
    )


def report_page(expected, actual, draft=""):
    i = next(
        (i for i, (a, b) in enumerate(zip(expected, actual)) if a != b),
        min(len(expected), len(actual)),
    )
    REPORT["unconverted pages"].append(
        {
            "expected": expected[max(0, i - 300) : i + 300],
            "actual": actual[max(0, i - 300) : i + 300],
            "draft": draft,
        }
    )


def to_markdown(pages, indent, languages, front_matter):
    """
    Convert each page's HTML to Markdown, keeping HTML for blocks that wouldn't render the same.

    Use Liquid tags for complex blocks, unless the page wouldn't render the same.
    """
    candidates = []
    drafts = []
    for content, language in zip(pages, languages):
        PAGES.clear()
        PAGES.update(front_matter[language])
        drafts.append(
            [
                convert(strip_ids(content), indent, candidates, tags)
                if content.strip()
                else ""
                for tags in (True, False)
            ]
        )

    # Render each block's Markdown at each escaping level, and use the lowest level that renders the same HTML.
    rendered = iter(
        render(
            [markdown or "" for markdowns, _, _ in candidates for markdown in markdowns]
        )
    )
    results = []
    for markdowns, original, raw in candidates:
        outputs = [next(rendered) for _ in markdowns]
        expected = normalize(original)
        for markdown, output in zip(markdowns, outputs):
            if markdown is not None and normalize(output) == expected:
                results.append(markdown)
                break
        else:
            results.append(raw)
            REPORT["unconverted blocks"].append(
                {
                    "markdown": markdowns[-1],
                    "expected": expected,
                    "actual": normalize(outputs[-1]),
                }
            )

    def fill(draft):
        return (
            None
            if draft is None
            else re.sub(r"\x00(\d+)\x00", lambda m: results[int(m.group(1))], draft)
        )

    filled = [[fill(draft) for draft in pair] for pair in drafts]
    verified = iter(
        render(
            [draft or "" for pair in filled for draft in pair],
            [language for language in languages for _ in (True, False)],
            front_matter,
        )
    )
    final = []
    tagged = 0
    for content, pair in zip(pages, filled):
        expected = normalize(expand_includes(strip_ids(content)))
        outputs = [next(verified) for _ in pair]
        for i, (draft, output) in enumerate(zip(pair, outputs)):
            if draft is not None and normalize(output) == expected:
                final.append(draft)
                tagged += i == 0
                break
            if draft is not None:
                report_page(expected, normalize(output), draft)
        else:
            final.append(None)
    (ROOT / ".crawl" / "markdown-report.json").write_text(
        json.dumps(REPORT, indent=1, ensure_ascii=False)
    )
    stats = sum(r in c[0] for r, c in zip(results, candidates)), len(candidates), tagged
    return final, stats
