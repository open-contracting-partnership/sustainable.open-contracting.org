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

  CLASSES.each do |type, classes|
    define_method(:"convert_#{type}") do |el, indent|
      el.attr["class"] ||= classes
      el.attr["type"] ||= "1" if type == :ol
      super(el, indent)
    end
  end

  # Render a fenced code block as a Notion code block, without syntax highlighting.
  def convert_codeblock(el, _indent)
    language = el.options[:lang] || el.attr["class"].to_s[/language-(\S+)/, 1]
    code = %(<code class="language-#{language}">#{escape_html(el.value.chomp)}</code>)
    %(<div class="notion-code no-wrap"><button class="notion-code__copy-button">#{COPY_ICON}Copy</button>) +
      %(<pre class="language-#{language}">#{code}</pre><figcaption class="notion-caption notion-semantic-string"></figcaption></div>\n)
  end
end

Kramdown::Converter::Html.prepend(NotionMarkdown)
