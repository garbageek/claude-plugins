# Calibrating against a real iPhone screenshot

The skill contains **no built-in screenshot or site-specific calibration**.
I obtain a reference from the actual page and state I am inspecting and keep
its images, JSON and comparison results in that project's output directory.

## What can be calibrated

- A native screenshot covers the entire device screen, including system status
  indicators and Safari controls. A Web Inspector page capture may include only
  page content. I record which capture type produced each reference.
- iPhone 13 mini is commonly reported as a 375x812-point logical screen with a
  nominal DPR of 3. Screenshot pixel dimensions can differ from physical panel
  pixels. I read the image's actual pixel dimensions rather than assuming either.
- I measure the **screen-pixel coordinates** of any visible system bands and
  select an interior page-content region (ROI). These boundaries belong to this
  screenshot and state only: toolbar movement, orientation, OS and capture mode
  can change them. I do not infer `innerHeight`, `100dvh` or safe-area values
  from the height of a screenshot crop.
- I use `safari_probe.js` or CDP inspection to record the real `innerHeight`,
  `visualViewport`, DPR and CSS safe-area values. Those are separate observations.
- I preserve the native source file unchanged. When the source has an ICC profile,
  I convert its color values to sRGB for comparisons; otherwise I explicitly
  assume sRGB. Derived WebP images are lossless **at 8-bit sRGB precision**; any
  higher-bit-depth original is retained independently.

## Prepare a project-specific reference

I store the phone screenshot at `out/real-screen.png`. When it includes Safari
chrome, I first determine `ROI_TOP` and `ROI_BOTTOM` from that **specific image**
(the bottom boundary is exclusive), in source-image pixels, then run:

```bash
python3 -B "$SKILL_DIR/scripts/reference.py" --reference out/real-screen.png --output-dir out/reference --roi-top "$ROI_TOP" --roi-bottom "$ROI_BOTTOM" --dpr 3
```

For a page-only capture without system chrome, I omit the ROI flags. The default
ROI is the entire image. When useful, I provide named landmarks with repeated
`--anchor NAME=X,Y,WIDTH,HEIGHT`, and color samples with `--sample NAME=X,Y`.
I can also supply `--device TEXT` and `--url TEXT` as operator-provided metadata;
neither is inferred by looking at a screenshot.

Generated files are `reference-original.<source-extension>` (a byte-for-byte
copy), `reference-srgb.webp`, an optional `reference-roi-srgb.webp`, an optional
`reference-annotated-srgb.webp`, and `calibration.json`. The JSON records exact
image geometry, chosen ROI, optional landmarks/color samples, ICC information
and which measurements remain unknown from a static image.

## Compare and investigate

I capture the corresponding local page state using `capture.py local`, then align
using the actual phone screenshot and its measured ROI:

```bash
python3 -B "$SKILL_DIR/scripts/compare.py" align --reference out/real-screen.png --candidate out/local.png --output-dir out/aligned --roi-top "$ROI_TOP" --roi-bottom "$ROI_BOTTOM" --dpr 3
python3 -B "$SKILL_DIR/scripts/compare.py" raw --reference out/reference/reference-roi-srgb.webp --candidate out/local.png --output-dir out/raw
```

The `raw` example requires **identical image dimensions and content geometry**;
I crop the local page with `--candidate-crop X,Y,WIDTH,HEIGHT` if necessary. I
never use automatic resizing to hide a layout difference. `align` uses
SIFT/RANSAC to estimate correspondence, rejects scale/rotation mismatches and
applies an *integer translation only*. It reports the shift separately because
an observed shift may itself be a layout defect.

The reference ROI defaults to the whole image if I omit `--roi-top` and
`--roi-bottom`. For native full-screen captures I explicitly exclude Safari
chrome rather than relying on any built-in coordinates. `overlay.png`,
`diff-3x.png`, `error-mask.png` and `report.json` report raw RGB differences,
**not** a numerical Safari-fidelity score.

## Investigate candidate viewport heights

I pass the actual reference explicitly; no screenshot is bundled or silently
selected by `capture.py sweep`:

```bash
python3 -B "$SKILL_DIR/scripts/capture.py" sweep --url http://127.0.0.1:8000/ --reference out/real-screen.png --output-dir out/sweep --roi-top "$ROI_TOP" --roi-bottom "$ROI_BOTTOM"
```

I can provide `--heights H1,H2,H3` using measured values from the real Safari
probe. The sweep uses a 375 CSS-pixel-wide, DPR 3 capture for each candidate
height; it is diagnostic only. A best-aligned candidate height is **not** a
measurement of real Safari's viewport height. The capture JSON records its
engine and evidence level, and missing/failed page loads are not accepted as
valid comparisons.
