"""Crawl the Super.so sites from their sitemaps, following internal links, into .crawl/."""

import concurrent.futures as cf, json, os, re, urllib.parse, urllib.request, html

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".crawl")
HOSTS = ["sustainable.open-contracting.org", "sostenibilidad.open-contracting.org", "achatdurable.open-contracting.org"]
UA = "Mozilla/5.0 (Macintosh) crawl-for-migration"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.geturl(), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, url, ""
    except Exception as e:
        return -1, url, str(e)

def process(url):
    status, final, body = fetch(url)
    p = urllib.parse.urlparse(url)
    path = p.path.strip("/") or "index"
    fn = os.path.join(OUT, p.netloc, path + ".html")
    os.makedirs(os.path.dirname(fn), exist_ok=True)
    if status == 200:
        open(fn, "w").write(body)
    s = body.replace('\\"', '"')
    m = re.search(r'"pageId":"([0-9a-f]{32})","pagesToCreate"', s)
    t = re.search(r"<title>([^<]*)", body)
    hrefs = set(html.unescape(h) for h in re.findall(r'href="([^"#]*)', body))
    links = sorted(h for h in hrefs if h.startswith("/") and not h.startswith("/_next") or any(x in h for x in HOSTS))
    return {"url": url, "status": status, "final": final, "pageId": m and m.group(1),
            "title": t and html.unescape(t.group(1)), "links": links}

def main():
    urls = []
    for h in HOSTS:
        _, _, sm = fetch(f"https://{h}/sitemap.xml")
        urls += re.findall(r"<loc>([^<]+)</loc>", sm)
    seen, results = set(urls), {}
    todo = list(urls)
    with cf.ThreadPoolExecutor(8) as ex:
        while todo:
            for r in ex.map(process, todo):
                results[r["url"]] = r
            todo = []
            for r in list(results.values()):
                host = urllib.parse.urlparse(r["url"]).netloc
                for l in r["links"]:
                    u = urllib.parse.urljoin(f"https://{host}/", l).split("?")[0].rstrip("/")
                    if urllib.parse.urlparse(u).path == "": u += "/"
                    if urllib.parse.urlparse(u).netloc in HOSTS and u not in seen:
                        seen.add(u); todo.append(u)
            print("discovered", len(todo), flush=True)
    json.dump(list(results.values()), open(os.path.join(OUT, "results.json"), "w"), indent=1, ensure_ascii=False)
    print(len(results))

main()
