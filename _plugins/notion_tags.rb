# Liquid tags for Notion's callouts, toggles and columns, which render Notion's markup around Markdown content.
module NotionTags
  ICON_STYLE = "object-fit:contain;object-position:center".freeze
  EMOJI_STYLE = "width:20px;height:20px;font-size:20px;fill:var(--color-text-default-light)".freeze

  # Convert Markdown to HTML with the site's converter.
  def self.markdown(context, text)
    context.registers[:site].find_converter_instance(Jekyll::Converters::Markdown).convert(text.strip)
  end

  # Convert Markdown text to the HTML of a paragraph's content.
  def self.inline(context, text)
    return "" if text.strip.empty?

    markdown(context, text).strip.sub(%r{\A<p[^>]*>(.*)</p>\z}m, '\1')
  end

  # {% callout COLOR ICON [label: LABEL] %}TEXT\n\nBLOCKS{% endcallout %}, where COLOR is a Notion color or "default",
  # ICON is an image's path or an emoji, and LABEL is Markdown, shown before TEXT. If TEXT is empty, BLOCKS follow a
  # blank line.
  class Callout < Liquid::Block
    def initialize(tag_name, markup, options)
      super
      markup, @label = markup.split(/\blabel:\s*/, 2)
      @color, @icon = markup.split
    end

    # Liquid discards the output of a block whose body is blank.
    def blank?
      false
    end

    def render(context)
      body = super.sub(/\A\n/, "")
      text, blocks = body.start_with?("\n") ? ["", body] : body.split(/\n\n/, 2)
      classes = @color == "default" ? "border" : "bg-#{@color}-light border"
      icon = if @icon.start_with?("/")
               %(<img alt="icon" loading="lazy" width="20" height="20" class="notion-icon" style="#{ICON_STYLE}" src="#{@icon}"/>)
             else # an emoji
               %(<span class="notion-icon text" style="#{EMOJI_STYLE}">#{@icon}</span>)
             end
      label = %(<p class="notion-callout__label">#{NotionTags.inline(context, @label.strip)}</p>) if @label
      unless text.to_s.strip.empty?
        text = %(<span class="notion-semantic-string">#{NotionTags.inline(context, text)}</span>)
      end
      %(<div class="notion-callout #{classes}"><div class="notion-callout__icon">#{icon}</div>) +
        %(<div class="notion-callout__content">#{label}#{text}) +
        %(#{blocks.to_s.strip.empty? ? "" : NotionTags.markdown(context, blocks)}</div></div>)
    end
  end

  # {% toggle SUMMARY %}BLOCKS{% endtoggle %}
  class Toggle < Liquid::Block
    def initialize(tag_name, markup, options)
      super
      @summary = markup.strip
    end

    # Liquid discards the output of a block whose body is blank.
    def blank?
      false
    end

    def render(context)
      trigger = %(<div class="notion-toggle__trigger"><div class="notion-toggle__trigger_icon"><span>‣</span></div></div>)
      %(<div class="notion-toggle closed"><div class="notion-toggle__summary">#{trigger}) +
        %(<span class="notion-semantic-string">#{NotionTags.inline(context, @summary)}</span></div>) +
        %(<div class="notion-toggle__content" style="display:none">#{NotionTags.markdown(context, super)}</div></div>)
    end
  end

  # {% columns %}{% column WIDTH %}BLOCKS{% endcolumn %}...{% endcolumns %}, where WIDTH is a fraction of the width.
  class Columns < Liquid::Block
    def render(context)
      columns = nodelist.grep(Column)
      html = columns.each_with_index.map { |column, index| column.render_column(context, index, columns.size) }
      %(<div class="notion-column-list">#{html.join}</div>)
    end
  end

  # {% column WIDTH %} contains Markdown, and {% column WIDTH html %} contains HTML.
  class Column < Liquid::Block
    def initialize(tag_name, markup, options)
      super
      @width, @format = markup.split
    end

    def render_column(context, index, count)
      style = "width:calc((100% - var(--column-spacing) * #{count - 1}) * #{@width})"
      style += ";margin-inline-start:var(--column-spacing)" if index.positive?
      content = render(context)
      content = NotionTags.markdown(context, content) unless @format == "html"
      %(<div class="notion-column" style="#{style}">#{content}</div>)
    end
  end
end

module NotionTags
  # {% properties %} renders a database item's properties from its front matter. Pills are a mapping of values to
  # colors, attachments and URLs are lists of mappings of text to URLs, numbers are numbers, and dates and text are
  # strings. The notion.date_properties and notion.url_properties settings name the dates and URLs.
  # The notion.hide_properties setting hides them.
  class Properties < Liquid::Tag
    def render(context)
      properties = context["page"]["properties"]
      config = context.registers[:site].config["notion"] || {}
      return "" if !properties || config["hide_properties"]

      html = properties.map do |name, value|
        label = %(<div class="notion-page__property-name-wrapper"><div class="notion-page__property-name">) +
                %(<span>#{h(name)}</span></div></div>)
        %(<div class="notion-page__property">#{label}#{Properties.value(name, value, config)}</div>)
      end
      %(<div class="notion-page__properties">#{html.join}<div class="notion-divider"></div></div>)
    end

    def h(text)
      Properties.h(text)
    end

    def self.value(name, value, config)
      case value
      when nil
        ""
      when Hash
        pills = value.each_with_index.map do |(text, color), index|
          %(<span class="notion-pill pill-#{color}#{index.zero? ? " first" : ""}">#{h(text)}</span>)
        end
        %(<div class="notion-property notion-property__select wrap">#{pills.join}</div>)
      when Array
        links = value.map(&:first)
        if config.fetch("url_properties", []).include?(name)
          html = links.map { |text, href| %(<a class="notion-link link" href="#{h(href)}">#{h(text)}</a>) }
          %(<div class="notion-property notion-property__url notion-semantic-string">#{html.join}</div>)
        else
          html = links.map do |text, href|
            target = href.start_with?("http") ? ' target="_blank" rel="noopener noreferrer"' : ""
            %(<span class="notion-pill pill-default"><span class="notion-semantic-string">) +
              %(<a href="#{h(href)}" class="notion-link link"#{target}>#{h(text)}</a></span></span>)
          end
          %(<div class="notion-property notion-property__file">#{html.join}</div>)
        end
      when Numeric
        %(<div class="notion-property notion-property__number notion-semantic-string">#{value}</div>)
      else
        if config.fetch("date_properties", []).include?(name)
          %(<div class="notion-property notion-property__date notion-semantic-string">#{h(value)}</div>)
        else
          %(<p class="notion-property notion-property__text notion-semantic-string">#{h(value)}</p>)
        end
      end
    end

    def self.h(text)
      CGI.escapeHTML(text.to_s)
    end
  end

  # Return each page's front matter, by permalink.
  def self.pages(context)
    context.registers[:notion_pages] ||= context.registers[:site].pages.to_h { |page| [page.data["permalink"], page.data] }
  end

  # {% database_table [no-click] %}YAML{% enddatabase_table %} renders a database's table view, where YAML has
  # "columns" (a list of mappings with "name", "type" and optional "width" in pixels, in which the first column is
  # the title) and "items" (a list of the items' paths). Cells are the items' titles and properties.
  # Its caption, for screen readers, is the title of the database block that contains it, or else of the page.
  class DatabaseTable < Liquid::Block
    def initialize(tag_name, markup, options)
      super
      @click = !markup.split.include?("no-click")
    end

    def render(context)
      data = YAML.safe_load(super)
      columns = data["columns"]
      pages = NotionTags.pages(context)
      config = context.registers[:site].config["notion"] || {}
      head = columns.map do |column|
        style = column["width"] ? %( style="width:#{column["width"]}px") : ""
        %(<th class="notion-collection-table__head-cell #{column["type"]}"#{style}>) +
          %(<div class="notion-collection-table__head-cell-content">#{h(column["name"])}</div></th>)
      end
      rows = data["items"].map do |path|
        page = pages.fetch(path)
        cells = columns.each_with_index.map do |column, index|
          if index.zero?
            title = %(<div class="notion-property notion-property__title notion-semantic-string">#{h(page["title"])}</div>)
            if @click
              %(<td class="notion-collection-table__cell title"><div><a href="#{h(path)}" class="notion-link">#{title}</a></div></td>)
            else
              %(<td class="notion-collection-table__cell title no-click"><div>#{title}</div></td>)
            end
          else
            value = (page["properties"] || {})[column["name"]]
            %(<td class="notion-collection-table__cell #{column["type"]}">#{Properties.value(column["name"], value, config)}</td>)
          end
        end
        "<tr>#{cells.join}</tr>"
      end
      caption = context.registers[:database_title] || h(context["page"]["title"])
      %(<div class="notion-collection-table__wrapper" tabindex="0"><table class="notion-collection-table">) +
        %(<caption>#{caption}</caption>) +
        %(<thead class="notion-collection-table__head"><tr>#{head.join}</tr></thead>) +
        %(<tbody class="notion-collection-table__body">#{rows.join}</tbody></table></div>)
    end

    private

    def h(text)
      CGI.escapeHTML(text.to_s)
    end
  end
end

module NotionTags
  # {% table WIDTH... [col-header] [row-header] [caption: CAPTION] %}ROWS{% endtable %}, where each WIDTH is a column's
  # width in pixels, or its minimum and maximum widths, as MIN-MAX, and CAPTION is Markdown. The widths set the table's
  # width, and the browser sizes the columns by their content.
  #
  # Each row is a line of cells separated by "|", as in a Markdown table, and a line of only "|", "-" and ":" is
  # ignored. A row or a cell can start with {COLOR} to set its background color. Cells contain Markdown text, in which
  # "\n" is a line break, and a cell whose lines all start with "- " is a bulleted list.
  class Table < Liquid::Block
    COLOR = /\A\{(\w+)\}\s*/
    LINE_BREAK = "\\n"
    LIST_ITEM = "- "
    # The width of the text column of a page that isn't full width (Notion's 900px, less its 96px margins).
    TEXT_WIDTH = 708

    def initialize(tag_name, markup, options)
      super
      markup, @caption = markup.split(/\bcaption:\s*/, 2)
      words = markup.split
      @widths = words.grep(/\A[\d.]+(?:-[\d.]+)?\z/)
      @classes = (["notion-table"] + (words - @widths)).join(" ")
      @col_header = words.include?("col-header")
      @row_header = words.include?("row-header")
    end

    def render(context)
      rows = super.strip.lines.map(&:strip).reject { |line| line.empty? || line.match?(/\A[|:\s-]+\z/) }
      html = rows.each_with_index.map do |line, row|
        color = line[COLOR, 1]
        line = line.sub(COLOR, "")
        style = color ? "background:var(--color-bg-#{color})" : "color:var(--color-text-default)"
        cells = line.delete_prefix("|").delete_suffix("|").split(/(?<!\\)\|/, -1)
        tds = cells.each_with_index.map do |cell, i|
          scope = "col" if @col_header && row.zero?
          scope ||= "row" if @row_header && i.zero?
          cell(context, cell.strip, scope)
        end
        %(<tr style="#{style}">#{tds.join}</tr>)
      end
      caption = @caption ? NotionTags.inline(context, @caption.strip) : nil
      caption &&= %(<caption class="notion-table__caption">#{caption}</caption>)
      label = context.registers[:site].config["table_scroll_label"]
      # The browser sizes the columns by their content, within the table's width.
      table = %(<table class="#{@classes}" style="width:100%;max-width:#{width}px">#{caption}<tbody>#{html.join}</tbody></table>)
      %(<div class="notion-table__wrapper#{" wide" if width > TEXT_WIDTH}" tabindex="0" ) +
        %(data-scroll-label="#{CGI.escapeHTML(label.to_s)}" style="--table-width:#{width}px">#{table}</div>)
    end

    private

    # The table's width, from its columns' maximum widths.
    def width
      @widths.sum { |width| width.split("-").last.to_f }.round
    end

    # A cell is a header (th), with its scope, in the first row of a table with col-header, or the first column of a
    # table with row-header.
    def cell(context, text, scope)
      color = text[COLOR, 1]
      text = text.sub(COLOR, "")
      style = %( style="background:var(--color-#{color == "default" ? "color" : "bg"}-#{color})") if color
      lines = text.split(LINE_BREAK).map(&:strip).reject(&:empty?)
      content = if text.empty?
                  %(<div class="notion-table__empty-cell"></div>)
                elsif lines.all? { |line| line.start_with?(LIST_ITEM) }
                  items = lines.map do |line|
                    %(<li class="notion-list-item notion-semantic-string">) +
                      %(#{NotionTags.inline(context, line.delete_prefix(LIST_ITEM))}</li>)
                  end
                  %(<div class="notion-table__cell"><ul class="notion-bulleted-list">#{items.join}</ul></div>)
                else
                  %(<div class="notion-table__cell"><span class="notion-semantic-string">#{NotionTags.inline(context, text.gsub(LINE_BREAK, "<br>"))}</span></div>)
                end
      scope ? %(<th scope="#{scope}"#{style}>#{content}</th>) : %(<td#{style}>#{content}</td>)
    end
  end
end

module NotionTags
  PAGE_ICON = File.read(File.join(__dir__, "notion_page_icon.svg")).freeze

  # {% database TITLE %}VIEWS{% enddatabase %} renders an inline database with a heading, where TITLE is Markdown.
  class Database < Liquid::Block
    def initialize(tag_name, markup, options)
      super
      @title = markup.strip
    end

    def render(context)
      title = NotionTags.inline(context, @title)
      context.registers[:database_title] = title
      views = super.strip
      context.registers.delete(:database_title)
      %(<div class="notion-collection inline"><div class="notion-collection__header-wrapper">) +
        %(<h3 class="notion-collection__header"><span class="notion-semantic-string">#{title}</span></h3></div>) +
        %(#{views}</div>)
    end
  end

  # {% gallery SIZE %}CARDS{% endgallery %}, where SIZE is "medium" or "large", and CARDS is a YAML list of cards with
  # keys: title, link (optional), icon (optional), cover (optional), cover_position (default 50) and cover_only.
  class Gallery < Liquid::Block
    COVER_WIDTHS = { "medium" => 780, "large" => 960 }.freeze

    def initialize(tag_name, markup, options)
      super
      @size = markup.strip
    end

    def render(context)
      cards = YAML.safe_load(super) || []
      %(<div class="notion-collection-gallery #{@size}">#{cards.map { |card| card(card) }.join}</div>)
    end

    private

    def card(card)
      title = h(card["title"])
      html = +""
      html << %(<a href="#{h(card["link"])}" class="notion-link notion-collection-card__anchor">#{title}</a>) if card["link"]
      if card["cover"]
        classes = "notion-collection-card__cover #{@size}#{card["cover_only"] ? " only-cover" : ""}"
        style = "object-fit:cover;object-position:center #{card.fetch("cover_position", 50)}%"
        html << %(<img alt="#{title}" loading="lazy" width="#{COVER_WIDTHS[@size]}" height="200" class="#{classes}") +
                %( style="#{style}" src="#{h(card["cover"])}"/>)
      end
      unless card["cover_only"]
        icon = if card["icon"]
                 %(<img alt="" loading="lazy" width="16" height="16" class="notion-icon" style="#{ICON_STYLE}" src="#{h(card["icon"])}"/>)
               else
                 PAGE_ICON
               end
        html << %(<div class="notion-collection-card__content notion-collection-card__property-list">) +
                %(<div class="notion-property notion-property__title notion-collection-card__property title notion-semantic-string">) +
                %(<div class="notion-property__title__icon-wrapper">#{icon}</div>#{title}</div></div>)
      end
      %(<div class="notion-collection-card gallery#{card["link"] ? "" : " no-click"}">#{html}</div>)
    end

    def h(text)
      CGI.escapeHTML(text.to_s)
    end
  end
end

module NotionTags
  # {% page PATH [bg-COLOR] [html] %} renders a link to a page, with its icon and title, and optionally a background
  # color. Without "html", it is wrapped for use as a block in Markdown.
  class Page < Liquid::Tag
    STYLE = "position:absolute;height:100%;width:100%;left:0;top:0;right:0;bottom:0;object-fit:contain;object-position:center;".freeze

    def initialize(tag_name, markup, options)
      super
      @path, *options = markup.split
      @color = options.grep(/\Abg-\w+\z/).first
      @html = options.include?("html")
    end

    def render(context)
      page = NotionTags.pages(context).fetch(@path)
      title = CGI.escapeHTML(page["title"].to_s)
      icon = if page["icon"]
               %(<img alt="" loading="lazy" class="notion-icon" style="#{STYLE}" src="#{CGI.escapeHTML(page["icon"])}"/>)
             else
               NotionTags::PAGE_ICON.gsub("16px", "20px")
             end
      classes = ["notion-link", "notion-page", @color].compact.join(" ")
      html = %(<a href="#{CGI.escapeHTML(@path)}" class="#{classes}"><span class="notion-page__icon">#{icon}</span>) +
             %(<span class="notion-page__title notion-semantic-string">#{title}</span></a>)
      @html ? html : "{::nomarkdown}\n#{html}\n{:/nomarkdown}"
    end
  end
end

module NotionTags
  # {% image SRC WIDTH HEIGHT [align-start] [normal] %} renders an image block, as wide as the page unless "normal".
  class Image < Liquid::Tag
    def initialize(tag_name, markup, options)
      super
      @src, @width, @height, *@options = markup.split
    end

    def render(_context)
      normal = @options.include?("normal")
      classes = ["notion-image", @options.include?("align-start") ? "align-start" : nil, normal ? "normal" : "page-width"]
      style = normal ? "height:auto" : "object-fit:contain;object-position:center;height:auto"
      %(<div class="#{classes.compact.join(" ")}"><img alt="image" loading="lazy" width="#{@width}" height="#{@height}") +
        %( style="#{style}" src="#{CGI.escapeHTML(@src)}"/></div>)
    end
  end
end

module NotionTags
  # {% pdf SRC [TITLE] %} renders an embedded PDF, whose frame's title is TITLE (by default, the file's name).
  class Pdf < Liquid::Tag
    def render(_context)
      src, title = @markup.strip.split(/\s+/, 2)
      title = CGI.escapeHTML(title || File.basename(src))
      src = CGI.escapeHTML(src)
      %(<div class="notion-pdf"><div class="notion-pdf__content"><iframe width="708" height="320" src="#{src}" ) +
        %(title="#{title}"></iframe></div></div>)
    end
  end

  # {% indent [TEXT] %}BLOCKS{% endindent %} renders a paragraph (TEXT, in Markdown, which can be empty) followed by
  # indented blocks.
  class Indent < Liquid::Block
    def initialize(tag_name, markup, options)
      super
      @text = markup.strip
    end

    # Liquid discards the output of a block whose body is blank.
    def blank?
      false
    end

    def render(context)
      %(<div class="notion-text"><p class="notion-text__content notion-semantic-string">#{NotionTags.inline(context, @text)}</p>) +
        %(<div class="notion-text__children">#{NotionTags.markdown(context, super)}</div></div>)
    end
  end
end

Liquid::Template.register_tag("pdf", NotionTags::Pdf)
Liquid::Template.register_tag("indent", NotionTags::Indent)
Liquid::Template.register_tag("image", NotionTags::Image)
Liquid::Template.register_tag("page", NotionTags::Page)
Liquid::Template.register_tag("database", NotionTags::Database)
Liquid::Template.register_tag("database_table", NotionTags::DatabaseTable)
Liquid::Template.register_tag("gallery", NotionTags::Gallery)
Liquid::Template.register_tag("table", NotionTags::Table)
Liquid::Template.register_tag("properties", NotionTags::Properties)
Liquid::Template.register_tag("callout", NotionTags::Callout)
Liquid::Template.register_tag("toggle", NotionTags::Toggle)
Liquid::Template.register_tag("columns", NotionTags::Columns)
Liquid::Template.register_tag("column", NotionTags::Column)
