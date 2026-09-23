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

Liquid::Template.register_tag("properties", NotionTags::Properties)
Liquid::Template.register_tag("callout", NotionTags::Callout)
Liquid::Template.register_tag("toggle", NotionTags::Toggle)
Liquid::Template.register_tag("columns", NotionTags::Columns)
Liquid::Template.register_tag("column", NotionTags::Column)
