---
name: iphone13mini-ui
description: Develop, debug, troubleshoot and test web UI/UX that must work on iPhone 13 mini (375x812 pt, Safari) or similar small iPhones. Use for layout at 375 CSS px, safe areas, the Safari toolbar and dynamic viewport, on-screen keyboard and input zoom, touch targets, hover on touch, small-screen overflow, and for comparing local renders with real iPhone screenshots. Not for native iOS apps or general desktop responsive work.
compatibility: Python 3.10+ with Playwright, Pillow, numpy and opencv-python-headless. Linux WebKit needs the Playwright browser download; real-device work needs a USB-connected iPhone and pymobiledevice3 on the host.
---

# iPhone 13 mini UI

Build and verify web interfaces for iPhone 13 mini Safari with evidence whose
level is always stated. A local engine reproduces layout rules; only a real
iPhone reproduces Safari chrome, keyboard, safe areas, scrolling physics and
typography.

## Evidence levels

Label every observation, screenshot and conclusion with its level.

| Level | Source                                      | Can establish                                              | Cannot establish                                  |
| ----- | ------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------- |
| L0    | Chromium + iPhone 13 Mini profile           | Width-driven layout, overflow, DOM sizes, CSS logic        | Anything WebKit- or Safari-specific               |
| L1    | Playwright WebKit (Linux WPE headless)      | WebKit layout/CSS behavior at the profile viewport         | Safari toolbar, keyboard, iOS fonts, real `env()` |
| L2    | Real iPhone 13 mini Safari (USB, Web Inspector) | What the user sees in the measured state               | Other iOS versions, settings or states            |

- Prefer the highest level available. Never present L0/L1 output as Safari
  behavior, and never quote a pixel-difference percentage as "similarity".
- Items the audit marks `device-verify`, and the high-risk states in
  [fidelity and limits](references/fidelity-and-limits.md), stay open until L2
  evidence exists. Report them as open, not as passed.

## Setup

Resolve `SKILL_DIR` to the directory containing this loaded skill file (a shell
variable you set from the actual installed path). Run helpers with `python3 -B`
so nothing is written into the installed skill. Write outputs to a project or
temporary directory, never into `SKILL_DIR`.

```bash
python3 -m pip install -r "$SKILL_DIR/scripts/requirements.txt"
python3 -m playwright install --with-deps webkit
```

Installing packages or browsers changes the environment: do it only when the
user's request or environment allows. Then establish what is available:

1. **L1:** run any `capture.py local` command. A "Executable doesn't exist"
   error means WebKit is not installed; if the download is blocked by the
   network, say so and fall back to L0.
2. **L0:** `--engine chromium`. If Playwright's Chromium is missing, pass an
   existing Chrome/Chromium binary with `--executable`.
3. **L2:** `pymobiledevice3 usbmux list` shows a trusted device. Without one,
   real-device steps are unavailable; do not simulate them.

The page must be reachable from the browser: `http://127.0.0.1:PORT` for local
engines, the host's LAN address for the iPhone.

## Workflows

### Develop

Design to these constraints from the start (sources and caveats in the
references):

- Content width 375 CSS px in portrait. The Playwright portrait viewport is
  375x629; landscape is 712x327. The real Safari viewport height depends on
  toolbar state: measure it, do not assume it.
- `<meta name="viewport" content="width=device-width, initial-scale=1">`. Add
  `viewport-fit=cover` only together with `env(safe-area-inset-*)` padding.
- Controls: Apple HIG lists 44x44 pt as the iOS default control size and
  28x28 pt as the minimum. At DPR 3 and page zoom 1, 1 CSS px = 1 pt.
- Text inputs, textareas and selects at 16px or more (focus zoom, see
  [audit checks](references/audit-checks.md)).
- Heights that must fit the visible area: prefer `svh`/`dvh` over `100vh`.
- `:hover` effects inside `@media (hover: hover)`.
- No horizontal overflow at 375 px; long strings wrap or truncate deliberately.

### Audit and test

```bash
python3 -B "$SKILL_DIR/scripts/ui_audit.py" --url http://127.0.0.1:8000/ --screenshot-dir out/audit --json out/audit/report.json
python3 -B "$SKILL_DIR/scripts/capture.py" local --url http://127.0.0.1:8000/ --output out/portrait.png --color-scheme dark
python3 -B "$SKILL_DIR/scripts/capture.py" local --url http://127.0.0.1:8000/ --output out/landscape.png --orientation landscape
```

