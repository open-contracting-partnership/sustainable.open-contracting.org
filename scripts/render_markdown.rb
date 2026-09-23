# Render pages' content with the site's Liquid tags and Markdown converter.
#
# Standard input is a JSON object with "documents" (a list of objects with "content" and "lang") and "pages" (an object
# of languages to objects of permalinks to front matter). Standard output is a JSON array of HTML.
require "jekyll"
require "json"

# Jekyll caches conversions by content, not by plugin code, so the cache could be stale.
config = Jekyll.configuration("config" => ["_config.yml", "_config.en.yml"], "quiet" => true, "disable_disk_cache" => true)
site = Jekyll::Site.new(config)
converter = site.find_converter_instance(Jekyll::Converters::Markdown)
input = JSON.parse($stdin.read)
output = input["documents"].map do |document|
  registers = { site: site, page: {}, notion_pages: input["pages"].fetch(document["lang"], {}) }
  converter.convert(Liquid::Template.parse(document["content"]).render!({}, registers: registers))
end
puts JSON.generate(output)
