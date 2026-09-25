const strategy = process.env.PA11Y_STRATEGY;
const includeWarnings = "PA11Y_INCLUDE_WARNINGS" in process.env;
const suppressKnownWarnings = "PA11Y_SUPPRESS_KNOWN_WARNINGS" in process.env;

const knownErrors = [];

const knownWarnings = [
  {
    // "This element's text or background contains transparency." (Notion's colours are translucent, and the axe
    // runner's color-contrast rule, which blends them, reports no errors)
    // https://www.w3.org/WAI/WCAG21/Techniques/general/G18
    rules: ["WCAG2AA.Principle1.Guideline1_4.1_4_3.G18.Alpha"],
    selectors: [],
  },
  {
    // "Elements must meet minimum color contrast ratio thresholds." (needs review: a database table view's cells clip
    // their content, and a gallery card's link is over its cover and properties)
    // "This element is absolutely positioned and the background color can not be determined." (a gallery card's link
    // covers the card, a code block's copy button is over the code, and a database table's caption is visually hidden)
    rules: ["color-contrast", "WCAG2AA.Principle1.Guideline1_4.1_4_3.G18.Abs"],
    selectors: [
      ".notion-collection-table .notion-property",
      ".notion-collection-table__head-cell-content",
      ".notion-page__property .notion-property",
      ".notion-collection-card__anchor",
      ".notion-collection-card__property",
      ".notion-code__copy-button",
      ".notion-collection-table > caption",
    ],
  },
  {
    // "This element has "position: fixed"." (the search dialog)
    // https://www.w3.org/WAI/WCAG21/Understanding/reflow.html
    rules: ["WCAG2AA.Principle1.Guideline1_4.1_4_10.C32,C31,C33,C38,SCR34,G206"],
    selectors: [],
  },
  {
    // "Check that this element has an inherited foreground/background colour…" (a table row sets the text colour,
    // and its cells set the background colour)
    // https://www.w3.org/WAI/WCAG21/Techniques/failures/F24
    rules: [
      "WCAG2AA.Principle1.Guideline1_4.1_4_3_F24.F24.BGColour",
      "WCAG2AA.Principle1.Guideline1_4.1_4_3_F24.F24.FGColour",
    ],
    selectors: [".notion-table tr"],
  },
  {
    // "Img element is marked so that it is ignored by Assistive Technology." (a page's icon, next to its title)
    rules: ["WCAG2AA.Principle1.Guideline1_1.1_1_1.H67.2"],
    selectors: ["img.notion-icon", "img.notion-breadcrumb__icon"],
  },
  {
    // "Frames should be tested with axe-core." (a PDF)
    rules: ["frame-tested"],
    selectors: [".notion-pdf iframe"],
  },
  {
    // "If this element contains a navigation section, it is recommended that it be marked up as a list." (prose paragraphs
    // and columns with several links, which aren't lists: see #28)
    rules: ["WCAG2AA.Principle1.Guideline1_3.1_3_1.H48"],
    selectors: [".notion-column", "p.notion-text"],
  },
  {
    // "Heading markup should be used if this content is intended as a heading." (Notion's bold paragraphs: see #17)
    rules: ["WCAG2AA.Principle1.Guideline1_3.1_3_1.H42"],
    selectors: [],
  },
  {
    // "The heading structure is not logically nested." (headings are at Notion's levels: see #17)
    rules: ["WCAG2AA.Principle1.Guideline1_3.1_3_1_A.G141", "heading-order"],
    selectors: [],
  },
];

function createDefaults(extraKnownWarnings = []) {
  const suppressions = [
    ...knownErrors,
    ...(includeWarnings && suppressKnownWarnings ? [...knownWarnings, ...extraKnownWarnings] : []),
  ];

  const withoutSelectors = suppressions.filter((suppression) => !suppression.selectors.length);
  const withSelectors = suppressions.filter((suppression) => suppression.selectors.length);

  const hideElements =
    strategy === "hideElements" ? withSelectors.flatMap((suppression) => suppression.selectors) : [];
  const ignore = [
    ...withoutSelectors.flatMap((suppression) => suppression.rules),
    ...(strategy === "ignore" ? withSelectors.flatMap((suppression) => suppression.rules) : []),
  ];

  return {
    runners: ["htmlcs", "axe"],
    levelCapWhenNeedsReview: "warning",
    includeWarnings: includeWarnings,
    ...(hideElements.length ? { hideElements: hideElements.join(", ") } : {}),
    ...(ignore.length ? { ignore: ignore } : {}),
    timeout: 60000,
  };
}

module.exports = {
  createDefaults,
  defaults: createDefaults(),
  concurrency: 4,
};
