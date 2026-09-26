# Renumber each page's headings from <h2>, below the page's title, in the order of the Markdown levels that the page
# uses, and at most a level below the heading before it, so that no level is skipped. Their classes, not their tags,
# set their sizes. A database's title is a level below the Markdown heading before it.
HEADING = %r{<h([1-6])([^>]*?) class="((?:notion-heading [^"]*)|notion-collection__header)"(.*?)</h\1>}m

Jekyll::Hooks.register :pages, :post_render do |page|
  next unless page.output_ext == ".html"

  levels = page.output.scan(/notion-heading--(\d)/).flatten.map(&:to_i).uniq.sort
  next if levels.empty? && !page.output.include?("notion-collection__header")

  previous = 1
  page.output = page.output.gsub(HEADING) do
    attributes, classes, rest = Regexp.last_match(2), Regexp.last_match(3), Regexp.last_match(4)
    if classes == "notion-collection__header"
      level = previous + 1
    else
      level = previous = [levels.index(classes[/notion-heading--(\d)/, 1].to_i) + 2, previous + 1].min
    end
    %(<h#{level}#{attributes} class="#{classes}"#{rest}</h#{level}>)
  end
end
