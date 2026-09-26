# Order the pages in one sequence, and link each to the pages before and after it, as page.previous and page.next.
#
# The sequence is the sidebar's pages, in order, each followed by the pages that its galleries and page links point
# to, in their order, and their pages in turn.
module Sequence
  CHILD = %r{^\s*(?:-\s+)?link:\s*["']?(/[^\s"']*)|\{% page (/\S*)}

  class Generator < Jekyll::Generator
    def generate(site)
      sidebar = File.read(File.join(site.source, "_includes", "sidebar-#{site.config["lang"]}.html"))
      top = sidebar.scan(/\{% page (\S+)/).flatten
      pages = site.pages.to_h { |page| [page.url, page] }
      sequence = []
      seen = Set.new
      visit = lambda do |path|
        page = pages[path]
        return if !page || seen.include?(path)

        seen << path
        sequence << page
        page.content.scan(CHILD).flatten.compact.each { |child| visit.call(child) unless top.include?(child) }
      end
      top.each { |path| visit.call(path) }

      sequence.each_with_index do |page, i|
        page.data["previous"] = link(sequence[i - 1]) if i.positive?
        page.data["next"] = link(sequence[i + 1]) if sequence[i + 1]
      end
    end

    private

    def link(page)
      { "url" => page.url, "title" => page.data["title"] }
    end
  end
end
