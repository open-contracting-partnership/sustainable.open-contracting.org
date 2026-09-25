"""
List problems in the text of the built sites' pages, and exit with 1 if any.

    uv run scripts/check_markup.py

Build the sites first. In each page's <article>, outside code, it reports:

- Markdown, Liquid or HTML syntax in the text, which didn't render
- links whose text starts or ends with a space or punctuation, which belong outside the link, unless the link is a
  whole block or sentence (like a reference in a list), or ends with an abbreviation
- bold or italics that are empty or only punctuation
- bold or italics that only spaces (or a link's edges) separate from the next bold or italics, which can be one span
- non-breaking spaces at the end of a block or line
"""

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "_site"

SYNTAX = {
    "asterisk": r"\*",
    "underscore": r"(?<![\w/])__?\w|\w__?(?![\w/])",
    "link": r"\]\(",
    "liquid": r"\{%|%\}|\{\{|\}\}",
    "color": r"\{(?:default|gray|brown|orange|yellow|green|blue|purple|pink|red)\}",
    "tag": r"</?[a-z][a-z0-9]*(?:\s[^<>]*)?/?>",
    "backslash": r"\\",
    "table": r"\s\|\s",
}
# Question and exclamation marks are usually part of a title.
END_PUNCTUATION = ".,;:…"
# Single quotation marks as escapes, since ruff confuses the left one with a grave accent.
PAIRS = {"(": ")", "[": "]", "“": "”", "\N{LEFT SINGLE QUOTATION MARK}": "\N{RIGHT SINGLE QUOTATION MARK}", "«": "»"}
CLOSERS = {v: k for k, v in PAIRS.items()}
SKIP = {"code", "pre", "script", "style"}
BLOCKS = {
    "p",
    "li",
    "td",
    "th",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "div",
    "blockquote",
    "summary",
}
# The text before a link that starts a block or a sentence.
STARTS = re.compile(r"(?:^|[.!?:]\s|\n)[\s“«(]*\Z")


def link_problem(text, before, after):
    if text != text.strip():
        return "space"
    if text[-1] in END_PUNCTUATION:
        whole_block = not after.strip(" \n\xa0”»)")
        whole_sentence = text[-1] in ".…" and re.match(r"[”»)]*(\s|\Z)", after)
        abbreviation = re.search(r"(?:\b\w\.){2,}\Z", text)
        if not (STARTS.search(before) and (whole_block or whole_sentence)) and not abbreviation:
            return "punctuation"
    if text[0] in PAIRS and (text.endswith(PAIRS[text[0]]) or PAIRS[text[0]] not in text):
        return "punctuation"
    if text[-1] in CLOSERS and CLOSERS[text[-1]] not in text:
        return "punctuation"
    return None


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.article = 0
        self.skip = 0
        self.stack = []  # [tag, text, block text before it] of open a, strong and em elements
        self.block = ""  # the text of the current block so far
        self.pending = None  # a link's text and the block text before it, awaiting the text after it
        self.closed = {}  # the length of the block text when each of strong and em last closed
        self.problems = []

    def check(self, after):
        if self.pending:
            text, before = self.pending
            self.pending = None
            if problem := link_problem(text, before, after):
                self.problems.append(f"link text with {problem} at an end: {text!r}")

    def end_line(self):
        line = self.block.rsplit("\n", 1)[-1].rstrip(" \n\t")
        if line.endswith("\xa0"):
            self.problems.append(f"non-breaking space at the end of a line: {line[-40:]!r}")

    def handle_starttag(self, tag, _attrs):
        if tag == "article":
            self.article += 1
        elif tag in SKIP:
            self.skip += 1
        elif not self.article or self.skip:
            return
        elif tag in BLOCKS:
            self.check("")
            self.end_line()
            self.block = ""
            self.closed = {}
        elif tag == "br":
            self.check("\n")
            self.end_line()
            self.block += "\n"
        elif tag in {"a", "strong", "em"}:
            if tag in self.closed and not self.block[self.closed[tag] :].strip(" \xa0"):
                self.problems.append(f"{tag} split only by spaces: {self.block[-60:]!r}")
            self.stack.append([tag, "", self.block])

    def handle_endtag(self, tag):
        if tag == "article":
            self.article -= 1
        elif tag in SKIP:
            self.skip -= 1
        elif tag in BLOCKS:
            self.check("")
            self.end_line()
            self.block = ""
            self.closed = {}
        elif self.stack and self.stack[-1][0] == tag:
            tag, text, before = self.stack.pop()
            for parent in self.stack:
                parent[1] += text
            if tag == "a":
                # Links without text are images, like gallery cards' covers. A URL's punctuation is part of it.
                if text.strip() and not re.match(r"https?://", text):
                    self.check("")
                    self.pending = (text, before)
            elif not text.strip(" \n\xa0.,;:!?()"):
                self.problems.append(f"{tag} without words: {text!r}")
            if tag != "a" and not any(parent[0] == tag for parent in self.stack):
                self.closed[tag] = len(self.block)

    def handle_data(self, data):
        if not self.article or self.skip:
            return
        self.check(data)
        self.block += data
        for parent in self.stack:
            parent[1] += data
        for name, pattern in SYNTAX.items():
            for m in re.finditer(pattern, data):
                context = data[max(0, m.start() - 40) : m.end() + 40].replace("\n", " ")
                self.problems.append(f"{name} syntax: {context!r}")


def main():
    count = 0
    for path in sorted(SITE.rglob("*.html")):
        page = Page()
        page.feed(path.read_text())
        page.check("")
        for problem in page.problems:
            count += 1
            print(f"{path.relative_to(SITE)}: {problem}")
    return 1 if count else 0


if __name__ == "__main__":
    sys.exit(main())
