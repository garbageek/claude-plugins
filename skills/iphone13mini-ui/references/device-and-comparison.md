# Device capture and screenshot comparison

## iPhone from Linux

I connect and trust the phone, enable Safari Web Inspector, and open the host's
LAN URL rather than `127.0.0.1`. With `pymobiledevice3` installed:

```bash
pymobiledevice3 usbmux list
pymobiledevice3 webinspector cdp --host 127.0.0.1 --port 9222
```

With the bridge running, I select the intended tab explicitly:

```bash
python3 -B "$SKILL_DIR/scripts/capture.py" iphone --mode page --tab-url-contains "$PHONE_URL" --output out/iphone/phone-page.png
```

A native screenshot uses `iphone --mode screen` and does not need the bridge.
The bundled CoreDevice command requires the device's developer services; I use
[the installed pymobiledevice3 version's setup instructions][recipes] for Developer
Mode, disk-image mounting and any required tunnel. `--inspect` adds a separate
CDP probe; inspecting a tab does not establish which app is on the screen.

I record the device/iOS version, orientation, toolbar or keyboard state and relevant
text/display settings. I run `scripts/safari_probe.js` in the page's inspector to
collect viewport, safe-area and font values without adding a visible overlay.
For toolbar or keyboard defects I capture the affected transition, not only its
final screenshot. Bridge failures remain separate from page failures.

## Compare the same state

I match route, data, theme, fonts and scroll position first. I use the image's
actual pixel dimensions, not the panel resolution. With a native screenshot,
I measure a content region excluding browser chrome; that crop is not a DOM
viewport measurement.

For equally sized content captures:

```bash
python3 -B "$SKILL_DIR/scripts/compare.py" raw --reference out/iphone/phone-page.png --candidate out/iphone/page.png --output-dir out/iphone/diff
```

I use `--reference-crop X,Y,W,H` and `--candidate-crop X,Y,W,H` for measured crops.
For an offset full-screen reference I use `align` with measured `--roi-top` and
`--roi-bottom` pixel boundaries. Alignment applies translation only; I inspect
both the reported shift and overlap. Resizing can conceal layout defects.

The tools convert embedded ICC colors to 8-bit sRGB; untagged images are assumed
sRGB. I inspect `overlay.png` and `diff-3x.png`, separating layout differences from
font rasterization and color. A pixel-error percentage is not Safari fidelity.

`reference.py --reference IMAGE --output-dir DIR` optionally prepares normalized
images, annotations and color samples; it is not needed before comparison.
`capture.py sweep --url "$URL" --reference IMAGE --heights H1,H2 --output-dir DIR`
compares explicitly chosen viewport heights. A sweep cannot recover toolbar or
keyboard behavior from a static image.

[recipes]: https://github.com/doronz88/pymobiledevice3/blob/master/docs/guides/cli-recipes.md

Bridge details: [pymobiledevice3 WebView debugging](https://github.com/doronz88/pymobiledevice3/blob/master/docs/guides/webview-debugging.md).
