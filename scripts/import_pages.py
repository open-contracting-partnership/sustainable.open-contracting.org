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
        filename.write_text(front_matter(data) + localize(content) + "\n")

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
