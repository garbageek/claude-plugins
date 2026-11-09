#!/usr/bin/env python3
"""Inspect mobile layout and CSS hints in the current top-level page DOM."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from playwright.async_api import async_playwright

from capture import (PROBE_JS, add_common_capture_flags, apply_safe_area, device_options,
                     launch_local, parse_safe_area, parse_viewport, prepare_page,
                     resources_ready, validate_common)

CHECKS = ("overflow-x", "offscreen", "touch-target", "input-zoom", "viewport-meta",
          "safe-area", "vh-units", "hover-only", "clipped-text")

AUDIT_JS = r"""opts => {
  for (const selector of opts.ignore) document.querySelector(selector);
  if (!document.body) throw new Error('The page has no HTML body');
  const styles = new Map();
  const style = el => {
    if (!styles.has(el)) styles.set(el, getComputedStyle(el));
    return styles.get(el);
  };
  const ignored = el => opts.ignore.some(selector => el.closest(selector));
  const visible = el => {
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0 || style(el).visibility !== 'visible') return false;
    for (let node = el; node; node = node.parentElement) {
      const s = style(node);
      if (s.display === 'none' || Number(s.opacity) === 0 ||
          s.contentVisibility === 'hidden' || node.inert) return false;
    }
    return true;
  };
  const describe = el => {
    let name = el.tagName.toLowerCase();
    if (el.id) name += '#' + el.id;
    else if (el.classList.length) name += '.' + [...el.classList].slice(0, 2).join('.');
    const text = (el.innerText || el.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ');
    return text ? `${name} "${text.slice(0, 50)}"` : name;
  };
  const box = el => {
    const r = el.getBoundingClientRect();
    return {x: Math.round(r.x), y: Math.round(r.y), width: Math.round(r.width), height: Math.round(r.height)};
  };
  const findings = [];
  const add = (check, severity, el, message, extra = {}) => {
    if (!opts.skip.includes(check)) findings.push({check, severity,
      target: el ? describe(el) : null, box: el ? box(el) : null, message, ...extra});
  };
  const elements = [...document.body.querySelectorAll('*')].filter(visible);
  const width = document.documentElement.clientWidth;
  const docWidth = document.documentElement.scrollWidth;
  // Clip against the actual ancestor box, not merely the presence of overflow CSS.
  const horizontalBox = el => {
    const r = el.getBoundingClientRect();
    let left = r.left, right = r.right;
    if (style(el).position !== 'fixed') {
      for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
        if (style(p).overflowX !== 'visible') {
          const parent = p.getBoundingClientRect();
          left = Math.max(left, parent.left);
          right = Math.min(right, parent.right);
        }
      }
    }
    return {left, right};
  };
  const culprits = [], excluded = [];
  for (const el of elements) {
    const r = horizontalBox(el);
    if (r.right <= r.left || (r.left >= -1 && r.right <= width + 1)) continue;
    const item = {target: describe(el), box: box(el)};
    (ignored(el) ? excluded : culprits).push(item);
    const partlyVisible = r.left < width - 1 && r.right > 1;
    if (!ignored(el) && partlyVisible && (style(el).position === 'fixed' || docWidth <= width + 1))
      add('offscreen', 'warning', el, `box crosses the ${width}px viewport horizontally`);
  }
  if (docWidth > width + 1) {
    const accepted = !culprits.length && excluded.length > 0;
    add('overflow-x', accepted ? 'accepted' : 'error', null,
      `scrollWidth ${docWidth}px > clientWidth ${width}px` +
      (accepted ? '; only ignored candidate boxes found' : ''),
      {culprits: culprits.slice(0, 15), ignoredCulprits: excluded.slice(0, 15)});
  }

  const interactive = 'a[href],button,input,select,textarea,summary,[role=button],[role=link],[role=tab],[role=switch],[role=checkbox],[tabindex]:not([tabindex="-1"])';
  for (const el of document.querySelectorAll(interactive)) {
    if (!visible(el) || ignored(el) || el.disabled) continue;
    const inlineLink = el.tagName === 'A' && style(el).display === 'inline' &&
      [...(el.parentElement?.childNodes || [])].some(n => n.nodeType === 3 && n.textContent.trim());
    if (inlineLink) continue;
    const areas = [el, ...(el.labels || [])].filter(visible).map(node => node.getBoundingClientRect());
    if (areas.some(r => r.width >= 44 && r.height >= 44)) continue;
    add('touch-target', 'info', el, 'hit-area candidate below 44×44 CSS px; inspect labels, spacing and overlap');
  }
  const nonText = new Set(['checkbox', 'radio', 'range', 'color', 'file', 'hidden', 'button', 'submit', 'reset', 'image']);
  for (const el of document.querySelectorAll('input,textarea,select')) {
    if (!visible(el) || ignored(el) || el.disabled || nonText.has(el.type)) continue;
    const size = parseFloat(style(el).fontSize);
    if (size < 16) add('input-zoom', 'info', el, `font-size ${size}px; check focus zoom on iOS`);
  }

  const meta = document.querySelector('meta[name="viewport"]')?.content || '';
  const normalized = meta.toLowerCase().replace(/\s/g, '');
  if (!meta) add('viewport-meta', 'error', null, 'missing viewport meta tag');
  else {
    if (!normalized.includes('width=device-width'))
      add('viewport-meta', 'warning', null, 'viewport does not use width=device-width');
    if (/user-scalable=(no|0)|maximum-scale=1(?:\.0)?(?:,|$)/.test(normalized))
      add('viewport-meta', 'info', null, 'viewport requests restricted zoom');
  }

  let readable = 0, unreadable = 0, envUsed = false;
  const vh = new Set(), hover = new Set();
  const inspectStyle = (declaration, target) => {
    if (declaration.cssText.includes('safe-area-inset-')) envUsed = true;
    if (['height', 'min-height', 'max-height'].some(p => /\b100vh\b/.test(declaration.getPropertyValue(p))))
      vh.add(target);
  };
  const walk = rules => {
    for (const rule of rules) {
      if (rule.type === CSSRule.MEDIA_RULE && !matchMedia(rule.conditionText).matches) continue;
      if (rule.type === CSSRule.SUPPORTS_RULE && !CSS.supports(rule.conditionText)) continue;
      if (rule.cssRules) {walk(rule.cssRules); continue;}
      if (!rule.selectorText || !rule.style) continue;
      let nodes;
      try {nodes = [...document.querySelectorAll(rule.selectorText.replace(/:hover\b/g, ''))];}
      catch {continue;}
      if (!nodes.some(el => visible(el) && !ignored(el))) continue;
      inspectStyle(rule.style, rule.selectorText);
      if (rule.selectorText.includes(':hover') && !matchMedia('(hover: hover)').matches)
        hover.add(rule.selectorText);
    }
  };
  for (const sheet of document.styleSheets) {
    try {walk(sheet.cssRules); readable++;} catch {unreadable++;}
  }
  for (const el of elements) if (!ignored(el) && el.hasAttribute('style')) inspectStyle(el.style, describe(el));
  for (const selector of [...vh].slice(0, 20))
    add('vh-units', 'info', null, `${selector}: 100vh; inspect the intended toolbar-height behavior`);
  for (const selector of [...hover].slice(0, 20))
    add('hover-only', 'info', null, `${selector}: active hover styling on a non-hover device`);
  if (normalized.includes('viewport-fit=cover') && !envUsed)
    add('safe-area', 'info', null, 'viewport-fit=cover with no safe-area use found in scanned CSS');

  const vv = window.visualViewport;
  const top = vv?.offsetTop || 0, bottom = top + (vv?.height || innerHeight);
  let clipped = 0;
  for (const el of elements) {
    if (ignored(el)) continue;
    const s = style(el), r = el.getBoundingClientRect();
    if (['fixed', 'sticky'].includes(s.position) && r.bottom > top && r.top < bottom &&
        (Math.abs(r.top - top) <= 2 || Math.abs(r.bottom - bottom) <= 2))
      add('safe-area', 'info', el, `${s.position} at a visible edge; inspect the affected phone state`);
    if (clipped < 20 && s.overflowX !== 'visible' && el.scrollWidth > el.clientWidth + 1 &&
        [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) {
      add('clipped-text', 'info', el, `text width ${el.scrollWidth}px exceeds ${el.clientWidth}px`);
      clipped++;
    }
  }
  return {findings, stylesheets: {readable, unreadable}};
}"""


def parse_orientations(raw: str) -> list[str]:
    values = [value.strip() for value in raw.split(",")]
    if not values or len(values) != len(set(values)) or any(v not in ("portrait", "landscape") for v in values):
        raise argparse.ArgumentTypeError("Use portrait, landscape, or portrait,landscape")
    return values


async def audit_state(pw, args, orientation: str) -> dict:
    name, device = device_options(pw, args, orientation)
    browser = await launch_local(pw, args.engine, args.executable)
    try:
        context = await browser.new_context(**device)
        page = await context.new_page()
        safe_area = await apply_safe_area(context, page, args.engine, args.safe_area)
        status, resources = await prepare_page(page, args, args.url)
        result = await page.evaluate(AUDIT_JS, {"ignore": args.ignore, "skip": args.skip})
        shot = None
        if args.screenshot_dir:
            args.screenshot_dir.mkdir(parents=True, exist_ok=True)
            shot = args.screenshot_dir / f"{args.engine}-{orientation}.png"
            await page.screenshot(path=str(shot), full_page=args.full_page, animations="disabled", caret="hide")
        return {
            "orientation": orientation, "profile": name, "viewport": device["viewport"],
            "browserVersion": browser.version, "httpStatus": status, "finalUrl": page.url,
            "resourceStatus": resources, "resourcesComplete": resources_ready(resources),
            "syntheticSafeArea": safe_area, "stylesheets": result["stylesheets"],
            "findings": result["findings"], "probe": await page.evaluate(PROBE_JS),
            "screenshot": str(shot) if shot else None,
        }
    finally:
        await browser.close()


async def run(args) -> dict:
    async with async_playwright() as pw:
        states = [await audit_state(pw, args, orientation) for orientation in args.orientations]
    return {
        "capturedAtUtc": datetime.now(timezone.utc).isoformat(), "url": args.url,
        "engine": args.engine, "playwrightVersion": version("playwright"),
        "ignoredSelectors": args.ignore, "skippedChecks": args.skip, "states": states,
    }


def to_markdown(report: dict) -> str:
    lines = [f"# Mobile UI scan — {report['engine']}", ""]
    for state in report["states"]:
        size = state["viewport"]
        lines += [f"## {state['orientation']} {size['width']}×{size['height']}"]
        if not state["resourcesComplete"]:
            lines.append(f"Resources incomplete: {json.dumps(state['resourceStatus'])}")
        if state["stylesheets"]["unreadable"]:
            lines.append(f"Unreadable stylesheets: {state['stylesheets']['unreadable']}")
        if not state["findings"]:
            lines.append("No findings in the scanned DOM and readable CSS.")
        for finding in state["findings"]:
            lines.append(f"- {finding['check']} [{finding['severity']}]: "
                         f"{finding['target'] or 'page'} — {finding['message']}")
            for culprit in finding.get("culprits", [])[:5]:
                lines.append(f"  {culprit['target']}: {culprit['box']}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--engine", choices=("webkit", "chromium"), default="webkit")
    parser.add_argument("--executable")
    parser.add_argument("--orientations", type=parse_orientations, default=["portrait"])
    parser.add_argument("--viewport", type=parse_viewport, help="Override for one selected orientation")
    parser.add_argument("--color-scheme", choices=("light", "dark", "no-preference"), default="light")
    parser.add_argument("--safe-area", type=parse_safe_area)
    parser.add_argument("--storage-state", type=Path)
    parser.add_argument("--ignore", action="append", default=[], help="CSS selector of an intentional exception")
    parser.add_argument("--skip", action="append", default=[], choices=CHECKS)
    parser.add_argument("--screenshot-dir", type=Path)
    parser.add_argument("--full-page", action="store_true")
    parser.add_argument("--json", type=Path, help="Write detailed results")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    add_common_capture_flags(parser)
    args = parser.parse_args()
    validate_common(parser, args)
    if args.viewport and len(args.orientations) != 1:
        parser.error("--viewport requires exactly one orientation")
    try:
        report = asyncio.run(run(args))
        text = json.dumps(report, ensure_ascii=False, indent=2)
        if args.json:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(text + "\n", encoding="utf-8")
        if args.format == "json":
            print(text)
        elif args.json:
            print(json.dumps({"report": str(args.json), "engine": args.engine,
                              "findings": sum(len(s["findings"]) for s in report["states"]),
                              "resourcesComplete": all(s["resourcesComplete"] for s in report["states"])}))
        else:
            print(to_markdown(report))
        return 0
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
