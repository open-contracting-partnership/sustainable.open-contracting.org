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
  minify: production,
  sourcemap: !production,
  legalComments: "linked",
  logLevel: "info",
  // The layout preloads the fonts, at their paths.
  external: ["*.woff2"],
  // main.css is overwritten.
  allowOverwrite: true,
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

await esbuild.build(options);

// The stylesheets that main.css imports.
for (const name of await readdir(directory)) {
  if (name.endsWith(".css") && name !== "main.css") await rm(join(directory, name));
}
