# Audit checks

`scripts/ui_audit.py` loads the page with the Playwright `iPhone 13 Mini`
profile (portrait and landscape by default) and reports advisory findings.
Severity orders the review; it is not a verdict. A finding becomes a defect
only after you confirm it on the page.

Clear an accepted exception with `--ignore SELECTOR` (the element and its
descendants) or `--skip CHECK_ID`, and record the reason in the report.
Accepted exceptions stay visible: overflow caused only by ignored elements is
reported with severity `accepted` and lists them under `ignoredCulprits`.

| Check           | Severity            | Rule                                                                  | Basis |
| --------------- | ------------------- | --------------------------------------------------------------------- | ----- |
| `overflow-x`    | error / accepted    | `scrollWidth` > `documentElement.clientWidth`; lists unclipped non-fixed elements past either edge. When every such element is an `--ignore` exception the finding is `accepted`, not `error`; with no element found it stays `error` with a hint (margins, transforms, pseudo-elements) | layout fact |
| `offscreen`     | warning             | `position: fixed` element partly outside 0..375 px. Fixed boxes never widen the document, so `overflow-x` cannot see them; fully off-canvas panels are not reported | layout fact |
| `touch-target`  | warning below 28 pt, info below 44 pt | visible interactive element whose shorter side is under the size; links inside running text are skipped | [Apple HIG, Accessibility][hig]: iOS default 44x44 pt, minimum 28x28 pt |
| `input-zoom`    | warning             | text input, textarea or select with computed `font-size` < 16px        | widely reported iOS Safari behavior ([CSS-Tricks][zoom]); not documented by Apple; confirm at L2 |
| `viewport-meta` | error / warning / info | missing tag; no `width=device-width`; zoom restricted by `user-scalable=no` or `maximum-scale=1` | without the tag Safari on iOS uses a 980 px layout width ([Apple][viewport]); zoom restriction harms accessibility |
| `safe-area`     | warning / device-verify | `viewport-fit=cover` without any `env(safe-area-inset-*)` in readable CSS; fixed or sticky elements touching the top or bottom edge | [WebKit safe areas][safe] |
| `vh-units`      | info                | `height`, `min-height` or `max-height` of `100vh`                      | [dynamic viewport units][units] |
| `hover-only`    | info                | `:hover` rule outside `@media (hover: hover)` / `(any-hover: hover)`   | hover can persist after a tap on touch screens |
| `clipped-text`  | info                | element with direct text whose `scrollWidth` exceeds its width under clipping or ellipsis | intended truncation is fine; clear it with `--ignore` |

Coverage limits: cross-origin stylesheets cannot be read and are counted in
the report; CSS-in-JS rules are seen only once inserted; inline-style
`safe-area-inset` is detected, computed `env()` values are not traced back to
rules. Elements hidden at load (menus, dialogs) are audited only if you open
them first, for example with `--ready-js` that triggers the state.

Touch-target sizes are CSS px. At DPR 3 with page zoom 1, one CSS px is one
point. Spacing between controls also matters to the HIG and is not measured.

## Symptom to cause

| Symptom (where seen)                              | Likely cause                                         | Evidence to collect |
| ------------------------------------------------- | ---------------------------------------------------- | ------------------- |
| Page scrolls sideways (any level)                 | element wider than 375 px, negative margin, long unbroken string, `100vw` plus scrollbar | `overflow-x` culprits, `innerWidth` vs `clientWidth` |
| Content hidden under the bottom toolbar (L2)      | `100vh` or fixed `bottom: 0` without safe-area padding | probe `css.dvh` vs `innerHeight` with toolbar expanded and collapsed |
| Content under the notch or status bar (L2)        | `viewport-fit=cover` without `env(safe-area-inset-top)` | probe `css.safeAreaTop`, native screenshot |
| Page zoomed after typing, does not zoom back (L2) | input font-size below 16px                           | `input-zoom` finding; `visualViewport.scale` after blur |
| Button looks pressed after tap (L2)               | `:hover` style without `(hover: hover)` guard        | `hover-only` finding |
| CTA covered when the keyboard opens (L2)          | fixed element positioned against the layout viewport | `visualViewport.height/offsetTop` with keyboard open |
| Gap or jump when the toolbar collapses (L2)       | height in `vh`/`dvh` recalculated during scroll      | captures before/after scroll, probe `svh/lvh/dvh` |
| Text wraps differently than locally (L2)          | San Francisco metrics vs Linux fallback font         | element boxes on both sides, not pixels |
| Tiny or overlapping controls (any level)          | sizes tuned for desktop pointer                      | `touch-target` findings, screenshot |

[hig]: https://developer.apple.com/design/human-interface-guidelines/accessibility
[viewport]: https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/SafariWebContent/UsingtheViewport/UsingtheViewport.html
[zoom]: https://css-tricks.com/16px-or-larger-text-prevents-ios-form-zoom/
[safe]: https://webkit.org/blog/7929/designing-websites-for-iphone-x/
[units]: https://webkit.org/blog/12445/new-webkit-features-in-safari-15-4/
