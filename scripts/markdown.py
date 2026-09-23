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


def inline(nodes, level, start_of_line=True):
    """Return the Markdown for inline content, or None."""
    output = []
    for node in nodes:
        at_start = (
            start_of_line and not output or (output and output[-1].endswith("\n"))
        )
        if isinstance(node, str):
            text = html.unescape(node)
            # A newline is a line break (white-space: pre-wrap), but a blank line would end the paragraph.
            lines = text.split("\n")
            parts = []
            for i, line in enumerate(lines):
                if line.endswith("  ") and i < len(lines) - 1:
                    return None  # would be a hard line break
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
            if content and content == content.strip() and "\n" not in content:
                output.append(f"{marker}{content}{marker}")
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


def block(node, level):
    """Return the Markdown for a paragraph, heading or list, or None."""
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
            if not content or content.startswith(" ") or "\n" in content:
                return None
            items.append(("- " if node.name == "ul" else f"{i + 1}. ") + content)
        return "\n".join(items)
    return None


def strip_ids(text):
    return re.sub(r' id="block-[^"]*"', "", text)


def convert(text, indent, candidates):
    """
    Return Markdown for a sequence of blocks, adding (Markdown, HTML) pairs to verify to ``candidates``.

    Each block's Markdown is a placeholder, replaced once verified.
    """
    nodes = parse(text)
    output = []
    for node in nodes:
        if isinstance(node, str):
            if node.strip():
                REPORT["unconverted containers"].append(f"text: {node.strip()[:80]}")
                return None
            continue
        raw = text[node.start : node.end]
        if node.name not in BLOCK:
            REPORT["unconverted containers"].append(f"inline element: {node.tag[:120]}")
            return None
        markdowns = [block(node, level) for level in LEVELS]
        if markdowns[-1] is not None:
            key = f"\x00{len(candidates)}\x00"
            candidates.append((markdowns, strip_ids(raw), indent(strip_ids(raw))))
            output.append(key)
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


def render(markdowns):
    """Render Markdown with the site's Markdown converter."""
    result = subprocess.run(
        ["bundle", "exec", "ruby", "scripts/render_markdown.rb"],
        input=json.dumps(markdowns),
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
    # Trailing spaces in a block don't render (white-space: pre-wrap), and Markdown drops them.
    text = re.sub(r" +(</(?:p|li|h1|h2|h3)>)", r"\1", text)
    # Nested bold is bold, and the order of nested bold and italic doesn't matter.
    while re.search(r"<(strong|em) ><\1 >", text):
        text = re.sub(
            r"<(strong|em) ><\1 >((?:(?!</?\1 ).)*)</\1></\1>", r"<\1 >\2</\1>", text
        )
    return re.sub(
        r"<em ><strong >((?:(?!</?(?:em|strong) ).)*)</strong></em>",
        r"<strong ><em >\1</em></strong>",
        text,
    )


def to_markdown(pages, indent):
    """Convert each page's HTML to Markdown, keeping HTML for blocks that wouldn't render the same."""
    candidates = []
    drafts = [
        convert(content, indent, candidates) if content.strip() else ""
        for content in pages
    ]
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
        return re.sub(r"\x00(\d+)\x00", lambda m: results[int(m.group(1))], draft)

    outputs = []
    for content, draft in zip(pages, drafts):
        outputs.append(None if draft is None else fill(draft))
    verified = render([output or "" for output in outputs])
    final = []
    for content, output, html_ in zip(pages, outputs, verified):
        if output is not None and normalize(html_) == normalize(strip_ids(content)):
            final.append(output)
        else:
            final.append(None)
            if output is not None:
                expected, actual = normalize(strip_ids(content)), normalize(html_)
                i = next(
                    (i for i, (a, b) in enumerate(zip(expected, actual)) if a != b),
                    min(len(expected), len(actual)),
                )
                REPORT["unconverted pages"].append(
                    {
                        "expected": expected[max(0, i - 300) : i + 300],
                        "actual": actual[max(0, i - 300) : i + 300],
                    }
                )
    (ROOT / ".crawl" / "markdown-report.json").write_text(
        json.dumps(REPORT, indent=1, ensure_ascii=False)
    )
    stats = sum(r in c[0] for r, c in zip(results, candidates)), len(candidates)
    return final, stats
