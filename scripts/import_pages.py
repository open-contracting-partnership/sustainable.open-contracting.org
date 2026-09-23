"""Convert the crawled Super.so pages in .crawl/ into Jekyll pages in en/, es/ and fr/."""

import html
import json
import re
import shutil
import urllib.parse
from pathlib import Path

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
    text = re.sub(r"<img [^>]*>", clean_image, text)
    return text


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
            if name in BLOCK and not preserving:
                output.append("\n" + "  " * len(stack))
                if stack:
                    stack[-1][1] = True
            output.append(token)
            if name not in VOID and not token.endswith("/>"):
                stack.append([preserving or bool(PRESERVE.search(token)), False])
        else:
            output.append(token)
    return "".join(output).strip()


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
        host = urllib.parse.urlparse(r["url"]).netloc
        lang = SITES[host]
        path = urllib.parse.urlparse(r["url"]).path.rstrip("/") or "/"
        slugs[(lang, r["pageId"])] = path

        document = crawled_path(r["url"]).read_text()
        head = document[: document.index("<body")]
        main_id, main_class, content = MAIN.search(document).groups()
        content = re.sub(r"<script.*?</script>", "", content, flags=re.S)

        data = {
            "layout": "default",
            "permalink": path,
            "title": html.unescape(re.search(r"<title>([^<]*)</title>", head).group(1)),
            "description": meta(head, "name", "description"),
            "image": meta(head, "property", "og:image"),
            "notion_id": r["pageId"],
            "main_id": main_id,
            "main_class": main_class,
            # Notion text can contain "{{" or "{%".
            "render_with_liquid": False,
        }
        data = {
            key: localize(value) if isinstance(value, str) else value
            for key, value in data.items()
        }
        filename = ROOT / lang / ((path.strip("/") or "index") + ".html")
        filename.parent.mkdir(parents=True, exist_ok=True)
        filename.write_text(
            front_matter(data) + indent(clean(localize(content))) + "\n"
        )

    # Super.so serves each page at its Notion ID, and some pages at other capitalizations, and redirects to the slug.
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
        lines = [
            f"{source} {target} 301"
            for source, target in sorted(rules.items())
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
