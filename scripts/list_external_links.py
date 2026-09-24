"""
Write .crawl/external-links.csv: each link to another website, with its context, whether the page's versions in the
other languages link to it too, and optionally whether it loads.

    uv run scripts/list_external_links.py [--check]

Build the sites first. A page's versions are matched by translations.py. With --check, each URL is requested with curl
(following redirects, as a browser), and its final status (or curl's error) and final URL are recorded.
"""

import collections
import concurrent.futures
import csv
import html
import subprocess
import sys
import urllib.parse
from pathlib import Path

import translations
from check_links import DOMAINS, SITE
from list_links import Links

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".crawl" / "external-links.csv"
HEADER = [
    "site",
    "page",
    "link text",
    "context",
    "url",
    "versions",
    "versions linking to it",
    "versions' other links",
    "status",
    "final url",
]
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def status(url):
    """Return a URL's final status (or curl's error) and final URL, as a browser would load it."""
    result = subprocess.run(
        [
            "curl",
            "-s",
            "-o",
            "/dev/null",
            "-L",
            "--max-time",
            "30",
            "-A",
            USER_AGENT,
            "-w",
            "%{http_code} %{url_effective}",
            url,
        ],
        capture_output=True,
        text=True,
    )
    code, _, final = result.stdout.partition(" ")
    if result.returncode:
        return f"error: curl {result.returncode}", final
    return code, final


def main():
    check = "--check" in sys.argv
    matches = translations.matches()
    # Each page's versions, by site and path.
    versions = collections.defaultdict(dict)
    for lang, matched in matches.items():
        for english, (other, _) in matched.items():
            versions[("en", english)][lang] = other
            versions[(lang, other)]["en"] = english
    for key, found in list(versions.items()):
        if key[0] != "en" and "en" in found:
            for lang, other in versions[("en", found["en"])].items():
                if lang != key[0]:
                    found[lang] = other

    links = collections.defaultdict(list)  # by site and page
    for lang in DOMAINS.values():
        for file in sorted((SITE / lang).rglob("*.html")):
            if "pagefind" in file.parts or file.name == "404.html":
                continue
            page = "/" + str(
                file.relative_to(SITE / lang).with_suffix("")
            ).removesuffix("index")
            page = page.rstrip("/") or "/"
            parser = Links()
            parser.feed(file.read_text())
            for record in parser.links:
                url = html.unescape(record["href"])
                parsed = urllib.parse.urlsplit(url)
                if parsed.scheme in ("http", "https") and parsed.netloc not in DOMAINS:
                    links[(lang, page)].append((record, url))

    statuses = {}
    if check:
        urls = sorted({url for records in links.values() for _, url in records})
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            statuses = dict(zip(urls, executor.map(status, urls)))

    rows = []
    for (lang, page), records in sorted(links.items()):
        page_versions = versions.get((lang, page), {})
        version_urls = {
            other_lang: {url for _, url in links.get((other_lang, path), [])}
            for other_lang, path in page_versions.items()
        }
        own = {url for _, url in records}
        for record, url in records:
            linking = [
                other_lang
                for other_lang, urls in sorted(version_urls.items())
                if url in urls
            ]
            others = sorted(
                {other for urls in version_urls.values() for other in urls - own}
            )
            rows.append(
                [
                    lang,
                    page,
                    record["link text"],
                    record["context"],
                    url,
                    " ".join(
                        f"{other_lang}:{path}"
                        for other_lang, path in sorted(page_versions.items())
                    ),
                    " ".join(linking),
                    " ".join(others),
                    statuses.get(url, ("", ""))[0],
                    # The final URL, if the URL redirects.
                    ""
                    if statuses.get(url, ("", url))[1] in ("", url)
                    else statuses[url][1],
                ]
            )

    with OUT.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(rows)
    print(len(rows), "links written to", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
