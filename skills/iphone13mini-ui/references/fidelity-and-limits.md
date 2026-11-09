# Fidelity and limits

What each environment reproduces for iPhone 13 mini Safari, and where only the
real device can answer. Facts marked **[verified]** were re-read from the cited
primary source when this skill was written (November 2026). Facts marked
**[research]** come from the bundled research and were not re-checked here.

## Device geometry

| Quantity                         | Value                          | Status and source |
| -------------------------------- | ------------------------------ | ----------------- |
| Display                          | 5.4", 2340x1080 px, 476 ppi    | [verified] [Apple specs][apple-specs] |
| Screen in points                 | 375x812 pt                     | [verified] [Use Your Loaf][uyl] |
| Native scale                     | 2.88x (screenshot scale is 3x) | [verified] [Use Your Loaf][uyl] |
| Screenshot at 3x                 | 1125x2436 px                   | derived: 375x3, 812x3; matches the bundled frame |
| Safe-area insets, portrait       | top 50, right 0, bottom 34, left 0 pt | [verified] [Use Your Loaf][uyl] (device baseline) |
| Safe-area insets, landscape      | top 0, right 50, bottom 21, left 50 pt | [verified] [Use Your Loaf][uyl] (device baseline) |
| Playwright `iPhone 13 Mini`      | screen 375x812, viewport 375x629, DPR 3, mobile, touch | [verified] [descriptor][pw-devices] |
| Playwright landscape             | viewport 712x327               | [verified] [descriptor][pw-devices] |

Device baseline insets are not what `env(safe-area-inset-*)` returns in an
ordinary Safari tab; that depends on `viewport-fit`, orientation, toolbar and
display mode. Measure it on the phone ([real device](real-device.md)).

The Playwright descriptor's user agent combines `iPhone OS 15_0` with
`Version/27.2` [verified]. It is synthetic: keep it in metadata, do not treat
it as an iOS version, and expect UA-sniffing sites to react to it.

## Viewport terms

- `screen.width/height`: logical screen, not the usable height.
- `innerWidth/innerHeight`: layout viewport. On mobile engines it can grow to
  fit overflowing content, so `innerWidth > 375` is itself an overflow signal.
- `documentElement.clientWidth/clientHeight`: layout viewport without that
  growth; compare `scrollWidth` against it.
- `visualViewport.*`: the visible region; changes with pinch zoom and the
  on-screen keyboard.
- `page.screenshot(full_page=False)`: web content only, no Safari chrome.
- A native iPhone screenshot: the whole screen with status bar and Safari UI.

`svh`, `lvh` and `dvh` are the small, large and dynamic viewport heights;
`dvh` changes as Safari's toolbar collapses and expands [verified]
([WebKit, Safari 15.4][webkit-units]). A local engine has no toolbar, so all
three report the same value there. A 375x684 or 375x812 local viewport is a
stress scenario, not a measured Safari height.

## What each engine reproduces

| Area                                  | L0 Chromium | L1 Linux WebKit | L2 iPhone |
| ------------------------------------- | ----------- | --------------- | --------- |
| Width-driven layout, overflow, grid/flex | yes      | yes             | yes       |
| WebKit-specific CSS and layout quirks | no          | mostly          | yes       |
| Safari toolbar states, dynamic viewport | no        | no              | yes       |
| Real `env(safe-area-inset-*)`         | synthetic only (CDP override) | no | yes |
| On-screen keyboard, focus scroll, input zoom | no   | no              | yes       |
| Native pickers (select, date, file)   | no          | no              | yes       |
| San Francisco text metrics, CoreText  | no          | no              | yes       |
| Color pipeline (Display P3, OLED)     | no          | no              | screenshot only |
| Gestures, inertia, rubber-band        | no          | no              | yes       |
| Home Screen web app (standalone)      | no          | no              | yes       |

