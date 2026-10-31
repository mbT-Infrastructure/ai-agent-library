---
name: design-corporate
description:
    Use whenever creating, editing or reviewing UI - Svelte/SvelteKit, HTML/CSS, Material 3 /
    @material/web components, Jetpack Compose screens, themes, colors, typography, spacing, buttons,
    forms, navigation or status states.
---

# design-corporate — mbT corporate design

## When to use / when not to

- **Use** for any UI surface: Svelte/SvelteKit, HTML/CSS, `@material/web`, Material 3 themes,
  Jetpack Compose screens, colors, typography, spacing, buttons, forms, navigation, status states.
- **Do not use** for backend logic, CLIs, infrastructure, build tooling or data-only changes.

## Non-negotiables

1. **Page background is always white in light mode** (`--md-sys-color-surface: #FFFFFF`); grey is
   structure (borders, chrome, dark surfaces), not a background color.
2. **Orange has exactly three jobs: CTA, active nav item, chart highlight.** Never scatter it
   decoratively; its impact lives in its scarcity.
3. **Text on orange is always black** (`--md-sys-color-on-tertiary`), never white.
4. **Primary ≠ CTA:** primary is jet black (light) / traffic white (dark); the CTA is the only
   orange button on the page, max. **one CTA per view**.
5. **Links use `--cd-link` / `--cd-link-hover`, never RAL 2004.**
6. **Dynamic color / `ColorScheme.fromSeed()` is forbidden.** The tokens are the scheme.
7. RAL 7016 appears on hero/brand surfaces and `surface-container-highest` (dark) only — never as a
   page or card background.
8. Status colors stay tinted background + dark text; warning is yellow/amber, never orange.
9. **Signal Blue is info only** (RAL 5005, `info` family) — never a button, nav item or accent.

## Brand anchors (do not modify)

- RAL 9005 `#0A0A0A` — jet black, primary action color.
- RAL 7016 `#383E42` — anthracite grey, structure and brand/hero surfaces.
- RAL 9016 `#F1F0EA` — traffic white, warm off-white and text on dark.
- RAL 2004 `#E75B12` — pure orange, the only accent (three jobs only).
- RAL 5005 `#005387` — signal blue, info only.

## Role table

CSS variable names are included so `var()` can be emitted without opening `tokens.css`.

| Role                          | Light                         | Dark                  | Usage                                       | CSS variable(s)                                                              |
| ----------------------------- | ----------------------------- | --------------------- | ------------------------------------------- | ---------------------------------------------------------------------------- |
| `primary` / `on-primary`      | `#0A0A0A` / `#F1F0EA`         | `#F1F0EA` / `#0A0A0A` | buttons, switches, sliders                  | `--md-sys-color-primary` / `--md-sys-color-on-primary`                       |
| `primary-container` / `on-`   | `#383E42` / `#F1F0EA`         | `#2C3032` / (same)    | tonal containers, selected states           | `--md-sys-color-primary-container` / `--md-sys-color-on-primary-container`   |
| `tertiary` / `on-tertiary`    | `#E75B12` / `#0A0A0A`         | `#FF8A3D` / (same)    | the orange cta — the only orange button     | `--md-sys-color-tertiary` / `--md-sys-color-on-tertiary`                     |
| `tertiary-container` / `on-`  | `#F6E9E2` / `#723615`         | `#4F2712` / `#EBBEA5` | orange-tinted chips, highlights             | `--md-sys-color-tertiary-container` / `--md-sys-color-on-tertiary-container` |
| `success` / `on-success`      | `#256E43` / `#F1F0EA`         | `#8FD5A8` / `#0F2A19` | confirmations, online states                | `--cd-success` / `--cd-on-success`                                           |
| `warning` / `on-warning`      | `#8A5A00` / `#F1F0EA`         | `#FFD48A` / `#2E2000` | cautions, degraded states                   | `--cd-warning` / `--cd-on-warning`                                           |
| `info` / `on-info`            | `#005387` / `#F1F0EA`         | `#AAD4EE` / `#092434` | neutral hints, tips (signal blue, ral 5005) | `--cd-info` / `--cd-on-info`                                                 |
| `link` / `link-hover`         | `#954216` / `#723615`         | `#FF8A3D` / `#EBBEA5` | text links on body surfaces                 | `--cd-link` / `--cd-link-hover`                                              |
| `surface` / `on-surface`      | `#FFFFFF` / `#0A0A0A`         | `#131516` / `#F1F0EA` | backgrounds / text                          | `--md-sys-color-surface` / `--md-sys-color-on-surface`                       |
| `surface-container-highest`   | `#E1E3E5`                     | `#383E42`             | elevated cards, sheets                      | `--md-sys-color-surface-container-highest`                                   |
| `surface-variant` / `on-`     | `#F1F0EA` / `#606A71`         | `#212426` / `#A2AAAF` | input fills, secondary text                 | `--md-sys-color-surface-variant` / `--md-sys-color-on-surface-variant`       |
| `outline` / `outline-variant` | `#7D8991` / `#E1E3E5`         | — / `#3A3F42`         | input borders / decorative lines            | `--md-sys-color-outline` / `--md-sys-color-outline-variant`                  |
| `error` / `on-error`          | `#A33030` / `#F1F0EA`         | `#F59A9A` / `#3A1A1A` | error states                                | `--md-sys-color-error` / `--md-sys-color-on-error`                           |
| `inverse-*`                   | snackbars, tooltips (defined) |                       |                                             | `--md-sys-color-inverse-surface` / `--md-sys-color-inverse-on-surface`       |

