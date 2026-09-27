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

Each project has no build command or output directory, and no preview deployments (its other branches are this repository's source). `_headers` sets the Content-Security-Policy and HSTS, as on the organization's other Cloudflare Pages sites. The policy follows the [OCP Software Development Handbook](https://ocp-software-handbook.readthedocs.io/en/latest/http/index.html#content-security-policy-csp), and allows Pagefind's WebAssembly and worker, Notion's inline styles, and Google Analytics (whose snippet is `assets/js/analytics.js`, not inline). It forbids framing, except of the PDFs in `/assets/files/`, which pages embed. To try it locally, after a build: `wrangler pages dev _site/en`. The workflows set the Ruby and Node versions.

## Pages

Each page is `<lang>/<path>.md`, with front matter:

| Key | Description |
| --- | --- |
| `permalink` | The page's URL path, which is also the path of its file |
| `title` | The page's title |
| `hide_title` | Whether to hide the title, like the home pages', whose first heading is then the page's `<h1>` |
| `description` | The page's meta description |
| `cover` | The header's cover image, 140px tall (the home pages', 30% of the screen's height, to show the site's name): a WebP, or an SVG for flat shapes, by default the standard cover (`_config.yml`), or `false` for none, like the worked examples' steps and the tools. The social media image is a JPEG with the same name, 1,200px wide, since not all platforms accept WebP |
| `cover_position` | The cover's vertical position, as a percentage (default 50) |
| `image` | The social media image, if not the cover's, like the case studies', which show their titles: a JPEG, 1,200px wide |
| `icon` | The header's icon, also used in breadcrumbs |
| `full_width` | Whether the page is full width. A page with the sidebar is full width |
| `collection` | Whether the page is a Notion database |
| `notion_id` | The ID of the Notion page from which it was imported |
| `sidebar` | Whether the page has the sidebar on wider screens. On phones, every page has its menu. Every page has it, except the sample M&E framework, whose wide table extends past the text column of a page that isn't full width |
| `properties` | A database item's properties, in order, rendered by the `{% properties %}` tag in the layout: a mapping of pills to their colors, a list of mappings of attachments' names to their URLs, a number, or text. The `notion.date_properties` and `notion.url_properties` settings in `_config.yml` name the properties that are dates and URLs. |

A page's versions in each language are a line of `_data/translations.yml`, like `- {en: /prioritize, es: /priorice, fr: /priorits}`, which all three builds read. The layout and the sitemaps link them as alternates (`hreflang`), with the English version as the default. The navbar's language links (`_includes/languages.html`) go to the page's versions, or to the other sites' home pages. To add a page's versions, or to change a permalink, edit its line.

The layout renders the breadcrumbs (from the pages at each prefix of the path) and the header, and the sidebar (in `_includes/sidebar-<lang>.html`, a navigation list of the sections and their pages) if a page has `sidebar: true`. On phones, where the columns stack, the sidebar is a menu, opened by a button in the navbar, on every page (`_includes/sidebar-menu.html`). It's a `<details>` element, so it works without JavaScript, and it's shown open on wider screens with `::details-content`. The `sidebar_width` setting in `_config.yml` is the sidebar's width, in pixels, or a quarter of the width if that's less. Pages have narrower margins below 1280px, so that the content has room. Text is at most 708px wide, about 75 characters per line, and so are images, unless `wide`. Code blocks are as wide as the text, or as their longest line, and tables as their content, up to the content's full width, which galleries use.

Each page ends with links to the previous and next pages, in one sequence (`_plugins/sequence.rb`): the sidebar's pages, in order, each followed by the pages that its galleries and page links point to, in their order. A new page is in the sequence once a page in it links to it that way.

Paragraphs, headings, lists, code blocks, bold, italics and links are Markdown, as are to-dos (`- [ ] text`) and dividers (`---`). A heading's size is its level in Markdown, as in Notion (`#` is the largest), but `_plugins/heading_levels.rb` numbers its tag from `<h2>`, below the page's title (or from `<h1>`, with `hide_title`), in the order of the levels that the page uses, so that screen readers see no skipped levels. A heading that links target has an ID at the end of its line, like `### Option 1: Assign tags to procurements {#option-1}`, and links add it to the page's path, like `/options-for-data-use#option-1`. The options pages' headings have the same IDs in every language. An image in a paragraph of its own is an image block, like `![Alt text](/assets/images/OCDS_model.png){: .wide}`, as wide as the text, or with `{: .wide}`, as wide as the content, for diagrams and screenshots whose text would be too small. Its alt text is in the page's language, and empty for decorative illustrations. `_plugins/notion_markdown.rb` reads its width and height from the file (a PNG, JPEG or WebP), so that the browser reserves its space as it loads, and lazy loads it. Code blocks that aren't code, like worked examples and formulas, are ```` ```text ````. A code block's optional `?mark=` after its language, like ```` ```json?mark=3-5,8 ````, highlights those lines. Callouts, toggles and indented blocks are Liquid tags (in `_plugins/notion_tags.rb`) that contain Markdown:

```liquid
{% callout gray /assets/images/Icons_Grey3.svg %}
The callout's **text**.

Other blocks in the callout.
{% endcallout %}

{% callout gray /assets/images/Notion-others2.svg label: Case study %}

A labelled callout's blocks, after a blank line.
{% endcallout %}

{% toggle **Step 1:** The toggle's summary %}
The toggle's content.
{% endtoggle %}

{% indent **A paragraph** %}
Blocks indented under the paragraph, which can be empty.
{% endindent %}
```

A toggle is a `<details>` element, so it works with the keyboard and without JavaScript, styled as an accordion: rows between borders, with a chevron on a green circle. An `{% expand_toggles %}` tag, before a group of toggles, like the FAQs', adds a button that opens or closes them all, labelled by the `expand_label` and `collapse_label` settings.

A callout's color is a Notion color (`gray`, `green`, `red`, `yellow`, `blue`) or `default`, and its icon is an image's path or an emoji. An optional `label:`, last, is shown in bold before the callout's text, like "Case study" or "Resources", so it isn't written in bold.

Links to pages (with the page's icon and title), images and PDFs are also tags:

```liquid
{% page /prioritize %}
{% page /monitoring-evaluation/sample-me-framework bg-green %}
{% pdf /assets/files/compliance-trail-checklist.pdf Compliance trail checklist %}
```

A page link's optional `bg-<color>` sets its background, and `html` (used in HTML, like the sidebars) omits the wrapper that makes it a Markdown block. A PDF's optional title, after its path, names its frame for screen readers (by default, the file's name). The frame shows a whole A4 page, up to 85% of the screen's height, and a link below it downloads the file, since most phones' browsers don't show PDFs in frames. The link's text is the `pdf_label` setting, with the file's size.

Tables are `{% table %}` tags, as wide as their content, up to their column's width, with the columns sized by the browser by their content, without breaking words. Each line is a row of cells, as in a Markdown table (the line of dashes is optional). The first row is the header row, whose cells are headers (`<th>`), in bold. The tag's options are:

- `row-header`: the first column's cells are headers too.
- `colors:`: each column's background color, in order, like `colors: default orange yellow green` (`default` for none).
- `row-colors:`: each row's background color, by its first cell's text, like `row-colors: {Reducing carbon emissions: green}`.
- `wide`: on a page that isn't full width, the table extends past both sides of the text column, on wider screens.
- `caption:`, last: the table's caption, in Markdown.

A row or cell that starts with `{color}` has that background color, like a header row's. A table that scrolls has a hint above it, in each site's language (`table_scroll_label`), and fades at the edges that have more. In a cell, `\n` is a line break, and a cell whose lines all start with `-` and a space is a bulleted list:

```liquid
{% table row-colors: {Reducing carbon emissions: green} caption: Goals and outcomes %}
| Goals | Outcomes |
|---|---|
| Reducing carbon emissions | Line one\nLine two |
| Promoting SPP uptake | - Number of SPP contracts\n- Total number of contracts |
{% endtable %}
```

The table of options for data use is an `{% options_table /options-for-data-use %}` tag, which builds its rows from the options page, so that each option is edited there, once: a row for each heading with an `{#option-N}` ID, linked to it, with the cells of the table under it.

A preview of another page's table, like the monitoring and evaluation page's example from the sample framework, is a `{% table_row /monitoring-evaluation/sample-me-framework Tonnes of Co2 associated with public contracts %}` tag: the first table on that page, with its options, but only its header and the row with that cell, so that the row is edited once. The build fails if no row, or more than one, has that cell.

Databases' gallery views are `{% gallery %}` tags (`medium` or `large`), containing a YAML list of cards, and inline databases are `{% database %}` tags, whose argument is the database's title in Markdown:

```liquid
{% database Click through to learn more %}
{% gallery medium %}

- title: Prioritize
  link: /prioritize
  icon: /assets/images/icons_D_Green2.svg
- title: Promoting circularity through furniture procurement in Wales
  link: /promoting-circularity-through-furniture-procurement-in-wales
  cover: /assets/images/Europe_-_Wales.webp
  cover_position: 55.89
  cover_only: true
{% endgallery %}
{% enddatabase %}
```

A card without a `link` isn't clickable, and a card without an `icon` has Notion's page icon. `cover_position` defaults to 50, and `cover_only` hides the title under the cover.

Databases' table views, like the resource directory and the ecolabels, are `{% database_table %}` tags, containing YAML with the columns and the items. The first column is the items' titles, and a column of pills lists its values' colors. Each item is a title, an optional link, which the title links to (like the resource's attachment), and its values, by column name: a pill, a list of pills, a number or text. An item is edited in its table. The table's caption, for screen readers, is the database's title (or the page's, outside a `{% database %}` tag). The title column is 280px wide and the others 200px. The comments turn off the Markdown linter's bare URL rule, which the links would break:

```liquid
{% comment %}
<!-- pyml disable md034 -->
{% endcomment %}
{% database_table %}
columns:

- name: Name
- name: Type
  colors: {Type I: green, Type I-like: default}
- name: Sectors
  colors: {ICT: red, Furniture: yellow}
items:

- title: TCO Certified
  link: https://tcocertified.com/criteria-documents/
  Type: Type I
  Sectors: [ICT]
{% enddatabase_table %}
{% comment %}
<!-- pyml enable md034 -->
{% endcomment %}
```

On the Spanish and French sites, the `notion.hide_properties` setting hides database items' properties, like the case studies', as on Super.so.

`_plugins/notion_markdown.rb` adds Notion's classes to the elements that Markdown generates, so that Super.so's stylesheets apply. In Notion's text, a newline is a line break, so a paragraph can contain newlines and `<br>` (for an empty line), but not a blank line. The spacing between blocks is set in `assets/css/site.css`.

## Editing

The content is edited by hand:

- Pages are `<lang>/<path>.md` (see [Pages](#pages)).
- Sidebars are `_includes/sidebar-<lang>.html`, whose links to pages are `{% page PATH html %}` tags.
- Redirects are `<lang>/_redirects`, one `SOURCE TARGET 301` rule per line, after the front matter. A target is a path on the same site, or a URL.

To fix a broken link, change the link in the linking page's Markdown, or (for a link from the same site) add a redirect. `uv run scripts/check_links.py` (after building the sites) lists broken links, including links to IDs that their pages don't have. To audit links against their text, `uv run scripts/list_links.py` lists the links between the sites' pages, with their context, and `uv run scripts/list_external_links.py --check` lists the links to other websites, with their parity across languages and their status. `scripts/translations.py` matches each page to its likely versions in the other languages, for a new line in `_data/translations.yml`.

### Checks

On each push, the `deploy.yml` workflow builds the sites, and runs `scripts/check_redirects.py`, `scripts/check_pages.py`, `scripts/check_links.py`, `scripts/check_orphans.py` and `scripts/check_markup.py`. Each fails if it finds a problem, as does the build on invalid front matter, a Liquid syntax error or an unknown filter. To run the checks locally, after building the sites with `scripts/build.sh`:

```bash
uvx pre-commit run --all-files
uv run scripts/check_redirects.py
uv run scripts/check_pages.py
uv run scripts/check_links.py
uv run scripts/check_orphans.py
uv run scripts/check_markup.py
```

[pre-commit.ci](https://pre-commit.ci) runs the pre-commit hooks on each push. To lint on each commit, run `uvx pre-commit install`. The Python linter and formatter is [Ruff](https://docs.astral.sh/ruff/), configured in `pyproject.toml` as in the [OCP Software Development Handbook](https://ocp-software-handbook.readthedocs.io/en/latest/python/linting.html). `pyproject.toml` also declares the scripts' project, so that `uv run` runs them in its environment, with `screenshots.py`'s dependencies in the `screenshots` group. The Markdown linter is [pymarkdownlnt](https://github.com/jackdewinter/pymarkdown), configured in `pyproject.toml`. It reads the Liquid tags' contents as Markdown, so the YAML lists in gallery and database table tags have a blank line before them, and aren't indented. The JavaScript and CSS linter and formatter is [Biome](https://biomejs.dev), configured in `biome.jsonc`. It skips the HTML (Jekyll templates, which it can't parse), and Super.so's stylesheets (all but `fonts.css`, `main.css` and `site.css`).

The `lint.yml` workflow runs [standard-maintenance-scripts](https://github.com/open-contracting/standard-maintenance-scripts)' linters: files' permissions, Ruff (with its own settings, which `pyproject.toml` extends), and the JSON, CSV and README tests. The `shell.yml` workflow checks `scripts/build.sh` with checkbashisms, shellcheck and shfmt. The `js.yml` workflow runs [knip](https://knip.dev), configured in `knip.jsonc`, which reports unused files, dependencies and exports (`pnpm exec knip`). The `spellcheck.yml` workflow runs [codespell](https://github.com/codespell-project/codespell) on the repository, except the Spanish and French pages and sidebars, which it would read as misspelled English. To accept a word, add it to the workflow's `ignore` input. Dependabot (`.github/dependabot.yml`) updates the workflows' actions, and the `automerge.yml` workflow merges its non-major updates and pre-commit.ci's updates to the hooks.

The `a11y.yml` workflow checks each site's pages for accessibility issues (WCAG 2.1 AA) with [pa11y-ci](https://github.com/pa11y/pa11y-ci), on a desktop and a mobile viewport, as in the [OCP Software Development Handbook](https://ocp-software-handbook.readthedocs.io/en/latest/python/a11y.html). The errors checks fail on any issue. The warnings checks fail on any issue that isn't a known warning, which `pa11y.default.js` lists with its reason. To run a check locally, after building and serving a site:

```bash
pnpm install
pnpm exec puppeteer browsers install chrome
PA11Y_STRATEGY=ignore pnpm exec pa11y-ci -c pa11y.default.js -s http://127.0.0.1:8000/sitemap.xml -f https://sustainable.open-contracting.org -r http://127.0.0.1:8000
```

Use `pa11y.mobile.js` for the mobile viewport, and set `PA11Y_INCLUDE_WARNINGS=1 PA11Y_SUPPRESS_KNOWN_WARNINGS=1` for the warnings.

`scripts/check_redirects.py` checks that each rule in `<lang>/_redirects` is `SOURCE TARGET 301`, that its source is unique and not a page, and that its target is a page (not another redirect), and that there are fewer rules than Cloudflare Pages allows. So, to rename or delete a page, redirect its path, and change the redirects that led to it.

`scripts/check_orphans.py` checks that links reach every page from the home page, except the pages in its `EXCEPTIONS`, which must match pages that aren't reachable. When fixing one, remove it from the list.

`scripts/check_pages.py` checks that each page's permalink is its file's path and unique, that it has a title, that its cover and icon are files, and that each path in `_data/translations.yml` is a page, on one line. In the built sites, it checks that the files in `/assets/` that pages refer to exist, that each file in `/assets/` is used by some site's pages, stylesheets or templates, that the sitemap's URLs are pages, and that the search index has every page with content.

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

`static.css`, `notion.css`, `super.css` and `theme.css` (the sites' theme, from the English site) in `assets/css/` are Super.so's own, unchanged. `fonts.css` serves the Montserrat font from `assets/fonts/`, and `site.css` has this site's own styles. `main.css` imports them all, so `jekyll serve` works as is. `scripts/build.sh` then bundles it with [esbuild](https://esbuild.github.io) (`build.mjs`, as in the [OCP Software Development Handbook](https://ocp-software-handbook.readthedocs.io/en/latest/javascript/index.html#build-js)), removing the rules that the built pages and scripts don't use with [PurgeCSS](https://purgecss.com), and adding vendor prefixes with Autoprefixer. With `NODE_ENV=production`, as in CI, it minifies the bundle; otherwise, it writes a sourcemap. A class that only a script adds must appear in the script's source, as the ones in `site.js` do. `assets/js/site.js` replaces the Super.so behavior that the pages need: breadcrumbs that collapse into a menu when they don't fit, and search (in Super.so's search dialog, `_includes/search.html`, whose search matched only titles). It also closes the sidebar's and languages' menus on Escape or a click outside them, shows the hint and fades on tables that scroll, and makes `{% expand_toggles %}` buttons work. Its sections are those of `site.css`. `sitemap.xml`, `robots.txt` and `404.html` replace the ones Super.so generated.

## History

The content was imported from the Super.so sites in 2026, by scripts that were removed once it was edited by hand (see `git log -- scripts/import_pages.py`). The pages were crawled as the live sites' server-rendered HTML, not the Notion export, which loses toggles, columns, gallery views, icons and covers. The import:

- converted each page to Markdown and Liquid tags, and checked that they render the same HTML as the original;
- downloaded the images and files into `assets/`;
- wrote each site's `_redirects`: from the URLs that Super.so redirected (Notion page IDs and other capitalizations), the URLs of pages that it listed but no longer rendered, pages that duplicated others (copies, and placeholders that Super.so published for gallery cards), paths without the numbers that Super.so added (like `/construction-sector-1`), and broken links, whose targets were reviewed;
- linked links to another language's page to its version in the linking page's language, where it has one.
