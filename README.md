# Open and Sustainable Public Procurement toolkit

A static copy of the three Super.so sites (backed by Notion), built with Jekyll for Cloudflare Pages:

| Directory | Site |
| --- | --- |
| `en/` | sustainable.open-contracting.org |
| `es/` | sostenibilidad.open-contracting.org |
| `fr/` | achatdurable.open-contracting.org |

## Run locally

```bash
bundle install
bundle exec jekyll serve --config _config.yml,_config.en.yml  # or _config.es.yml, _config.fr.yml
```

Each build writes to `_site/<lang>/`, which is the output directory for that site's Cloudflare Pages project. Google Analytics is included only when `JEKYLL_ENV=production`.

## How the content was produced

The pages are the server-rendered HTML of the live sites, not the Notion export, because the export loses toggles, columns, gallery views, icons and covers.

1. `python3 scripts/crawl.py` crawls each site's sitemap (and any linked page not in it) into `.crawl/`, recording each URL's status and Notion page ID in `.crawl/results.json`.
1. `python3 scripts/download_assets.py` downloads the images and files the pages reference into `assets/`.
1. `python3 scripts/import_pages.py` writes each page's `<main>` element to `<lang>/<path>.html`, with the page's metadata as front matter, and writes each site's `_redirects` and `assets/css/theme-<lang>.css`. The redirects are for URLs that Super.so redirected (Notion page IDs and other capitalizations), and for URLs of pages that Super.so lists but no longer renders, if a live page has the same final path segment. The latter are read from `.crawl/super-so-pages.csv`, exported from the Super.so dashboard.

`import_pages.py` deletes and rewrites `en/`, `es/` and `fr/`.

The stylesheets in `assets/css/` (except `fonts.css` and `theme-*.css`) are Super.so's own. `assets/js/site.js` replaces the Super.so behavior that the pages need: toggles and code block copy buttons. `sitemap.xml`, `robots.txt` and `404.html` replace the ones Super.so generated.
