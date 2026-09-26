# Add Notion's classes to the elements that Markdown generates, so that Super.so's stylesheets apply to them.
module NotionMarkdown
  CLASSES = {
    p: "notion-text notion-text__content notion-semantic-string",
    header: "notion-heading notion-semantic-string",
    ul: "notion-bulleted-list",
    ol: "notion-numbered-list",
    li: "notion-list-item notion-semantic-string",
    a: "notion-link link",
  }.freeze

  COPY_ICON = '<svg class="notion-icon notion-icon__copy" viewBox="0 0 14 16"><path d="M2.404 15.322h5.701c1.26 0 ' \
              "1.887-.662 1.887-1.927V12.38h1.154c1.254 0 1.91-.662 1.91-1.928V5.555c0-.774-.158-1.266-.626-1.74L9.512.837" \
              "C9.066.387 8.545.21 7.865.21H5.463c-1.254 0-1.91.662-1.91 1.928v1.084H2.404c-1.254 0-1.91.668-1.91 1.933v8.239" \
              "c0 1.265.656 1.927 1.91 1.927zm7.588-6.62c0-.792-.1-1.161-.592-1.665L6.225 3.814c-.452-.462-.844-.58-1.5-.591" \
              "V2.215c0-.533.28-.832.843-.832h2.38v2.883c0 .726.386 1.113 1.107 1.113h2.83v4.998c0 .539-.276.832-.844.832" \
              "H9.992V8.701zm-.79-4.29c-.206 0-.288-.088-.288-.287V1.594l2.771 2.818H9.201zM2.503 14.15c-.563 0-.844-.293" \
              "-.844-.832V5.232c0-.539.281-.837.85-.837h1.91v3.187c0 .85.416 1.26 1.26 1.26h3.14v4.476c0 .54-.28.832-.843.832" \
              'H2.504zM5.79 7.816c-.24 0-.346-.105-.346-.345V4.547l3.223 3.27H5.791z"></path></svg>'.freeze

  # Lists and list items are converted below.
  CLASSES.slice(:p, :header, :a).each do |type, classes|
    define_method(:"convert_#{type}") do |el, indent|
      el.attr["class"] ||= classes
      super(el, indent)
    end
  end

  CHECKBOX = '<div class="notion-checkbox"><svg viewBox="0 0 16 16"><path d="M1.5,1.5 L1.5,14.5 L14.5,14.5 L14.5,1.5 ' \
             'L1.5,1.5 Z M0,0 L16,0 L16,16 L0,16 L0,0 Z"></path></svg></div>'.freeze

  # Render a task list ("- [ ] ...") whose items are all unchecked as Notion's to-dos.
  def convert_ul(el, indent)
    return el.children.map { |li| convert_todo(li, indent) }.join if el.children.all? { |li| todo?(li) }

    el.attr["class"] ||= CLASSES[:ul]
    super
  end

  # Number nested lists 1, a, i, as Notion does.
  def convert_ol(el, indent)
    @ol_depth = (@ol_depth || 0) + 1
    el.attr["class"] ||= CLASSES[:ol]
    el.attr["type"] ||= %w[1 a i][(@ol_depth - 1) % 3]
    super
  ensure
    @ol_depth -= 1
  end

  # Render a list item's text without a paragraph, followed by its other blocks (paragraphs and nested lists).
  def convert_li(el, indent)
    first, *rest = el.children.reject { |child| child.type == :blank }
    el.attr["class"] ||= CLASSES[:li]
    return super unless first&.type == :p

    # A list item's white-space is pre-wrap, so that newlines are line breaks, so no whitespace separates its blocks.
    text = rest.empty? ? inner(first, indent) : inner(first, indent).sub(/\s+\z/, "")
    %(#{" " * indent}<li#{html_attributes(el.attr)}>#{text}#{rest.map { |child| convert(child, indent).strip }.join}</li>\n)
  end

  # The GFM parser replaces "[ ]" with a checkbox.
  def todo?(li)
    paragraph = li.children.first
    checkbox = paragraph&.children&.first
    paragraph&.type == :p && checkbox&.type == :html_element && checkbox.value == "input" && !checkbox.attr.key?("checked")
  end

  # Render a to-do's other blocks (like a nested list) as its children.
  def convert_todo(li, indent)
    paragraph, *rest = li.children.reject { |child| child.type == :blank }
    paragraph.children.shift
    text = paragraph.children.first
    text.value = text.value.delete_prefix(" ") if text&.type == :text
    children = rest.empty? ? "" : %(<div class="notion-to-do__children">#{rest.map { |child| convert(child, indent) }.join}</div>)
    %(<div class="notion-to-do"><div class="notion-to-do__content"><div class="notion-to-do__icon">#{CHECKBOX}</div>) +
      %(<div class="notion-to-do__title"><span class="notion-semantic-string">#{inner(paragraph, indent).chomp}</span></div></div>#{children}</div>\n)
  end

  # Render a thematic break as a Notion divider.
  def convert_hr(_el, indent)
    %(#{" " * indent}<div class="notion-divider"></div>\n)
  end

  # Render a fenced code block as a Notion code block, without syntax highlighting. A mark option after its language,
  # like ```json?mark=3-5,8, marks those lines.
  def convert_codeblock(el, _indent)
    language, query = (el.options[:lang] || el.attr["class"].to_s[/language-(\S+)/, 1]).to_s.split("?", 2)
    marked = query.to_s[/\bmark=([\d,-]+)/, 1].to_s.split(",").flat_map do |part|
      first, last = part.split("-").map(&:to_i)
      (first..(last || first)).to_a
    end
    lines = escape_html(el.value.chomp).split("\n", -1).each_with_index.map do |line, i|
      marked.include?(i + 1) ? "<mark>#{line}</mark>" : line
    end
    code = %(<code class="language-#{language}">#{lines.join("\n")}</code>)
    %(<div class="notion-code no-wrap"><button class="notion-code__copy-button">#{COPY_ICON}Copy</button>) +
      %(<pre class="language-#{language}" tabindex="0">#{code}</pre><figcaption class="notion-caption notion-semantic-string"></figcaption></div>\n)
  end
end

Kramdown::Converter::Html.prepend(NotionMarkdown)
