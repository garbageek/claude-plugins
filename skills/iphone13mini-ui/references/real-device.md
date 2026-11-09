# Real device (L2)

A USB-connected iPhone 13 mini running Safari is the reference for Safari UX.
The host can be Linux or macOS; no Xcode is needed. Commands below were
checked against the pymobiledevice3 documentation ([CLI recipes][recipes],
[WebView debugging][webview]) in November 2026. Re-check `--help` after
upgrading pymobiledevice3.

## One-time setup

Host (Ubuntu):

```bash
sudo apt-get install -y usbmuxd
python3 -m pip install pymobiledevice3
pymobiledevice3 usbmux list
```

Phone: connect by USB, unlock, accept "Trust This Computer". Enable Web
Inspector: iOS 18 and later, Settings > Apps > Safari > Advanced > Web
Inspector; before iOS 18, Settings > Safari > Advanced. Enable Remote
Automation next to it only for automation sessions.

Open the page by the host's LAN address (`http://192.168.1.10:8000/` is a
placeholder). On the phone, `127.0.0.1` is the phone itself.

## Capabilities and their prerequisites

| Task                              | Command                                                                     | Needs |
| --------------------------------- | --------------------------------------------------------------------------- | ----- |
| List Safari tabs                  | `pymobiledevice3 webinspector opened-tabs`                                  | Web Inspector |
| JS shell in a tab                 | `pymobiledevice3 webinspector js-shell`                                     | Web Inspector |
| Open a URL in a JS shell          | `pymobiledevice3 webinspector js-shell --open-safari URL`                   | Web Inspector |
| Automation session at a URL       | `pymobiledevice3 webinspector launch URL`                                   | Web Inspector + Remote Automation |
| CDP bridge for Playwright         | `pymobiledevice3 webinspector cdp --host 127.0.0.1 --port 9222`             | Web Inspector only (no tunnel, Developer Mode or disk image) |
| Full-screen PNG (iOS 17+)         | `pymobiledevice3 developer core-device screen-capture screenshot out.png`   | Developer Mode + `pymobiledevice3 mounter auto-mount` |
| Tap (normalized 0..65535)         | `pymobiledevice3 developer core-device universal-hid-service tap -- 32768 32768` | Developer Mode + mounted image |

The bridge serves one set of clients per inspected page; close other Web
Inspector sessions if attaching fails. Through the bridge Playwright supports
navigation, evaluation, text input, clicks, screenshots and network
observation ([WebView debugging][webview]); it is a protocol bridge, so treat
any unsupported call as a limitation, not as a page bug.

HID coordinates are normalized: `hid_x = round(px_x * 65535 / screen_width_px)`
using the size from `pymobiledevice3 developer core-device get-display-info`.

## Capture with this skill

```bash
pymobiledevice3 webinspector cdp --host 127.0.0.1 --port 9222          # keep running
python3 -B "$SKILL_DIR/scripts/capture.py" iphone --mode page --tab-url-contains 192.168.1.10:8000 --output out/real-page.png
python3 -B "$SKILL_DIR/scripts/capture.py" iphone --mode screen --inspect --tab-url-contains 192.168.1.10:8000 --output out/real-screen.png
```

- `--mode page` is a web-content PNG through the bridge plus the probe JSON.
  Viewport-sized by default; `--full-page` for the whole document.
- `--mode screen` is the native screenshot including Safari chrome. Without
  `--inspect` it needs no bridge and writes no probe.
- `--url` navigates the matched tab first; `--ready-selector`, `--ready-js`,
  `--scroll-y` and `--settle-ms` work as for local captures.
- If a page screenshot fails through the bridge, fall back to `--mode screen`
  and crop; do not mark the comparison as passed.

`scripts/safari_probe.js` measures the same viewport, unit and safe-area values
and shows a Copy JSON panel. Use it when no host is connected: paste it into
the Web Inspector console or run it from a Shortcut ("Run JavaScript on Web
Page").

## Capture protocol

1. Record device model, iOS version, Display Zoom, Text Size, Bold Text,
   color scheme and Reduce Motion.
2. Bring the app to a fixed state (data, theme, storage, fonts loaded).
3. Portrait, top of page, toolbar expanded: native PNG + probe.
4. Scroll until the toolbar collapses: native PNG + probe.
5. Focus a text input (keyboard open): PNG + probe; blur and check that
   `visualViewport.scale` returned to 1.
6. Landscape: PNG + probe.
7. Home Screen web app, only if the app is meant to be installed.
8. Keep the original PNGs untouched; crop copies for comparison.
9. Capture the local engine at the measured `innerWidth`x`innerHeight`
   (`capture.py local --viewport 375xH`) and compare
   ([calibration](calibration.md)).

A native screenshot is the reference for its own state only. Screenshot
encoding, ICC profile and the OLED panel are separate layers; compare layout
and visible defects, not absolute color.

## Without a phone

Cloud real-device services (BrowserStack, Sauce Labs and others) can stand in
for the USB phone if a real iPhone 13 mini with the needed iOS version is
actually available on the plan; confirm the model and OS before relying on it,
and note that their local tunnels change the page origin [research].

[recipes]: https://github.com/doronz88/pymobiledevice3/blob/master/docs/guides/cli-recipes.md
[webview]: https://github.com/doronz88/pymobiledevice3/blob/master/docs/guides/webview-debugging.md
