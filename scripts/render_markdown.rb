# Render a JSON array of Markdown strings (on standard input) with the site's Markdown converter, as a JSON array.
require "jekyll"
require "json"

site = Jekyll::Site.new(Jekyll.configuration("config" => ["_config.yml", "_config.en.yml"], "quiet" => true))
converter = site.find_converter_instance(Jekyll::Converters::Markdown)
puts JSON.generate(JSON.parse($stdin.read).map { |markdown| converter.convert(markdown) })
