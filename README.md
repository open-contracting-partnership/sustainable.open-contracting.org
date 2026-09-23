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

## Pages

Each page is `<lang>/<path>.md`, with front matter:

| Key | Description |
| --- | --- |
| `permalink` | The page's URL path, which is also the path of its file |
| `title` | The page's title |
| `description` | The page's meta description |
| `cover` | The header's cover image, also used as the social media image |
| `cover_position` | The cover's vertical position, as a percentage (default 50) |
| `icon` | The header's icon, also used in breadcrumbs |
| `full_width` | Whether the page is full width |
| `collection` | Whether the page is a Notion database |
| `notion_id` | The ID of the Notion page from which it was imported |
| `sidebar` | Whether the page has the sidebar |
| `properties` | A database item's properties, in order, rendered by the `{% properties %}` tag in the layout: a mapping of pills to their colors, a list of mappings of attachments' names to their URLs, a number, or text. The `notion.date_properties` and `notion.url_properties` settings in `_config.yml` name the properties that are dates and URLs. |

The layout renders the breadcrumbs (from the pages at each prefix of the path) and the header, and the sidebar (in `_includes/sidebar-<lang>.html`) if a page has `sidebar: true`. The `sidebar_width` setting in `_config.yml` is the sidebar's fraction of the width.

Paragraphs, headings, lists, code blocks, bold, italics and links are Markdown, as are to-dos (`- [ ] text`) and dividers (`---`). Callouts, toggles, columns and indented blocks are Liquid tags (in `_plugins/notion_tags.rb`) that contain Markdown:

```liquid
{% callout gray /assets/images/Icons_Grey3.png %}
The callout's **text**.

Other blocks in the callout.
{% endcallout %}

{% toggle **Step 1:** The toggle's summary %}
The toggle's content.
{% endtoggle %}

{% columns %}
{% column 0.5 %}
The first column's content.
{% endcolumn %}
{% column 0.5 html %}
<div class="notion-text">The second column's content, as HTML.</div>
{% endcolumn %}
{% endcolumns %}

{% indent **A paragraph** %}
Blocks indented under the paragraph, which can be empty.
{% endindent %}
```

A callout's color is a Notion color (`gray`, `green`, `red`, `yellow`, `blue`) or `default`, and its icon is an image's path or an emoji. If a callout's text is empty, its other blocks follow a blank line. A column's width is a fraction of the column list's width, and `html` means that its content is HTML, not Markdown.

Links to pages (with the page's icon and title), images and PDFs are also tags:

```liquid
{% page /plan/prioritize %}
{% page /monitoring-evaluation/sample-me-framework bg-green %}
{% image /assets/images/Untitled.jpg 672 420 align-start normal %}
{% pdf /assets/super/.../file.pdf %}
```

A page link's optional `bg-<color>` sets its background, and `html` (used in HTML, like the sidebars) omits the wrapper that makes it a Markdown block. An image's arguments are its source and its width and height in Notion, then `align-start` to align it left, and `normal` to not make it as wide as the page.

Tables are `{% table %}` tags, whose arguments are the columns' widths in pixels (or `MIN-MAX`) and Notion's `col-header` and `row-header` options. Each line is a row of cells, as in a Markdown table (the line of dashes is optional). A row or cell that starts with `{color}` has that background color, and `<br>` is a line break in a cell:

```liquid
{% table 166.24 177.23 col-header %}
| {default} **Goals** | {default} **Outcomes** |
|---|---|
{green} | Reducing carbon emissions | Line one<br>Line two |
{% endtable %}
```

Databases' gallery views are `{% gallery %}` tags (`medium` or `large`), containing a YAML list of cards, and inline databases are `{% database %}` tags, whose argument is the database's title in Markdown:

```liquid
{% database Click through to learn more %}
{% gallery medium %}
- title: Prioritize
  link: /plan/prioritize
  icon: /assets/images/icons_D_Green2.png
- title: Promoting circularity through furniture procurement in Wales
  link: /promoting-circularity-through-furniture-procurement-in-wales
  cover: /assets/images/Europe_-_Wales.png
  cover_position: 55.89
  cover_only: true
{% endgallery %}
{% enddatabase %}
```

A card without a `link` isn't clickable, and a card without an `icon` has Notion's page icon. `cover_position` defaults to 50, and `cover_only` hides the title under the cover.

Databases' table views are `{% database_table %}` tags, containing YAML with the columns (the first is the items' titles) and the items' paths. Each row's cells are its item's title and `properties` front matter, so an item is edited on its own page. `no-click` makes the rows not links:

