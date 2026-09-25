import { readdir, readFile, rm } from "node:fs/promises";
import { join } from "node:path";
import purgecss from "@fullhuman/postcss-purgecss";
import autoprefixer from "autoprefixer";
import browserslist from "browserslist";
import * as esbuild from "esbuild";
import { esbuildPluginBrowserslist } from "esbuild-plugin-browserslist";
import postcss from "postcss";

const production = process.env.NODE_ENV === "production";

// The site whose built stylesheets to bundle: en, es or fr.
const site = join("_site", process.argv[2]);
const directory = join(site, "assets", "css");

const processor = postcss([
  purgecss({
    // site.js's class names are in its source, like those in the pages' HTML.
    content: [join(site, "**", "*.html"), join(site, "assets", "js", "*.js")],
  }),
  autoprefixer,
]);

const options = {
  entryPoints: { main: join(directory, "main.css") },
  bundle: true,
  outdir: directory,
  // main.css is overwritten.
  allowOverwrite: true,
  minify: production,
  sourcemap: !production,
  legalComments: "linked",
  logLevel: "info",
  loader: { ".woff2": "file" },
  plugins: [
    esbuildPluginBrowserslist(browserslist(), { printUnknownTargets: false }),
    {
      name: "postcss",
      setup(build) {
        build.onLoad({ filter: /\.css$/ }, async (args) => {
          const { css } = await processor.process(await readFile(args.path, "utf8"), { from: args.path });
          return { contents: css, loader: "css" };
        });
      },
    },
  ],
};

// The stylesheets that main.css imports.
const imported = (await readdir(directory)).filter((name) => name.endsWith(".css") && name !== "main.css");

await esbuild.build(options);

for (const name of imported) {
  await rm(join(directory, name));
}
// esbuild copies the fonts that the stylesheets use, with content hashes.
await rm(join(site, "assets", "fonts"), { recursive: true });
