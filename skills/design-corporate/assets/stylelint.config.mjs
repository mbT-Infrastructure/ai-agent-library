// Optional, opt-in stylelint guard for web projects using the corporate design.
// This file is not part of any build and adds no dependency to this repository.
// Use it from a consumer project that already has stylelint installed:
//
//     npm install --save-dev stylelint
//     // stylelint.config.mjs
//     export default {
//         extends: ["<path-to>/skills/design-corporate/assets/stylelint.config.mjs"],
//     };
//
// Or copy the `rules` object into an existing config. `color-no-hex` catches hex
// anywhere; the disallowed-list keeps color-only properties on the design tokens
// (transparent and currentColor are allowed).
export default {
    rules: {
        "color-no-hex": true,
        "declaration-property-value-disallowed-list": {
            "/^(?:color|background-color|border(?:-(?:top|right|bottom|left))?-color|outline-color|text-decoration-color|caret-color|accent-color|fill|stroke)$/": [
                "/^(?!var\\(--md-sys-color-[a-z0-9-]+\\)$|var\\(--cd-[a-z0-9-]+\\)$|transparent$|currentColor$).+/",
            ],
        },
    },
};