## Recipes

**Web (Svelte / `@material/web`)** — one file, minimal:

```svelte
<script lang="ts">
    import '@material/web/button/filled-button.js';
    import '@material/web/button/text-button.js';
    import '@material/web/card/elevated-card.js';
    import '@material/web/textfield/outlined-text-field.js';
    import { theme, toggleTheme } from '@corporate-design/theme.ts';
</script>

<!-- why: primary is the black action color; orange is reserved for the CTA -->
<md-filled-button>Save</md-filled-button>
<!-- why: low-emphasis action stays on-surface, never orange -->
<md-text-button>Cancel</md-text-button>
<!-- why: the one orange CTA — tertiary container, black on-tertiary label -->
<md-filled-button class="cta">Continue</md-filled-button>
<!-- why: elevated card on the white page; RAL 7016 is never a card background -->
<md-elevated-card class="card">
    <h2 class="card-title">Title</h2>
    <p class="card-body">Supporting text.</p>
</md-elevated-card>
<!-- why: outlined field; @material/web reads the outline and surface tokens itself -->
<md-outlined-text-field label="Email" type="email"></md-outlined-text-field>
<!-- why: tinted container + dark text; warning is amber, never orange -->
<span class="badge success">Online</span> <span class="badge warning">Degraded</span> <span class="badge error">Failed</span> <span class="badge info">Info</span>
<!-- why: active nav is one of orange's three jobs; black text on orange -->
<a href="/" class="nav-item" aria-current="page">Home</a>
<a href="/reports" class="nav-item">Reports</a>
<!-- why: the store persists data-theme; the label follows the live state -->
<button class="theme-toggle" onclick={toggleTheme}>{$theme === 'light' ? 'Dark mode' : 'Light mode'}</button>
<style>
    .cta { --md-filled-button-container-color: var(--md-sys-color-tertiary); --md-filled-button-label-text-color: var(--md-sys-color-on-tertiary); }
    .card { padding: 16px; }
    .card-title { font: var(--md-sys-typescale-title-medium); color: var(--md-sys-color-on-surface); }
    .card-body { font: var(--md-sys-typescale-body-medium); color: var(--md-sys-color-on-surface-variant); }
    .badge { padding: 2px 10px; border-radius: var(--md-sys-shape-corner-full); font: var(--md-sys-typescale-label-small); }
    .success { background: var(--cd-success-container); color: var(--cd-on-success-container); }
    .warning { background: var(--cd-warning-container); color: var(--cd-on-warning-container); }
    .error { background: var(--md-sys-color-error-container); color: var(--md-sys-color-on-error-container); }
    .info { background: var(--cd-info-container); color: var(--cd-on-info-container); }
    .nav-item { padding: 8px 12px; border-radius: var(--md-sys-shape-corner-full); color: var(--md-sys-color-on-surface-variant); text-decoration: none; }
    .nav-item[aria-current="page"] { background: var(--md-sys-color-tertiary); color: var(--md-sys-color-on-tertiary); }
    .theme-toggle { border: 0; background: none; color: var(--md-sys-color-primary); cursor: pointer; }
</style>
```

