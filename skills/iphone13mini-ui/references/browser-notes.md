# Browser notes

## Setup

I use the project's Python environment (3.10+) and existing browser installation.
When dependencies are missing:

```bash
python3 -m pip install -r "$SKILL_DIR/scripts/requirements.txt"
python3 -m playwright install --with-deps webkit
```

For Chromium I pass `--engine chromium`; `--executable PATH` selects an installed
Chrome/Chromium binary. The helpers do not switch engines after a launch failure.
I retain the Playwright/browser versions in capture metadata so a renderer update
is distinguishable from a layout change.

## Geometry and CSS

The logical screen is 375×812 in portrait, with nominal DPR 3. Screen dimensions,
page viewport and screenshot pixels are different measurements. I read viewport
and user-agent defaults from the installed [Playwright profile][emulation], not
from an assumed Safari version. For a phone reference I use its measured viewport.

| Symptom | What I inspect or change |
|---|---|
| Horizontal overflow | `scrollWidth` versus `clientWidth`, then offending boxes; flex/grid min-content sizing, unbroken strings, fixed widths and absolute/fixed positioning. I use `min-width: 0`, wrapping or a deliberate scroller where appropriate. |
| Unusable controls | Hit area and spacing, including associated labels. I use roughly 44 CSS px as a starting point for standalone touch targets, not a rule for every inline link. |
| Focus zoom | Computed input font size and page scale on the phone. The audit's 16px threshold is a heuristic, not a browser conformance rule. |
| Toolbar overlap or jumping height | `100svh` for a stable minimum-height viewport; `100dvh` when the layout should follow browser controls. I choose by the interaction, not by replacing every `vh`. |
| Edge content under a cutout | `viewport-fit=cover` and padding with `env(safe-area-inset-*)`; I account for existing padding rather than applying the inset twice. |
| Keyboard covers a control | `visualViewport.height`, offsets and focus scrolling on the phone; a smaller desktop viewport does not reproduce the keyboard. |
| Different line breaks | Loaded fonts, computed family/weight/line-height and element widths. Linux system fonts and rasterization differ from iOS. |
| Sticky hover after tapping | Hover-only styling and the equivalent tap/focus action; I scope decorative hover effects with `(hover: hover)` where appropriate. |

I retain `width=device-width, initial-scale=1` in the viewport meta tag. A native
safe-area constant is not the value Safari must return in a tab. Chromium's
experimental `--safe-area TOP,RIGHT,BOTTOM,LEFT` is a synthetic CSS scenario;
WebKit capture has no equivalent override.

## Audit scope

`ui_audit.py` checks the current top-level light DOM. It reports horizontal
geometry, control sizes, input-font hints, viewport metadata, edge positioning,
readable CSS and clipped text. I use `--ignore SELECTOR` for intentional element
exceptions and `--skip CHECK` for inapplicable checks.

I inspect hidden menus, dialogs, frames and shadow roots through the project's
browser flow. A readiness predicate waits for state; it is not a script for
repeated clicks. Unreadable stylesheets, failed resources and excluded checks
limit coverage. No findings means no findings in that scan, not a complete UX
review.

[emulation]: https://playwright.dev/python/docs/emulation

Sources: [WebKit safe areas](https://webkit.org/blog/7929/designing-websites-for-iphone-x/),
[viewport units](https://webkit.org/blog/12445/new-webkit-features-in-safari-15-4/),
[Apple control guidance](https://developer.apple.com/design/human-interface-guidelines/accessibility),
[Chromium safe-area override](https://chromedevtools.github.io/devtools-protocol/tot/Emulation/#method-setSafeAreaInsetsOverride).
