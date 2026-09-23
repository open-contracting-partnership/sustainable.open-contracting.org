# /// script
# dependencies = ["playwright", "pillow"]
# ///
"""
Screenshot every built page, or compare two sets of screenshots.

    uv run scripts/screenshots.py take NAME [PATH ...]
    uv run scripts/screenshots.py compare NAME1 NAME2

Screenshots are saved to .crawl/screenshots/NAME/<lang>/<path>.png. Build the sites first.
"""

import asyncio
import mimetypes
import sys
import urllib.parse
from pathlib import Path

from PIL import Image, ImageChops
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
SCREENSHOTS = ROOT / ".crawl" / "screenshots"
LANGUAGES = ("en", "es", "fr")
CONCURRENCY = 8
# Differences in anti-aliasing (e.g. of box shadows) vary between runs.
TOLERANCE = 8

# Load lazy images and wait until they and the fonts are painted, so that screenshots are deterministic.
READY = """async () => {
  document.querySelectorAll("img[loading=lazy]").forEach((img) => (img.loading = "eager"));
  await Promise.all([...document.images].map((img) => img.decode().catch(() => {})));
  await document.fonts.ready;
  await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
}"""


def pages(lang):
    for path in sorted((SITE / lang).rglob("*.html")):
        relative = path.relative_to(SITE / lang).with_suffix("")
        if relative.name != "404":
            yield (
                "/"
                if relative.name == "index" and relative.parent == Path(".")
                else f"/{relative}"
            )


def resolve(lang, url_path):
    path = SITE / lang / urllib.parse.unquote(url_path).lstrip("/")
    for candidate in (path, path.with_name(path.name + ".html"), path / "index.html"):
        if candidate.is_file():
            return candidate
    return None


async def take(name, only):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        semaphore = asyncio.Semaphore(CONCURRENCY)

        async def shoot(lang, url_path):
            async with semaphore:
                page = await browser.new_page(viewport={"width": 1440, "height": 900})

                async def route(route):
                    url = urllib.parse.urlparse(route.request.url)
                    file = (
                        resolve(lang, url.path)
                        if url.hostname == f"{lang}.test"
                        else None
                    )
                    if file:
                        content_type = (
                            mimetypes.guess_type(file.name)[0]
                            or "application/octet-stream"
                        )
                        await route.fulfill(
                            body=file.read_bytes(), content_type=content_type
                        )
                    else:
                        await route.abort()

                await page.route("**/*", route)
                await page.goto(f"http://{lang}.test{url_path}", wait_until="load")
                await page.evaluate(READY)
                output = (
                    SCREENSHOTS
                    / name
                    / lang
                    / ((url_path.strip("/") or "index") + ".png")
                )
                output.parent.mkdir(parents=True, exist_ok=True)
                # Rendering can lag behind the ready checks, so repeat until two screenshots agree.
                previous = None
                for _ in range(10):
                    screenshot = await page.screenshot(full_page=True)
                    if screenshot == previous:
                        break
                    previous = screenshot
                else:
                    print(f"unstable {lang}{url_path}")
                output.write_bytes(screenshot)
                await page.close()

        await asyncio.gather(
            *(
                shoot(lang, url_path)
                for lang in LANGUAGES
                for url_path in pages(lang)
                if not only or url_path in only
            )
        )
        await browser.close()


def compare(a, b):
    changed = 0
    for path in sorted((SCREENSHOTS / a).rglob("*.png")):
        relative = path.relative_to(SCREENSHOTS / a)
        other = SCREENSHOTS / b / relative
        if not other.exists():
            print(f"missing  {relative}")
            changed += 1
            continue
        image_a, image_b = (
            Image.open(path).convert("RGB"),
            Image.open(other).convert("RGB"),
        )
        if image_a.size != image_b.size:
            print(f"size     {relative} {image_a.size} -> {image_b.size}")
            changed += 1
        elif bbox := (
            ImageChops.difference(image_a, image_b)
            .convert("L")
            .point(lambda value: 255 if value > TOLERANCE else 0)
            .getbbox()
        ):
            print(f"pixels   {relative} {bbox}")
            changed += 1
    print(f"{changed} changed")


if __name__ == "__main__":
    if sys.argv[1] == "take":
        asyncio.run(take(sys.argv[2], set(sys.argv[3:])))
    else:
        compare(sys.argv[2], sys.argv[3])
