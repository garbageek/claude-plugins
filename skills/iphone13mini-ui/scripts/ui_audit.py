#!/usr/bin/env python3
"""Advisory DOM audit of a page under the iPhone 13 Mini Playwright profile.

Findings are review prompts, not verdicts: each one names its evidence, its
source class, and whether only a real iPhone can settle it. Accepted
exceptions are cleared with --ignore SELECTOR (repeatable) or --skip CHECK_ID.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capture import (  # noqa: E402  (sibling helper module)
    ENGINE_LABELS,
    FIDELITY_LEVELS,
    PROBE_JS,
    apply_safe_area,
    launch_local,
    parse_safe_area,
    wait_resources,
)

CHECKS = {
    "overflow-x": "Horizontal overflow of the document at the device width",
    "offscreen": "Fixed element partly outside the visible width (does not cause scrolling)",
    "touch-target": "Interactive control smaller than Apple HIG iOS sizes (44x44 pt default, 28x28 pt minimum)",
    "input-zoom": "Text-entry control with computed font-size below 16px (iOS Safari focus zoom)",
    "viewport-meta": "Missing or risky meta viewport",
    "safe-area": "viewport-fit=cover without env(safe-area-inset-*) usage, or fixed/sticky edge elements",
    "vh-units": "100vh-style heights that ignore Safari's dynamic toolbar",
    "hover-only": ":hover rules not guarded by (hover: hover)",
    "clipped-text": "Text clipped by overflow (ellipsis or hidden)",
}

AUDIT_JS = r"""(opts) => {
  const ignore = (el) => opts.ignore.some(sel => { try { return el.closest(sel); } catch { return false; } });
  const visible = (el) => {
    const s = getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden' || Number(s.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const describe = (el) => {
    let d = el.tagName.toLowerCase();
    if (el.id) d += '#' + el.id;
    const cls = [...el.classList].slice(0, 3);
    if (cls.length) d += '.' + cls.join('.');
    const text = (el.innerText || el.value || el.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ');
    return text ? `${d} "${text.slice(0, 40)}"` : d;
  };
  const box = (el) => { const r = el.getBoundingClientRect();
    return {x: Math.round(r.x), y: Math.round(r.y + scrollY), w: Math.round(r.width), h: Math.round(r.height)}; };
  const out = [];
  const add = (check, severity, el, message, extra = {}) =>
    out.push({check, severity, target: el ? describe(el) : null, box: el ? box(el) : null, message, ...extra});
  const vw = document.documentElement.clientWidth;

  // overflow-x and offscreen
  // Mobile layout viewports grow to fit overflowing content (innerWidth can exceed the
  // device width), so compare against the layout viewport's clientWidth instead.
  const clippedByAncestor = (el) => {
    for (let p = el.parentElement; p && p !== document.body && p !== document.documentElement; p = p.parentElement) {
      if (getComputedStyle(p).overflowX !== 'visible') return true;
    }
    return false;
  };
  const crossesEdge = (r) => (r.left < vw - 1 && r.right > vw + 1) || (r.left < -1 && r.right > 1);
  const pastEdge = (r) => r.right > vw + 1 || r.left < -1;
  const overflowCulprits = [], ignoredCulprits = [];
  for (const el of document.body.querySelectorAll('*')) {
    if (!visible(el)) continue;
    const s = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    if (s.position === 'fixed') {
      // Fixed boxes do not widen the document, so they never show up as scroll overflow.
      // Report only boxes that are partly on screen; fully off-canvas panels are a pattern.
      if (crossesEdge(r) && !ignore(el) && !clippedByAncestor(el))
        add('offscreen', 'warning', el,
            `fixed element spans x ${Math.round(r.left)}..${Math.round(r.right)} px; visible width is 0..${vw} px`);
      continue;
    }
    if (!pastEdge(r) || clippedByAncestor(el)) continue;
    (ignore(el) ? ignoredCulprits : overflowCulprits).push(el);
  }
  const docWidth = document.documentElement.scrollWidth;
  if (docWidth > vw + 1) {
    const detail = `document scrollWidth ${docWidth}px > layout width ${vw}px (innerWidth ${innerWidth}px)`;
    const extra = {
      culprits: overflowCulprits.slice(0, 15).map(el => ({target: describe(el), box: box(el)})),
      ignoredCulprits: ignoredCulprits.slice(0, 15).map(el => ({target: describe(el), box: box(el)})),
    };
    if (overflowCulprits.length)
      add('overflow-x', 'error', null, detail, extra);
    else if (ignoredCulprits.length)
      add('overflow-x', 'accepted', null, `${detail}; every element past the edge is an accepted exception`, extra);
    else
      add('overflow-x', 'error', null, `${detail}; no single element found past the edge (check margins, transforms, pseudo-elements)`, extra);
  }

  // touch-target
  const interactive = 'a[href],button,input:not([type=hidden]),select,textarea,summary,[role=button],[role=link],[role=tab],[role=switch],[role=checkbox],[tabindex]:not([tabindex="-1"])';
  for (const el of document.querySelectorAll(interactive)) {
    if (ignore(el) || !visible(el) || el.disabled) continue;
    const r = el.getBoundingClientRect();
    const short = Math.min(r.width, r.height);
    if (short >= 44) continue;
    const inlineLink = el.tagName === 'A' && getComputedStyle(el).display === 'inline' &&
      [...(el.parentElement?.childNodes || [])].some(n => n.nodeType === 3 && n.textContent.trim());
    if (inlineLink) continue;   // links inside running text follow text size, not control size
    const severity = short < 28 ? 'warning' : 'info';
    add('touch-target', severity, el,
        `${Math.round(r.width)}x${Math.round(r.height)} CSS px; HIG iOS default 44x44 pt, minimum 28x28 pt`);
  }

  // input-zoom
  const textEntry = 'input:not([type=checkbox]):not([type=radio]):not([type=range]):not([type=color]):not([type=file]):not([type=hidden]):not([type=button]):not([type=submit]):not([type=reset]):not([type=image]),textarea,select';
  for (const el of document.querySelectorAll(textEntry)) {
    if (ignore(el) || !visible(el)) continue;
    const size = parseFloat(getComputedStyle(el).fontSize);
    if (size < 16) add('input-zoom', 'warning', el,
      `computed font-size ${size}px < 16px; iOS Safari is widely reported to zoom the page on focus`);
  }

  // viewport-meta
  const meta = document.querySelector('meta[name="viewport"]')?.content ?? null;
  const metaLower = (meta || '').toLowerCase().replace(/\s+/g, '');
  if (!meta) add('viewport-meta', 'error', null, 'no <meta name="viewport">; iOS lays the page out at 980px');
  else {
    if (!metaLower.includes('width=device-width')) add('viewport-meta', 'warning', null, `"${meta}" lacks width=device-width`);
    if (/user-scalable=(no|0)|maximum-scale=1(\.0)?(,|$)/.test(metaLower))
      add('viewport-meta', 'info', null, `"${meta}" restricts zoom; accessibility cost, and iOS may ignore it`);
  }

  // Stylesheet scan (same-origin only; cross-origin sheets are reported as unreadable)
  let readable = 0, unreadable = 0, envUsed = false;
  const vhRules = [], hoverRules = [];
  const walk = (rules, hoverGuarded) => {
    for (const rule of rules) {
      if (rule.cssRules && rule.conditionText !== undefined) {
        const guarded = hoverGuarded || /hover\s*:\s*hover|any-hover\s*:\s*hover/.test(rule.conditionText);
        walk(rule.cssRules, guarded);
        continue;
      }
      if (rule.cssRules) { walk(rule.cssRules, hoverGuarded); }
      const text = rule.cssText || '';
      if (text.includes('safe-area-inset')) envUsed = true;
      if (rule.selectorText) {
        if (/(^|[^-])(min-|max-)?height\s*:\s*100vh/.test(text)) vhRules.push(rule.selectorText);
        if (rule.selectorText.includes(':hover') && !hoverGuarded) hoverRules.push(rule.selectorText);
      }
    }
  };
  for (const sheet of document.styleSheets) {
    try { walk(sheet.cssRules, false); readable++; } catch { unreadable++; }
  }
  for (const el of document.querySelectorAll('[style]')) if (el.getAttribute('style').includes('safe-area-inset')) envUsed = true;

  // safe-area
  if (metaLower.includes('viewport-fit=cover') && !envUsed)
    add('safe-area', 'warning', null, 'viewport-fit=cover is set but no env(safe-area-inset-*) found in readable CSS');
  for (const el of document.body.querySelectorAll('*')) {
    if (ignore(el) || !visible(el)) continue;
    const pos = getComputedStyle(el).position;
    if (pos !== 'fixed' && pos !== 'sticky') continue;
    const r = el.getBoundingClientRect();
    const edge = r.bottom >= innerHeight - 2 ? 'bottom' : (r.top <= 2 ? 'top' : null);
    if (edge) add('safe-area', 'device-verify', el,
      `${pos} element at the ${edge} edge; check toolbar, home indicator, keyboard and safe area on a real iPhone`);
  }

  // vh-units
  for (const sel of [...new Set(vhRules)].slice(0, 20))
    add('vh-units', 'info', null, `"${sel}" uses 100vh (in Safari usually sized to the large viewport); consider svh/dvh and verify on device`);

  // hover-only
  for (const sel of [...new Set(hoverRules)].slice(0, 20))
    add('hover-only', 'info', null, `"${sel}" is not inside @media (hover: hover); hover can stick after a tap`);

  // clipped-text
  let clipped = 0;
  for (const el of document.body.querySelectorAll('*')) {
    if (clipped >= 20 || ignore(el) || !visible(el) || !el.childElementCount && !el.textContent.trim()) continue;
    const s = getComputedStyle(el);
    if (s.overflowX === 'visible' && s.textOverflow !== 'ellipsis') continue;
    if (el.scrollWidth > el.clientWidth + 1 && [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) {
      add('clipped-text', 'info', el, `text clipped: scrollWidth ${el.scrollWidth}px > clientWidth ${el.clientWidth}px`);
      clipped++;
    }
  }

  return {findings: out, stylesheets: {readable, unreadable}};
}"""

SEVERITY_ORDER = {"error": 0, "warning": 1, "device-verify": 2, "info": 3, "accepted": 4}


async def audit_state(pw, args, orientation: str) -> dict:
    device_name = "iPhone 13 Mini" + (" landscape" if orientation == "landscape" else "")
    device = dict(pw.devices[device_name])
    device.pop("default_browser_type", None)
    if args.viewport and orientation == "portrait":
        device["viewport"] = args.viewport
    device["color_scheme"] = args.color_scheme
    browser = await launch_local(pw, args.engine, args.executable)
    try:
        context = await browser.new_context(**device)
        page = await context.new_page()
        page.set_default_timeout(args.timeout_ms)
        safe_area = await apply_safe_area(context, page, args.engine, args.safe_area)
        response = await page.goto(args.url, wait_until="domcontentloaded")
        if args.ready_selector:
            await page.locator(args.ready_selector).first.wait_for(state="visible")
        if args.ready_js:
            await page.wait_for_function(f"() => Boolean({args.ready_js})")
        resources = await wait_resources(page, args.resource_timeout_ms)
        await page.evaluate("() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
        result = await page.evaluate(AUDIT_JS, {"ignore": args.ignore})
        browser_version = browser.version
        probe = await page.evaluate(PROBE_JS)
        shot = None
        if args.screenshot_dir:
            args.screenshot_dir.mkdir(parents=True, exist_ok=True)
            shot = args.screenshot_dir / f"audit-{orientation}.png"
            await page.screenshot(path=str(shot), full_page=True, animations="disabled", caret="hide")
        findings = [f for f in result["findings"] if f["check"] not in args.skip]
        findings.sort(key=lambda f: SEVERITY_ORDER.get(f["severity"], 9))
        return {
            "orientation": orientation, "profile": device_name, "browserVersion": browser_version,
            "viewport": device["viewport"], "httpStatus": response.status if response else None,
            "finalUrl": page.url, "syntheticSafeArea": safe_area, "resourceStatus": resources,
            "stylesheets": result["stylesheets"], "findings": findings,
            "probe": probe, "screenshot": str(shot) if shot else None,
        }
    finally:
        await browser.close()


def to_markdown(report: dict) -> str:
    lines = [f"# iPhone 13 mini UI audit: {report['url']}", "",
             f"- Engine: {report['browserEngine']} ({report['fidelityLevel']})",
             f"- Captured: {report['capturedAtUtc']}", "",
             "Advisory findings. `device-verify` items can only be settled on a real iPhone.", ""]
    for state in report["states"]:
        lines += [f"## {state['orientation']} {state['viewport']['width']}x{state['viewport']['height']} "
                  f"(HTTP {state['httpStatus']})", ""]
        sheets = state["stylesheets"]
        if sheets["unreadable"]:
            lines += [f"Coverage: {sheets['unreadable']} cross-origin stylesheet(s) not scanned.", ""]
        if not state["findings"]:
            lines += ["No findings within the checked rules.", ""]
            continue
        lines += ["| Severity      | Check        | Target | Detail |", "| ------------- | ------------ | ------ | ------ |"]
        for f in state["findings"]:
            target = (f.get("target") or "-").replace("|", "/")
            detail = f["message"].replace("|", "/")
            if f.get("culprits"):
                detail += "; culprits: " + ", ".join(c["target"] for c in f["culprits"][:5]).replace("|", "/")
            if f.get("ignoredCulprits"):
                detail += "; accepted: " + ", ".join(c["target"] for c in f["ignoredCulprits"][:5]).replace("|", "/")
            lines.append(f"| {f['severity']:<13} | {f['check']:<12} | {target} | {detail} |")
        lines.append("")
    return "\n".join(lines)


async def run(args) -> dict:
    async with async_playwright() as pw:
        states = []
        for orientation in args.orientations:
            states.append(await audit_state(pw, args, orientation))
    return {
        "capturedAtUtc": datetime.now(timezone.utc).isoformat(),
        "url": args.url, "engine": args.engine,
        "browserEngine": ENGINE_LABELS[args.engine], "fidelityLevel": FIDELITY_LEVELS[args.engine],
        "playwrightVersion": version("playwright"),
        "ignoredSelectors": args.ignore, "skippedChecks": sorted(args.skip),
        "checks": CHECKS, "states": states,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", required=True)
    parser.add_argument("--engine", choices=("webkit", "chromium"), default="webkit")
    parser.add_argument("--executable", help="Chromium/Chrome binary for --engine chromium")
    parser.add_argument("--orientations", default="portrait,landscape",
                        type=lambda v: [o for o in v.split(",") if o in ("portrait", "landscape")] or ["portrait"])
    parser.add_argument("--viewport", type=lambda v: dict(zip(("width", "height"), map(int, v.lower().split("x")))),
                        help="Portrait viewport override WIDTHxHEIGHT (e.g. a height measured on the device)")
    parser.add_argument("--color-scheme", choices=("light", "dark", "no-preference"), default="dark")
    parser.add_argument("--safe-area", type=parse_safe_area, help="Chromium only: synthetic TOP,RIGHT,BOTTOM,LEFT")
    parser.add_argument("--ignore", action="append", default=[], help="CSS selector of an accepted exception")
    parser.add_argument("--skip", action="append", default=[], choices=sorted(CHECKS), help="Check id to skip")
    parser.add_argument("--ready-selector")
    parser.add_argument("--ready-js")
    parser.add_argument("--timeout-ms", type=int, default=20000)
    parser.add_argument("--resource-timeout-ms", type=int, default=8000)
    parser.add_argument("--screenshot-dir", type=Path, help="Write full-page PNGs per orientation here")
    parser.add_argument("--json", type=Path, help="Write the full JSON report here")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()
    args.skip = set(args.skip)
    if args.safe_area and args.engine != "chromium":
        parser.error("--safe-area needs --engine chromium; WebKit has no confirmed env() override")
    try:
        report = asyncio.run(run(args))
    except (PlaywrightError, OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")
    print(text if args.format == "json" else to_markdown(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