Add `--engine chromium [--executable PATH]` for L0. Use `--ready-selector` or
`--ready-js` for app readiness; check `httpStatus` and `resourceStatus` in the
JSON before trusting a PNG (`eagerImages: broken` lists failed images in
`brokenImages`; `--strict-resources` turns that into a failure). Every JSON
records `fidelityLevel`, `playwrightVersion` and `browserVersion`.

1. Run the audit in portrait and landscape. Its findings are advisory review
   prompts. Confirm each against the page before reporting it as a defect.
2. Accepted exceptions are cleared with `--ignore SELECTOR` or
   `--skip CHECK_ID`; record why they were accepted.
3. Look at the screenshots yourself (open the PNGs). Check first screen,
   bottom of the page, long labels, both color schemes, and states that change
   text length (dates, numbers, localized strings).
4. For interactions, drive the page with Playwright at the same profile and
   capture after each step. Touch flags do not reproduce iOS gestures.
5. Synthetic safe areas (L0 only):
   `--engine chromium --safe-area 50,0,34,0`, or `0,50,21,50` in landscape. These
   are device baseline insets, not values Safari reports in a normal tab.
   Label the result synthetic.

### Debug and troubleshoot

1. Reproduce at the lowest level that shows the symptom, then confirm the fix
   at the level where the user saw it.
2. Read the capture JSON first: `innerWidth` vs `layoutViewport.clientWidth`
   (a wider `innerWidth` means content overflows), `visualViewport`,
   `css.svh/lvh/dvh`, `css.safeArea*`, `viewportMeta`.
3. Map the symptom with the table in
   [audit checks](references/audit-checks.md#symptom-to-cause); state the
   evidence for the cause, not only the fix.
4. Symptoms that exist only on the phone (toolbar overlap, keyboard covering a
   CTA, zoom after typing, rubber-band gaps, native pickers) need L2. Say the
   fix is unverified until it is captured on the device.

### Verify on the real iPhone (L2)

Follow [real device](references/real-device.md): Web Inspector on the phone,
CDP bridge on the host, then:

```bash
pymobiledevice3 webinspector cdp --host 127.0.0.1 --port 9222
python3 -B "$SKILL_DIR/scripts/capture.py" iphone --mode page --tab-url-contains 192.168.1.10:8000 --output out/real-page.png
python3 -B "$SKILL_DIR/scripts/capture.py" iphone --mode screen --inspect --tab-url-contains 192.168.1.10:8000 --output out/real-screen.png
```

`--mode page` captures web content through the CDP bridge. `--mode screen`
captures the full screen including Safari chrome and needs Developer Mode plus
a mounted Developer Disk Image. Capture the required states (toolbar expanded
and collapsed, keyboard open, landscape) and keep the JSON probe with each PNG.

### Compare local and real captures

```bash
python3 -B "$SKILL_DIR/scripts/compare.py" align --reference out/real-screen.png --candidate out/portrait.png --output-dir out/aligned --roi-top "$ROI_TOP" --roi-bottom "$ROI_BOTTOM" --dpr 3
python3 -B "$SKILL_DIR/scripts/compare.py" raw --reference out/real-page.png --candidate out/portrait.png --output-dir out/raw
```

I set `ROI_TOP` and `ROI_BOTTOM` to measured screen-pixel boundaries for the
*supplied reference*. For a page-only screenshot without Safari chrome, I omit
the ROI flags. `align` applies only an integer shift and reports it: a shift
can itself be a layout defect. It refuses scale/rotation mismatches instead of
hiding them. `raw` needs identical geometry unless `--resize-candidate` is
passed explicitly. Compare local captures with each other only when their
`playwrightVersion` and `browserVersion` match; a different engine build is a
different renderer. Inspect `overlay.png` and `diff-3x.png`; the numbers in
`report.json` are raw RGB statistics. Details: [calibration](references/calibration.md).

## Reporting

For each finding or fix, state: what was observed, the evidence level and
artifact (PNG/JSON path), the cause with its evidence, the change made, and
what remains open for L2. Keep accepted exceptions visible. When no L2 capture
exists, end with the specific device states still to check.

## References

- [Fidelity and limits](references/fidelity-and-limits.md): device geometry,
  what each engine reproduces, high-risk states, sources.
- [Audit checks](references/audit-checks.md): rule rationale, thresholds,
  symptom-to-cause table.
- [Real device](references/real-device.md): pymobiledevice3 setup, CDP bridge,
  screenshots, HID input, capture protocol.
- [Calibration](references/calibration.md): prepare a user-supplied screenshot,
  measure its ROI, compare it with local captures, and run a viewport sweep.