Playwright headless WebKit on Linux runs the WPE MiniBrowser; headed runs
GTK [verified] ([pw_run.sh][pw-run]). It shares WebCore with Safari but not
the iOS platform layer, fonts, compositor or browser UI [research]
([WebKit ports][webkit-ports], [Playwright browsers][pw-browsers]).

Chromium's `Emulation.setSafeAreaInsetsOverride` overrides
`env(safe-area-inset-*)` and is marked experimental [verified]
([CDP][cdp-safe-area]). No public WebKit equivalent was found; fake CSS
custom properties do not replace `env()`.

## Fonts

`system-ui` / `-apple-system` resolve to San Francisco only on Apple
platforms. On Linux they resolve through Fontconfig to another family, so line
breaks and text widths are approximate at L0/L1 [research]. San Francisco is
distributed under Apple's own license for Apple-platform mockups
([Apple Fonts][apple-fonts]); do not install it globally or ship it as a
webfont. With an app-supplied webfont, wait for `document.fonts.ready` on both
sides and compare wrap points and element boxes, not pixels.

## High-risk states

| State                               | Risk a local render misses                   | Check at L2 |
| ----------------------------------- | -------------------------------------------- | ----------- |
| Fixed bottom CTA + keyboard         | CTA under keyboard or toolbar                | focus an input, capture, then blur |
| `100vh`/`100dvh` layouts, scroll-snap | jump or empty band when the toolbar moves  | before and after scrolling |
| Text inputs below 16px              | page zooms on focus and stays zoomed         | type, blur, check `visualViewport.scale` |
| `<select>`, date, file inputs       | native iOS pickers                           | open each control |
| Sticky header, nested scrolling     | bounce and stacking differences              | scroll with a finger |
| Long text, tight flex rows          | different glyph widths change wrapping       | compare element boxes |
| `backdrop-filter`, shadows, gradients | compositing and color differences          | visual check, no strict pixel equality |
| Landscape                           | side safe areas, 327 px of height            | rotate and capture |
| Home Screen web app                 | different geometry and safe areas            | add to Home Screen and launch |

Each L2 capture records: iOS version, Safari state (toolbar expanded or
collapsed), orientation, Display Zoom, Text Size, Bold Text, color scheme,
Reduce Motion, URL, `scrollY`, keyboard state, and the probe JSON.

## Known reports

These describe specific versions, not general behavior [research]:
WebKit font/kerning differences on Ubuntu ([#22429][i22429], [#20203][i20203]);
`document.fonts.ready` hang in Playwright 1.63.0 ([#42986][i42986]);
request for iOS safe-area emulation ([#23611][i23611]); CDP-bridge screenshot
fixes in pymobiledevice3 ([#1904][i1904]).

[apple-specs]: https://support.apple.com/en-am/111873
[uyl]: https://useyourloaf.com/blog/iphone-13-screen-sizes/
[pw-devices]: https://github.com/microsoft/playwright/blob/main/packages/isomorphic/deviceDescriptorsSource.json
[pw-run]: https://github.com/microsoft/playwright/blob/main/browser_patches/webkit/pw_run.sh
[pw-browsers]: https://playwright.dev/docs/browsers
[webkit-ports]: https://docs.webkit.org/Ports/Introduction.html
[webkit-units]: https://webkit.org/blog/12445/new-webkit-features-in-safari-15-4/
[cdp-safe-area]: https://chromedevtools.github.io/devtools-protocol/tot/Emulation/#method-setSafeAreaInsetsOverride
[apple-fonts]: https://developer.apple.com/fonts/
[i22429]: https://github.com/microsoft/playwright/issues/22429
[i20203]: https://github.com/microsoft/playwright/issues/20203
[i42986]: https://github.com/microsoft/playwright/issues/42986
[i23611]: https://github.com/microsoft/playwright/issues/23611
[i1904]: https://github.com/doronz88/pymobiledevice3/issues/1904
