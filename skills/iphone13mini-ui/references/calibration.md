# Calibration reference

`assets/calibration/` holds one real Safari screenshot from an iPhone 13 mini
and files derived from it. It anchors comparisons and shows what a native
capture contains; it is not a measurement of Safari's viewport.

| File                                         | Content |
| -------------------------------------------- | ------- |
| `real-safari-original-display-p3.png`        | Original native screenshot, 1125x2436, 16-bit, Display P3 ICC |
| `real-safari-srgb.webp`                      | Same pixels converted to sRGB, lossless |
| `real-safari-safe-comparison-roi-srgb.webp`  | sRGB crop of the comparison ROI (y 135..2186) |
| `real-safari-annotated-srgb.webp`            | sRGB with excluded bands and landmarks drawn |
| `calibration.json`                           | Geometry, ROI, landmarks, sampled colors, unknowns |

## The frame

- Page: the Rust Pocket Mini raid calculator (`#raid`), dark theme, portrait,
  Safari with the bottom floating toolbar. State: Wooden door, quantity 1,
  method Auto.
- Status bar band: y 0..134. Safari toolbar band: y 2187..2435.
- Comparison ROI: x 0, y 135, 1125x2052 px, which is 375x684 CSS px at 3x.
  684 is the height of a screen region without browser chrome, **not** a
  measured `innerHeight`, `visualViewport.height` or `100svh`.
- Unknown from the PNG: `innerHeight`, `visualViewport`, safe-area values,
  `scrollY`, computed layout, toolbar expansion state.
- Sampled colors in `calibration.json` are screenshot samples, not CSS values.

All coordinates apply to this frame only. For another screenshot, measure the
bands and ROI again.

## Comparing against it

`compare.py align` expects a 1125x2436 reference and a candidate captured at
375 CSS px and DPR 3 (1125 px wide). It matches SIFT features inside the ROI,
estimates scale and rotation only to reject mismatches (outside 0.98..1.02 or
beyond 1 degree), applies an integer translation, and writes
`aligned-candidate.png`, `overlay.png`, `diff-3x.png`, `error-mask.png`,
`valid-mask.png` and `report.json`. A different page or state fails with too
few inliers instead of producing a misleading diff.

`capture.py sweep` captures the page at several viewport heights
(default 629, 684, 700, 728, 812) and aligns each against the reference:

```bash
python3 -B "$SKILL_DIR/scripts/capture.py" sweep --url http://127.0.0.1:8000/#raid --output-dir out/sweep
```

Files are named after the engine (`webkit-375x684-dpr3.png`,
`chromium-375x684-dpr3.png`) and every entry records its `fidelityLevel`;
`--engine chromium --safe-area T,R,B,L` adds synthetic safe areas. Pages
returning a non-2xx status are excluded. The sweep is diagnostic: it
shows which local height lines up with the screenshot, not which height Safari
reports. Confirm with the probe on the device.

`scripts/reference.py --output-dir DIR` regenerates the derived files from the
original PNG. It refuses any image that is not 1125x2436 because its bounds and
landmarks are specific to this frame.
