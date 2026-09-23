"""Download the images and files that the crawled Super.so pages reference into assets/."""

import concurrent.futures
import hashlib
import html
import json
import mimetypes
import re
import shutil
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRAWL = ROOT / ".crawl"
IMAGES = ROOT / "assets" / "images"
IMAGE = re.compile(
    r"https://images\.spr\.so/cdn-cgi/imagedelivery/([^/]+)/([^/]+)/([^/\"]+)/"
)
FILE = re.compile(
    r"https://assets\.super\.so/[0-9a-f-]+/(?:files|images|uploads)/[^\"\\&?\s]+"
)
# The variant that Super.so serves. The "public" variant is limited to 768px.
VARIANT = "w=1920,quality=90,fit=scale-down"
EXTENSIONS = {"image/jpeg": ".jpg", "image/svg+xml": ".svg", "image/x-icon": ".ico"}


def fetch(url, path, add_extension):
    # Each image is alone in a directory named by its UUID.
    if (
        add_extension and path.parent.exists() and any(path.parent.iterdir())
    ) or path.exists():
        return None
    request = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (migration)"}
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read()
            content_type = response.headers.get_content_type()
    except Exception as e:
        return f"{url}: {e}"
    if add_extension:
        path = path.with_name(
            path.name
            + (EXTENSIONS.get(content_type) or mimetypes.guess_extension(content_type))
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return None


def main():
    jobs = {}
    for path in CRAWL.rglob("*.html"):
        text = html.unescape(urllib.parse.unquote(path.read_text()))
        for account, uuid, name in IMAGE.findall(text):
            url = f"https://images.spr.so/cdn-cgi/imagedelivery/{account}/{uuid}/{name}/{VARIANT}"
            jobs[url] = (CRAWL / "images" / uuid / name, True)
        for url in FILE.findall(text):
            jobs[url] = (
                ROOT / "assets" / "super" / urllib.parse.urlparse(url).path.lstrip("/"),
                False,
            )
    with concurrent.futures.ThreadPoolExecutor(8) as executor:
        errors = [
            e
            for e in executor.map(lambda item: fetch(item[0], *item[1]), jobs.items())
            if e
        ]
    print(len(jobs), "assets,", len(errors), "errors")
    json.dump(errors, open(CRAWL / "asset-errors.json", "w"), indent=1)
    deduplicate()


def deduplicate():
    """Copy each distinct image in .crawl/images/<uuid>/ to assets/images/, and map UUIDs to paths in .crawl/images.json."""
    shutil.rmtree(IMAGES, ignore_errors=True)
    IMAGES.mkdir(parents=True)
    paths = {}
    mapping = {}
    for directory in sorted((CRAWL / "images").iterdir()):
        source = next(directory.iterdir())
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if digest not in paths:
            target = IMAGES / source.name
            n = 1
            while target.exists():
                n += 1
                target = IMAGES / f"{source.stem}-{n}{source.suffix}"
            shutil.copyfile(source, target)
            paths[digest] = f"/assets/images/{target.name}"
        mapping[directory.name] = paths[digest]
    json.dump(mapping, open(CRAWL / "images.json", "w"), indent=1, sort_keys=True)
    print(len(mapping), "images,", len(paths), "distinct")


if __name__ == "__main__":
    main()
