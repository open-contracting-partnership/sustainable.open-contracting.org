# Liquid tags for Notion's callouts, toggles and columns, which render Notion's markup around Markdown content.
module NotionTags
  ICON_STYLE = "object-fit:contain;object-position:center".freeze

  # Convert Markdown to HTML with the site's converter.
  def self.markdown(context, text)
    context.registers[:site].find_converter_instance(Jekyll::Converters::Markdown).convert(text.strip)
  end

  # Convert Markdown text to the HTML of a paragraph's content.
  def self.inline(context, text)
    return "" if text.strip.empty?

    markdown(context, text).strip.sub(%r{\A<p[^>]*>(.*)</p>\z}m, '\1')
  end

  # {% callout COLOR ICON %}TEXT\n\nBLOCKS{% endcallout %}, where COLOR is a Notion color or "default".
  class Callout < Liquid::Block
    def initialize(tag_name, markup, options)
      super
      @color, @icon = markup.split
    end

    def render(context)
      text, blocks = super.strip.split(/\n\n/, 2)
      classes = @color == "default" ? "border" : "bg-#{@color}-light border"
      icon = %(<img alt="icon" loading="lazy" width="20" height="20" class="notion-icon" style="#{ICON_STYLE}" src="#{@icon}"/>)
      %(<div class="notion-callout #{classes}"><div class="notion-callout__icon">#{icon}</div>) +
        %(<div class="notion-callout__content"><span class="notion-semantic-string">#{NotionTags.inline(context, text.to_s)}</span>) +
        %(#{NotionTags.markdown(context, blocks.to_s)}</div></div>)
    end
  end

  # {% toggle SUMMARY %}BLOCKS{% endtoggle %}
  class Toggle < Liquid::Block
    def initialize(tag_name, markup, options)
      super
      @summary = markup.strip
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
  class Properties < Liquid::Tag
    def render(context)
      properties = context["page"]["properties"]
      return "" unless properties

      config = context.registers[:site].config["notion"] || {}
      html = properties.map do |name, value|
        label = %(<div class="notion-page__property-name-wrapper"><div class="notion-page__property-name">) +
                %(<span>#{h(name)}</span></div></div>)
        %(<div class="notion-page__property">#{label}#{value(name, value, config)}</div>)
      end
      %(<div class="notion-page__properties">#{html.join}<div class="notion-divider"></div></div>)
    end

    private

    def value(name, value, config)
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

    def h(text)
      CGI.escapeHTML(text.to_s)
    end
  end
end

module NotionTags
  # {% table WIDTH... [col-header] [row-header] %}ROWS{% endtable %}, where each WIDTH is a column's width in pixels.
  #
  # Each row is a line of cells separated by "|", as in a Markdown table, and a line of only "|", "-" and ":" is
  # ignored. A row or a cell can start with {COLOR} to set its background color. Cells contain Markdown text.
  class Table < Liquid::Block
    COLOR = /\A\{(\w+)\}\s*/

    def initialize(tag_name, markup, options)
      super
      words = markup.split
      @widths = words.grep(/\A[\d.]+\z/)
      @classes = (["notion-table"] + (words - @widths)).join(" ")
    end

    def render(context)
      rows = super.strip.lines.map(&:strip).reject { |line| line.empty? || line.match?(/\A[|:\s-]+\z/) }
      html = rows.map do |line|
        color = line[COLOR, 1]
        line = line.sub(COLOR, "")
        style = color ? "background:var(--color-bg-#{color})" : "color:var(--color-text-default)"
        cells = line.delete_prefix("|").delete_suffix("|").split(/(?<!\\)\|/, -1)
        %(<tr style="#{style}">#{cells.each_with_index.map { |cell, i| cell(context, cell.strip, @widths[i]) }.join}</tr>)
      end
      %(<div class="notion-table__wrapper"><table class="#{@classes}"><tbody>#{html.join}</tbody></table></div>)
    end

    private

    def cell(context, text, width)
      color = text[COLOR, 1]
      text = text.sub(COLOR, "")
      style = "min-width:#{width}px;max-width:#{width}px"
      style += ";background:var(--color-#{color == "default" ? "color" : "bg"}-#{color})" if color
      content = if text.empty?
                  %(<div class="notion-table__empty-cell"></div>)
                else
                  %(<div class="notion-table__cell"><span class="notion-semantic-string">#{NotionTags.inline(context, text)}</span></div>)
                end
      %(<td style="#{style}">#{content}</td>)
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
      title = %(<span class="notion-semantic-string">#{NotionTags.inline(context, @title)}</span>)
      %(<div class="notion-collection inline"><div class="notion-collection__header-wrapper">) +
        %(<h3 class="notion-collection__header">#{title}</h3></div>#{super.strip}</div>)
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

Liquid::Template.register_tag("database", NotionTags::Database)
Liquid::Template.register_tag("gallery", NotionTags::Gallery)
Liquid::Template.register_tag("table", NotionTags::Table)
Liquid::Template.register_tag("properties", NotionTags::Properties)
Liquid::Template.register_tag("callout", NotionTags::Callout)
Liquid::Template.register_tag("toggle", NotionTags::Toggle)
Liquid::Template.register_tag("columns", NotionTags::Columns)
Liquid::Template.register_tag("column", NotionTags::Column)
