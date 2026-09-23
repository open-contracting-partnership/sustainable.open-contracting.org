# Render a JSON array of pages' content (on standard input) with the site's Liquid tags and Markdown converter.
require "jekyll"
require "json"

site = Jekyll::Site.new(Jekyll.configuration("config" => ["_config.yml", "_config.en.yml"], "quiet" => true))
converter = site.find_converter_instance(Jekyll::Converters::Markdown)
output = JSON.parse($stdin.read).map do |content|
  liquid = Liquid::Template.parse(content).render!({}, registers: { site: site, page: {} })
  converter.convert(liquid)
end
puts JSON.generate(output)
