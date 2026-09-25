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

Each build writes to `_site/<lang>/`. Google Analytics is included only when `JEKYLL_ENV=production`.

Each site has search (the `search` setting, with its labels in `search_labels`), whose index [Pagefind](https://pagefind.app) builds from a site's build. `scripts/build.sh` builds a site, its stylesheet and its index, after installing the Node packages:

```bash
pnpm install
scripts/build.sh en  # or es, fr
```

To try search locally, serve the build, since `jekyll serve` rebuilds the site without the index. `scripts/serve.py` serves it as Cloudflare Pages does, with a page at its path without `.html`:

```bash
scripts/build.sh en && uv run scripts/serve.py _site/en  # port 8000, or pass a port after the directory
```

Pagefind indexes each page's `<main>`, except the navbar, sidebar, cover and icon, and skips pages without content or properties (placeholders for database items).

## Deploy

The `deploy.yml` workflow builds the sites with `JEKYLL_ENV=production` and, on a push to `main` whose checks pass, pushes each build to its branch. Each site is a Cloudflare Pages project, connected to this repository, which serves its branch without building it:

| Site | Production branch |
| --- | --- |
| sustainable.open-contracting.org | `publish-en` |
| sostenibilidad.open-contracting.org | `publish-es` |
| achatdurable.open-contracting.org | `publish-fr` |

Each project has no build command or output directory, and no preview deployments (its other branches are this repository's source). `_headers` sets the Content-Security-Policy and HSTS, as on the organization's other Cloudflare Pages sites. The policy allows Pagefind's WebAssembly and worker, Notion's inline styles, Google Analytics (whose snippet is `assets/js/analytics.js`, not inline), and the PDFs' frames. To try it locally, after a build: `wrangler pages dev _site/en`. The workflows set the Ruby and Node versions.

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

A callout's color is a Notion color (`gray`, `green`, `red`, `yellow`, `blue`) or `default`, and its icon is an image's path or an emoji. A column's width is a fraction of the column list's width, and `html` means that its content is HTML, not Markdown.

Links to pages (with the page's icon and title), images and PDFs are also tags:

```liquid
{% page /plan/prioritize %}
{% page /monitoring-evaluation/sample-me-framework bg-green %}
{% image /assets/images/Untitled.jpg 672 420 align-start normal %}
{% pdf /assets/files/compliance-trail-checklist.pdf Compliance trail checklist %}
```

A page link's optional `bg-<color>` sets its background, and `html` (used in HTML, like the sidebars) omits the wrapper that makes it a Markdown block. An image's arguments are its source and its width and height in Notion, then `align-start` to align it left, and `normal` to not make it as wide as the page. A PDF's optional title, after its path, names its frame for screen readers (by default, the file's name).

Tables are `{% table %}` tags, whose arguments are the columns' widths in pixels (or `MIN-MAX`) and Notion's `col-header` and `row-header` options. Each line is a row of cells, as in a Markdown table (the line of dashes is optional). A cell whose lines all start with `\-` and a space is a bulleted list. A row or cell that starts with `{color}` has that background color, and `<br>` is a line break in a cell:

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

Databases' table views are `{% database_table %}` tags, containing YAML with the columns (the first is the items' titles) and the items' paths. Each row's cells are its item's title and `properties` front matter, so an item is edited on its own page. Its caption, for screen readers, is the database's title (or the page's, outside a `{% database %}` tag). `no-click` makes the rows not links:

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

`_plugins/notion_markdown.rb` adds Notion's classes to the elements that Markdown generates, so that Super.so's stylesheets apply. In Notion's text, a newline is a line break, so a paragraph can contain newlines and `<br>` (for an empty line), but not a blank line. The spacing between blocks is set in `assets/css/site.css`.

## Editing

The content is edited by hand:

- Pages are `<lang>/<path>.md` (see [Pages](#pages)).
- Sidebars are `_includes/sidebar-<lang>.html`, whose links to pages are `{% page PATH html %}` tags.
- Redirects are `<lang>/_redirects`, one `SOURCE TARGET 301` rule per line, after the front matter. A target is a path on the same site, or a URL.

To fix a broken link, change the link in the linking page's Markdown, or (for a link from the same site) add a redirect. `uv run scripts/check_links.py` (after building the sites) lists broken links. To audit links against their text, `uv run scripts/list_links.py` lists the links between the sites' pages, with their context, and `uv run scripts/list_external_links.py --check` lists the links to other websites, with their parity across languages and their status. `scripts/translations.py` matches each page to its versions in the other languages.

### Checks

On each push, the `deploy.yml` workflow runs the pre-commit hooks, runs `scripts/check_redirects.py`, builds the sites, and runs `scripts/check_pages.py`, `scripts/check_links.py` and `scripts/check_markup.py`. Each fails if it finds a problem, as does the build on invalid front matter, a Liquid syntax error or an unknown filter. To run the checks locally, after building the sites with `scripts/build.sh`:

```bash
uvx pre-commit run --all-files
uv run scripts/check_redirects.py
uv run scripts/check_pages.py
uv run scripts/check_links.py
uv run scripts/check_markup.py
```

To lint on each commit, run `uvx pre-commit install`. The Python linter and formatter is [Ruff](https://docs.astral.sh/ruff/), configured in `pyproject.toml` as in the [OCP Software Development Handbook](https://ocp-software-handbook.readthedocs.io/en/latest/python/linting.html). `pyproject.toml` also declares the scripts' project, so that `uv run` runs them in its environment, with `screenshots.py`'s dependencies in the `screenshots` group. The Markdown linter is [pymarkdownlnt](https://github.com/jackdewinter/pymarkdown), configured in `pyproject.toml`. It reads the Liquid tags' contents as Markdown, so the YAML lists in gallery and database table tags have a blank line before them, and aren't indented. The JavaScript and CSS linter and formatter is [Biome](https://biomejs.dev), configured in `biome.jsonc`. It skips the HTML (Jekyll templates, which it can't parse), and Super.so's stylesheets (all but `fonts.css` and `site.css`).

The `lint.yml` workflow runs [standard-maintenance-scripts](https://github.com/open-contracting/standard-maintenance-scripts)' linters: files' permissions, Ruff (with its own settings, which `pyproject.toml` extends), and the JSON, CSV and README tests. The `shell.yml` workflow checks `scripts/build.sh` with checkbashisms, shellcheck and shfmt. The `js.yml` workflow runs [knip](https://knip.dev), configured in `knip.jsonc`, which reports unused files, dependencies and exports (`pnpm exec knip`). The `spellcheck.yml` workflow runs [codespell](https://github.com/codespell-project/codespell) on the repository, except the Spanish and French pages and sidebars, which it would read as misspelled English. To accept a word, add it to the workflow's `ignore` input. Dependabot (`.github/dependabot.yml`) updates the workflows' actions, and the `automerge.yml` workflow merges its non-major updates and pre-commit.ci's updates to the hooks.

The `a11y.yml` workflow checks each site's pages for accessibility issues (WCAG 2.1 AA) with [pa11y-ci](https://github.com/pa11y/pa11y-ci), on a desktop and a mobile viewport, as in the [OCP Software Development Handbook](https://ocp-software-handbook.readthedocs.io/en/latest/python/a11y.html). The errors checks fail on any issue. The warnings checks fail on any issue that isn't a known warning, which `pa11y.default.js` lists with its reason. To run a check locally, after building and serving a site:

```bash
pnpm install
pnpm exec puppeteer browsers install chrome
PA11Y_STRATEGY=ignore pnpm exec pa11y-ci -c pa11y.default.js -s http://127.0.0.1:8000/sitemap.xml -f https://sustainable.open-contracting.org -r http://127.0.0.1:8000
```

Use `pa11y.mobile.js` for the mobile viewport, and set `PA11Y_INCLUDE_WARNINGS=1 PA11Y_SUPPRESS_KNOWN_WARNINGS=1` for the warnings.

`scripts/check_redirects.py` checks that each rule in `<lang>/_redirects` is `SOURCE TARGET 301`, that its source is unique and not a page, and that its target is a page (not another redirect), and that there are fewer rules than Cloudflare Pages allows. So, to rename or delete a page, redirect its path, and change the redirects that led to it.

`scripts/check_pages.py` checks that each page's permalink is its file's path and unique, that it has a title, and that its cover and icon are files. In the built sites, it checks that the files in `/assets/` that pages refer to exist, that the sitemap's URLs are pages, and that the search index has every page with content.

`scripts/check_markup.py` checks the built pages' text for Markdown, Liquid and HTML syntax that didn't render, links whose text starts or ends with a space or punctuation (which belongs outside the link, except `?` and `!`, and except at the end of a link that is a whole block or sentence, like a reference in a list, or that ends with an abbreviation), bold or italics without words, bold or italics that only spaces separate from the next bold or italics (which can be one span), and non-breaking spaces at the end of a line or block.

### Screenshots

To check that a change doesn't change how pages look, build the sites and compare screenshots before and after:

```bash
uv run --group screenshots scripts/screenshots.py take before
# make the change and build the sites
uv run --group screenshots scripts/screenshots.py take after
uv run --group screenshots scripts/screenshots.py compare before after
```

### Stylesheets and scripts

The stylesheets in `assets/css/` (except `fonts.css`, `main.css`, `site.css` and `theme-*.css`) are Super.so's own. `main.css` imports them all, with the site's theme, so `jekyll serve` works as is. `scripts/build.sh` then bundles it with [esbuild](https://esbuild.github.io) (`build.mjs`, as in the [OCP Software Development Handbook](https://ocp-software-handbook.readthedocs.io/en/latest/javascript/index.html#build-js)), removing the rules that the built pages and scripts don't use with [PurgeCSS](https://purgecss.com), and adding vendor prefixes with Autoprefixer. With `NODE_ENV=production`, as in CI, it minifies the bundle; otherwise, it writes a sourcemap. A class that only a script adds must appear in the script's source, as the ones in `site.js` do. `assets/js/site.js` replaces the Super.so behavior that the pages need: toggles, code block copy buttons, breadcrumbs that collapse into a menu when they don't fit, and search (in Super.so's search dialog, `_includes/search.html`, whose search matched only titles). `sitemap.xml`, `robots.txt` and `404.html` replace the ones Super.so generated.

## History

The content was imported from the Super.so sites in 2026, by scripts that were removed once it was edited by hand (see `git log -- scripts/import_pages.py`). The pages were crawled as the live sites' server-rendered HTML, not the Notion export, which loses toggles, columns, gallery views, icons and covers. The import:

- converted each page to Markdown and Liquid tags, and checked that they render the same HTML as the original;
- downloaded the images and files into `assets/`;
- wrote each site's `_redirects`: from the URLs that Super.so redirected (Notion page IDs and other capitalizations), the URLs of pages that it listed but no longer rendered, pages that duplicated others (copies, and placeholders that Super.so published for gallery cards), paths without the numbers that Super.so added (like `/construction-sector-1`), and broken links, whose targets were reviewed;
- linked links to another language's page to its version in the linking page's language, where it has one.
