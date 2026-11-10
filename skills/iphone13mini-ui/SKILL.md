---
name: iphone13mini-ui
description: "Build or fix web UI for iPhone 13 mini Safari: 375px layouts, overflow, touch controls, safe areas, toolbar or keyboard overlap, and screenshot comparison. Use for small-iPhone web UI work, not native iOS apps or general desktop styling."
---

# iPhone 13 mini UI

## Workflow

I reproduce the requested route and interaction using the project's existing dev
server and styles. I use Playwright WebKit with `iPhone 13 Mini`; when unavailable,
I use Chromium explicitly and identify it in the result. Neither runs iOS Safari.

I inspect the rendered page and DOM at 375 CSS px, then address the actual cause:
flex/grid minimum sizes, overflowing content, text wrapping, hit areas or viewport
positioning. I preserve intentional horizontal scrollers and truncation rather
than hiding overflow on the whole page.

For an implementation request, I capture the affected state before and after the
change. I check landscape, alternate themes or keyboard states when the change
can affect them. Toolbar, keyboard and iOS font behavior need the real device;
missing device access does not block local layout work.

## Local capture

I set `SKILL_DIR` to this file's directory and `URL` to the running page.

```bash
python3 -B "$SKILL_DIR/scripts/capture.py" local --url "$URL" --output out/iphone/page.png
```

I use `--ready-selector` or `--ready-js` for application readiness,
`--orientation landscape` for rotation and `--viewport WIDTHxHEIGHT` for measured
geometry. I inspect the PNG and its JSON: response status, loaded resources,
viewport and browser version. For stateful flows I reuse the project's Playwright
setup; a fresh capture context has no existing login or application storage.

For a DOM scan I run `ui_audit.py --url "$URL" --json out/iphone/audit.json`.
Its findings are leads: I confirm the affected element and interaction before
changing CSS. Other flags are in each helper's `--help`.

## Targeted references

- For setup, CSS decisions or interpreting the audit, I read
  [browser notes](references/browser-notes.md).
- For phone capture or comparing a supplied screenshot, I read
  [device and comparison](references/device-and-comparison.md).

I report the change, the environment and state actually checked, and any relevant
phone behavior still unverified. I link useful artifacts rather than repeating
capture metadata.
