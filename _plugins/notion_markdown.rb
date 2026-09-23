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

  CLASSES.each do |type, classes|
    define_method(:"convert_#{type}") do |el, indent|
      el.attr["class"] ||= classes
      el.attr["type"] ||= "1" if type == :ol
      super(el, indent)
    end
  end
end

Kramdown::Converter::Html.prepend(NotionMarkdown)
