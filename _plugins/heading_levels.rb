# Renumber each page's headings from <h2>, below the page's title (or from <h1>, if the title is hidden), in the order
# of the Markdown levels that the page uses, and at most a level below the heading before it, so that no level is
# skipped. Their classes, not their tags, set their sizes.
HEADING = %r{<h([1-6])([^>]*?) class="(notion-heading [^"]*)"(.*?)</h\1>}m

Jekyll::Hooks.register :pages, :post_render do |page|
  next unless page.output_ext == ".html"

  levels = page.output.scan(/notion-heading--(\d)/).flatten.map(&:to_i).uniq.sort
  next if levels.empty?

  # Without its title, the page's first level is <h1>.
  first = page.data["hide_title"] ? 1 : 2
  previous = first - 1
  page.output = page.output.gsub(HEADING) do
    attributes, classes, rest = Regexp.last_match(2), Regexp.last_match(3), Regexp.last_match(4)
    level = previous = [levels.index(classes[/notion-heading--(\d)/, 1].to_i) + first, previous + 1].min
    %(<h#{level}#{attributes} class="#{classes}"#{rest}</h#{level}>)
  end
end
