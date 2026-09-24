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

Each site has search (the `search` setting, with its labels in `search_labels`), whose index [Pagefind](https://pagefind.app) builds from a site's build. `scripts/build.sh` builds a site and its index:

```bash
scripts/build.sh en  # or es, fr
```

To try search locally, serve the build, since `jekyll serve` rebuilds the site without the index:

```bash
scripts/build.sh en && python3 -m http.server -d _site/en
```

Pagefind indexes each page's `<main>`, except the navbar, sidebar, cover and icon, and skips pages without content or properties (placeholders for database items).

## Deploy

Each site is a Cloudflare Pages project, connected to this repository:

| Site | Build command | Output directory |
| --- | --- | --- |
| sustainable.open-contracting.org | `JEKYLL_ENV=production scripts/build.sh en` | `_site/en` |
| sostenibilidad.open-contracting.org | `JEKYLL_ENV=production scripts/build.sh es` | `_site/es` |
| achatdurable.open-contracting.org | `JEKYLL_ENV=production scripts/build.sh fr` | `_site/fr` |

`.ruby-version` and `.node-version` set the versions that the build uses, and Cloudflare runs `bundle install` before the build command.

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

The few remaining blocks (the French case study database's large galleries) are HTML. `_plugins/notion_markdown.rb` adds Notion's classes to the elements that Markdown generates, so that Super.so's stylesheets apply. In Notion's text, a newline is a line break, so a paragraph can contain newlines and `<br>` (for an empty line), but not a blank line. The spacing between blocks is set in `assets/css/site.css`.

## Editing

The content is edited by hand:

- Pages are `<lang>/<path>.md` (see [Pages](#pages)).
- Sidebars are `_includes/sidebar-<lang>.html`, whose links to pages are `{% page PATH html %}` tags.
- Redirects are `<lang>/_redirects`, one `SOURCE TARGET 301` rule per line, after the front matter. A target is a path on the same site, or a URL.

To fix a broken link, change the link in the linking page's Markdown, or (for a link from the same site) add a redirect. `uv run scripts/check_links.py` (after building the sites) lists broken links. To audit links against their text, `uv run scripts/list_links.py` lists the links between the sites' pages, with their context, and `uv run scripts/list_external_links.py --check` lists the links to other websites, with their parity across languages and their status. `scripts/translations.py` matches each page to its versions in the other languages.

To check that a change doesn't change how pages look, build the sites and compare screenshots before and after:

```bash
uv run scripts/screenshots.py take before
# make the change and build the sites
uv run scripts/screenshots.py take after
uv run scripts/screenshots.py compare before after
```

The stylesheets in `assets/css/` (except `fonts.css`, `site.css` and `theme-*.css`) are Super.so's own. `assets/js/site.js` replaces the Super.so behavior that the pages need: toggles, code block copy buttons and search (in Super.so's search dialog, `_includes/search.html`, whose search matched only titles). `sitemap.xml`, `robots.txt` and `404.html` replace the ones Super.so generated.

## History

The content was imported from the Super.so sites in 2026, by scripts that were removed once it was edited by hand (see `git log -- scripts/import_pages.py`). The pages were crawled as the live sites' server-rendered HTML, not the Notion export, which loses toggles, columns, gallery views, icons and covers. The import:

- converted each page to Markdown and Liquid tags, and checked that they render the same HTML as the original;
- downloaded the images and files into `assets/`;
- wrote each site's `_redirects`: from the URLs that Super.so redirected (Notion page IDs and other capitalizations), the URLs of pages that it listed but no longer rendered, pages that duplicated others (copies, and placeholders that Super.so published for gallery cards), paths without the numbers that Super.so added (like `/construction-sector-1`), and broken links, whose targets were reviewed;
- linked links to another language's page to its version in the linking page's language, where it has one.