```liquid
{% database_table %}
columns:
  - name: Name
    type: title
    width: 278
  - name: Sectors
    type: multi_select
    width: 202
items:
  - /tco-certified
  - /the-blue-angel-eco-label
{% enddatabase_table %}
```

On the Spanish and French sites, the `notion.hide_properties` setting hides the properties on the items' own pages, as on Super.so.

The few remaining blocks (lists with callouts in them) are HTML. `_plugins/notion_markdown.rb` adds Notion's classes to the elements that Markdown generates, so that Super.so's stylesheets apply. In Notion's text, a newline is a line break, so a paragraph can contain newlines and `<br>` (for an empty line), but not a blank line. The spacing between blocks is set in `assets/css/site.css`.

## How the content was produced

The pages are the server-rendered HTML of the live sites, not the Notion export, because the export loses toggles, columns, gallery views, icons and covers.

1. `python3 scripts/crawl.py` crawls each site's sitemap (and any linked page not in it) into `.crawl/`, recording each URL's status and Notion page ID in `.crawl/results.json`.
1. `python3 scripts/download_assets.py` downloads the images and files the pages reference into `assets/`.
1. `python3 scripts/import_pages.py` writes each page's article to `<lang>/<path>.md`, with its metadata, header, properties and sidebar as front matter, and writes each site's `_redirects` and `assets/css/theme-<lang>.css`. The redirects are for URLs that Super.so redirected (Notion page IDs and other capitalizations), and for URLs of pages that Super.so lists but no longer renders, if a live page has the same final path segment. The latter are read from `.crawl/super-so-pages.csv`, exported from the Super.so dashboard. Pages that duplicate other pages also redirect to them (see below), as do the broken links in `link-fixes.csv` that have a target.

Some pages that Super.so published duplicate others (listed in `.crawl/duplicates.json`), and redirect to them:

- A copy has the same title and content as other pages. The page with the most incoming links is kept.
- A placeholder is a database item that Super.so published for a gallery card: empty, or with the same content as pages with other titles. It redirects to its `super:Link` property's page, else to the only other page with its title (ignoring case and spacing). Items in table views are kept, since their properties are the views' cells.

`link-fixes.csv` maps broken links' paths to their targets: a path on the same site, or a URL. `uv run scripts/propose_link_fixes.py` (after building the sites) adds each broken link, with a proposed target if the links' text is the title of exactly one non-empty page on the same site. Review the proposals, fill in or clear the targets, and rerun `import_pages.py`. Rows keep their targets when the script is rerun. `uv run scripts/check_links.py` lists the links that are still broken.

`import_pages.py` deletes and rewrites `en/`, `es/` and `fr/`. It converts HTML to Markdown with `scripts/markdown.py`, which keeps HTML wherever the Markdown wouldn't render the same HTML, as rendered by `scripts/render_markdown.rb`, and writes a report to `.crawl/markdown-report.json`.

To check that a change doesn't change how pages look, build the sites and compare screenshots before and after:

```bash
uv run scripts/screenshots.py take before
# make the change and build the sites
uv run scripts/screenshots.py take after
uv run scripts/screenshots.py compare before after
```

The stylesheets in `assets/css/` (except `fonts.css`, `site.css` and `theme-*.css`) are Super.so's own. `assets/js/site.js` replaces the Super.so behavior that the pages need: toggles and code block copy buttons. `sitemap.xml`, `robots.txt` and `404.html` replace the ones Super.so generated.