**Compose (Jetpack Compose Material 3)**:

```kotlin
// why: one wrapper applies CdLightColors/CdDarkColors, CdTypography and CdShapes
CdTheme {
    AppNavHost()
}
// why: the single orange CTA; onTertiary is black, never white
Button(
    onClick = { save() },
    colors = ButtonDefaults.buttonColors(
        containerColor = MaterialTheme.colorScheme.tertiary,
        contentColor = MaterialTheme.colorScheme.onTertiary,
    ),
) {
    Text("Continue")
}
// why: status/link colors are outside ColorScheme; tinted container + dark text
val cd = cdSemanticColors()
Surface(color = cd.successContainer, contentColor = cd.onSuccessContainer, shape = RoundedCornerShape(50)) {
    Text("Online", style = MaterialTheme.typography.labelSmall)
}
```

## Setup

`+layout.svelte` — import the tokens once and initialise the theme store:

```svelte
<script>
    import '@corporate-design/tokens.css';
    import { initTheme } from '@corporate-design/theme.ts';
    initTheme();
</script>

<slot />
```

No flash of light theme — inline script at the end of `<head>` in `app.html`:

```html
<script>
    const t = localStorage.getItem("cd-theme");
    document.documentElement.dataset.theme =
        t === "dark" || (!t && matchMedia("(prefers-color-scheme: dark)").matches)
            ? "dark"
            : "light";
</script>
```

```bash
npm install @material/web
```

Android — copy the five generated files, adjust `package`, then wrap the app with `CdTheme`:

```bash
cp android/CdColor.kt android/CdType.kt android/CdShape.kt android/CdSemantic.kt android/CdTheme.kt \
    app/src/main/kotlin/<your-package>/corporatedesign/
```

Long version:
<https://github.com/mbT-Solutions/corporate-design/blob/main/Readme.md#android-jetpack-compose-material-3>

## Progressive disclosure

The tables above cover ~95% of cases. Read `tokens.css` only for roles not listed here; read
`tokens.json` only when changing token values. Never edit `tokens.css` or `android/*.kt` by hand —
they are generated by `generate.py`; run `python3 generate.py` and commit all outputs together.

## Checklist before finishing

- [ ] No hardcoded hex/rgb/`Color(0x…)` outside the design-system files (`tokens.css`, `theme.ts`,
      `*.tokens.*`, `Cd*.kt`).
- [ ] Colors only via `var(--md-sys-color-*)`, `var(--cd-*)` or `MaterialTheme.colorScheme`.
- [ ] At most one orange CTA per view; orange used only for CTA, active nav, chart highlight.
- [ ] Contrast pairs from the role table; text on orange is black.
- [ ] Page surface is white in light mode; no RAL 7016 page or card backgrounds.
- [ ] `bash skills/design-corporate/scripts/check-design.sh <changed files>` passes.

## Sources

- Repo: <https://github.com/mbT-Solutions/corporate-design> (branch `main`, v0.1.0) · rules:
  <https://github.com/mbT-Solutions/corporate-design/blob/main/Readme.md>
- Tokens: <https://github.com/mbT-Solutions/corporate-design/blob/main/tokens.css> ·
  <https://github.com/mbT-Solutions/corporate-design/blob/main/tokens.json>
- Theme store: <https://github.com/mbT-Solutions/corporate-design/blob/main/theme.ts> · Compose:
  <https://github.com/mbT-Solutions/corporate-design/tree/main/android>

If this skill and the repo disagree, the repo wins; report the drift instead of guessing.
