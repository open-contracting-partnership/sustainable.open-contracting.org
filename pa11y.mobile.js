const base = require("./pa11y.default.js");

const knownWarnings = [];

module.exports = {
  ...base,
  defaults: {
    ...base.createDefaults(knownWarnings),
    viewport: {
      width: 320,
      height: 480,
      deviceScaleFactor: 2,
      isMobile: true,
    },
  },
};
