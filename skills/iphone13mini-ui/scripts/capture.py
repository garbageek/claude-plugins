#!/usr/bin/env python3
"""iPhone 13 mini captures: local engine (WebKit or Chromium), real iOS screen, and viewport sweep."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import shutil
import struct
import subprocess
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import async_playwright

LOGGER = logging.getLogger("iphone13mini")
SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_REFERENCE = SKILL_DIR / "assets" / "calibration" / "real-safari-original-display-p3.png"

PROBE_JS = r"""() => {
  const measure = (property, value) => {
    const probe = document.createElement('div');
    probe.style.cssText = 'position:absolute;visibility:hidden;pointer-events:none;' +
      'left:-100000px;top:0;width:0;box-sizing:content-box;';
    probe.style.setProperty(property, value);
    document.documentElement.appendChild(probe);
    const style = getComputedStyle(probe);
    const result = style.getPropertyValue(property);
    probe.remove();
    return result;
  };
  const vv = window.visualViewport;
  return {
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    language: navigator.language,
    screen: {width: screen.width, height: screen.height,
             availWidth: screen.availWidth, availHeight: screen.availHeight},
    devicePixelRatio,
    window: {innerWidth, innerHeight, outerWidth, outerHeight,
             scrollX, scrollY},
    layoutViewport: {
      clientWidth: document.documentElement.clientWidth,
      clientHeight: document.documentElement.clientHeight,
    },
    visualViewport: vv ? {
      width: vv.width, height: vv.height, scale: vv.scale,
      offsetTop: vv.offsetTop, offsetLeft: vv.offsetLeft,
      pageTop: vv.pageTop, pageLeft: vv.pageLeft,
    } : null,
    document: {
      scrollWidth: document.documentElement.scrollWidth,
      scrollHeight: document.documentElement.scrollHeight,
    },
    viewportMeta: document.querySelector('meta[name="viewport"]')?.content ?? null,
    displayMode: {
      standalone: matchMedia('(display-mode: standalone)').matches,
      navigatorStandalone: navigator.standalone ?? null,
    },
    media: {
      fine: matchMedia('(pointer: fine)').matches,
      coarse: matchMedia('(pointer: coarse)').matches,
      hover: matchMedia('(hover: hover)').matches,
      colorSchemeDark: matchMedia('(prefers-color-scheme: dark)').matches,
    },
    css: {
      svh: measure('height', '100svh'),
      lvh: measure('height', '100lvh'),
      dvh: measure('height', '100dvh'),
      vh: measure('height', '100vh'),
      safeAreaTop: measure('padding-top', 'env(safe-area-inset-top, 0px)'),
      safeAreaRight: measure('padding-right', 'env(safe-area-inset-right, 0px)'),
      safeAreaBottom: measure('padding-bottom', 'env(safe-area-inset-bottom, 0px)'),
      safeAreaLeft: measure('padding-left', 'env(safe-area-inset-left, 0px)'),
    },
    fonts: {status: document.fonts?.status ?? 'unsupported'},
    readyState: document.readyState,
  };
}"""


ENGINE_LABELS = {
    "webkit": "Playwright WebKit (Linux WPE headless; WebKit engine, NOT iOS Safari)",
    "chromium": "Chromium with iPhone 13 Mini emulation (Blink engine; NOT WebKit, NOT Safari)",
}
FIDELITY_LEVELS = {"webkit": "L1-linux-webkit", "chromium": "L0-blink-emulation"}


async def launch_local(pw, engine: str, executable: str | None):
    """Launch the requested local engine. Never silently substitute another engine."""
    if engine == "webkit":
        if executable:
            raise ValueError("--executable applies only to --engine chromium")
        return await pw.webkit.launch(headless=True)
    options = {"headless": True}
    if executable:
        options["executable_path"] = executable
    return await pw.chromium.launch(**options)


def parse_safe_area(raw: str) -> dict[str, int]:
    try:
        top, right, bottom, left = (int(value) for value in raw.split(","))
        if min(top, right, bottom, left) < 0:
            raise ValueError
    except ValueError:
        raise argparse.ArgumentTypeError("Expected TOP,RIGHT,BOTTOM,LEFT CSS px, e.g. 50,0,34,0") from None
    return {"top": top, "right": right, "bottom": bottom, "left": left}


async def apply_safe_area(context, page, engine: str, insets: dict[str, int] | None):
    """Chromium-only synthetic env(safe-area-inset-*) via experimental CDP; no WebKit equivalent."""
    if not insets:
        return None
    if engine != "chromium":
        raise ValueError("--safe-area needs --engine chromium (CDP Emulation.setSafeAreaInsetsOverride); "
                         "WebKit has no confirmed equivalent")
    session = await context.new_cdp_session(page)
    await session.send("Emulation.setSafeAreaInsetsOverride", {"insets": insets})
    return {"insets_css_px": insets,
            "source": "CDP Emulation.setSafeAreaInsetsOverride (experimental)",
            "note": "Synthetic stress value, not a measured Safari env() value"}


async def wait_resources(page, timeout_ms: int) -> dict[str, object]:
    """Bound font and image waits; do not mistake 'networkidle' for app readiness."""
    return await page.evaluate(
        r"""async (timeoutMs) => {
          const bounded = async (promise) => {
            let timer;
            try {
              return await Promise.race([
                Promise.resolve(promise).then(() => 'ready', e => `error: ${String(e)}`),
                new Promise(resolve => {timer = setTimeout(() => resolve('timeout'), timeoutMs);}),
              ]);
            } finally { clearTimeout(timer); }
          };
          const fonts = document.fonts?.ready ?
            await bounded(document.fonts.ready) : 'unsupported';
          const images = [...document.images].filter(img => img.loading !== 'lazy');
          const failed = new Set();
          const imagePromises = images.map(img => img.complete ? Promise.resolve() :
            new Promise(resolve => {
              img.addEventListener('load', resolve, {once: true});
              img.addEventListener('error', () => { failed.add(img); resolve(); }, {once: true});
            }));
          let eagerImages = await bounded(Promise.all(imagePromises));
          // A completed image can still be a failed load: complete === true with no
          // decoded pixels. Dimensionless SVGs can also report 0; the list lets you check.
          for (const img of images) {
            if (img.complete && img.naturalWidth === 0 && img.naturalHeight === 0 && img.currentSrc) failed.add(img);
          }
          const brokenImages = [...failed].map(img => img.currentSrc || img.src).slice(0, 20);
          if (eagerImages === 'ready' && failed.size) eagerImages = 'broken';
          return {fonts, eagerImages, eagerImageCount: images.length, brokenImageCount: failed.size, brokenImages};
        }""",
        timeout_ms,
    )


async def warm_lazy_images(page) -> None:
    """Load lazy images below the fold before making a full-page capture."""
    viewport_height = await page.evaluate("Math.max(innerHeight, 1)")
    doc_height = await page.evaluate("document.documentElement.scrollHeight")
    # Prevent pathological infinite-scroll pages from making this a limitless loop.
    max_scrolls = min(100, max(1, (doc_height + viewport_height - 1) // viewport_height))
    for index in range(max_scrolls):
        await page.evaluate("y => scrollTo(0, y)", index * viewport_height)
        await page.wait_for_timeout(100)
    await page.evaluate("scrollTo(0, 0)")
    await page.wait_for_timeout(150)


def parse_viewport(raw: str) -> dict[str, int]:
    try:
        width, height = (int(value) for value in raw.lower().split("x"))
        if width <= 0 or height <= 0:
            raise ValueError
    except (ValueError, TypeError):
        raise argparse.ArgumentTypeError("Expected positive WIDTHxHEIGHT, e.g. 375x629") from None
    return {"width": width, "height": height}


def png_dimensions(path: Path) -> dict[str, int]:
    with path.open("rb") as src:
        header = src.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"Not a PNG: {path}")
    width, height = struct.unpack(">II", header[16:24])
    return {"width": width, "height": height}


async def capture_webkit(args: argparse.Namespace) -> dict:
    output = Path(args.output).expanduser().resolve()
    metadata = Path(args.metadata).expanduser().resolve() if args.metadata else output.with_suffix(".json")
    output.parent.mkdir(parents=True, exist_ok=True)
    metadata.parent.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as pw:
        device_name = "iPhone 13 Mini" + (" landscape" if args.orientation == "landscape" else "")
        device = dict(pw.devices[device_name])
        device.pop("default_browser_type", None)  # Not a Browser.new_context option.
        # Playwright's Python descriptor does not expose the raw registry's screen.
        # Keep screen points distinct from viewport points in our diagnostics.
        device["screen"] = ({"width": 375, "height": 812} if args.orientation == "portrait"
                            else {"width": 812, "height": 375})
        if args.viewport:
            device["viewport"] = args.viewport
        if args.dpr:
            device["device_scale_factor"] = args.dpr
        device["color_scheme"] = args.color_scheme
        if args.locale:
            device["locale"] = args.locale
        if args.user_agent:
            device["user_agent"] = args.user_agent

        browser = await launch_local(pw, args.engine, args.executable)
        try:
            context = await browser.new_context(**device)
            page = await context.new_page()
            safe_area = await apply_safe_area(context, page, args.engine, args.safe_area)
            page.set_default_timeout(args.timeout_ms)
            response = await page.goto(args.url, wait_until="domcontentloaded", timeout=args.timeout_ms)
            if args.wait_load:
                await page.wait_for_load_state("load", timeout=args.timeout_ms)
            if args.ready_selector:
                await page.locator(args.ready_selector).first.wait_for(state="visible", timeout=args.timeout_ms)
            if args.ready_js:
                await page.wait_for_function(f"() => Boolean({args.ready_js})", timeout=args.timeout_ms)

            if args.full_page:
                await warm_lazy_images(page)

            resource_status = await wait_resources(page, args.resource_timeout_ms)
            if any(resource_status[key] not in ("ready", "unsupported") for key in ("fonts", "eagerImages")):
                if args.strict_resources:
                    raise RuntimeError(f"Resources not confirmed ready: {resource_status}")
                LOGGER.warning("Some resources are not confirmed ready: %s", resource_status)
            if args.scroll_y:
                await page.evaluate("y => scrollTo(0, y)", args.scroll_y)
            # Allow compositor and transition state to settle by at least two frames.
            await page.evaluate("() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
            if args.settle_ms:
                await page.wait_for_timeout(args.settle_ms)

            details = await page.evaluate(PROBE_JS)
            await page.screenshot(
                path=str(output), full_page=args.full_page,
                animations="disabled", caret="hide", scale=args.scale,
                timeout=args.timeout_ms,
            )
            report = {
                "capturedAtUtc": datetime.now(timezone.utc).isoformat(),
                "requestedUrl": args.url,
                "finalUrl": page.url,
                "httpStatus": response.status if response else None,
                "engine": args.engine,
                "browserEngine": ENGINE_LABELS[args.engine],
                "fidelityLevel": FIDELITY_LEVELS[args.engine],
                "syntheticSafeArea": safe_area,
                "playwrightVersion": version("playwright"),
                "browserVersion": browser.version,
                "profile": device_name,
                "appliedContext": device,
                "orientation": args.orientation,
                "fullPage": args.full_page,
                "screenshotScale": args.scale,
                "pngSize": png_dimensions(output),
                "resourceStatus": resource_status,
                "probe": details,
            }
            metadata.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            return report
        finally:
            await browser.close()



async def capture_iphone(args: argparse.Namespace) -> dict:
    """Native screen capture works without CDP; page capture and probes require CDP."""
    output = args.output.expanduser().resolve()
    metadata = args.metadata.expanduser().resolve() if args.metadata else output.with_suffix('.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    metadata.parent.mkdir(parents=True, exist_ok=True)

    details = None
    readiness = None
    final_url = None
    needs_cdp = args.mode == 'page' or args.inspect
    if needs_cdp:
        async with async_playwright() as pw:
            # Chromium is merely the CDP client. The page runs in real iOS Safari.
            browser = await pw.chromium.connect_over_cdp(args.cdp_url, timeout=args.timeout_ms)
            try:
                all_pages = [p for ctx in browser.contexts for p in ctx.pages]
                matches = ([p for p in all_pages if args.tab_url_contains in p.url]
                           if args.tab_url_contains else all_pages)
                if len(matches) != 1:
                    raise ValueError(f'Expected one matching Safari tab; found {[p.url for p in all_pages]}')
                page = matches[0]
                page.set_default_timeout(args.timeout_ms)
                if args.url:
                    await page.goto(args.url, wait_until='domcontentloaded', timeout=args.timeout_ms)
                if args.ready_selector:
                    await page.locator(args.ready_selector).first.wait_for(state='visible')
                if args.ready_js:
                    await page.wait_for_function(f'() => Boolean({args.ready_js})')
                if args.scroll_y:
                    await page.evaluate('y => scrollTo(0, y)', args.scroll_y)
                if args.settle_ms:
                    await page.wait_for_timeout(args.settle_ms)
                readiness = await wait_resources(page, args.resource_timeout_ms)
                details = await page.evaluate(PROBE_JS)
                final_url = page.url
                if args.mode == 'page':
                    await page.screenshot(path=str(output), full_page=args.full_page,
                                          animations='disabled', caret='hide', timeout=args.timeout_ms)
            finally:
                await browser.close()  # Disconnect the client; do not close real Safari.

    if args.mode == 'screen':
        cli = shutil.which('pymobiledevice3')
        if cli is None:
            raise RuntimeError('pymobiledevice3 missing; install the real-device optional dependency')
        subprocess.run(
            [cli, 'developer', 'core-device', 'screen-capture', 'screenshot', str(output)],
            check=True, timeout=max(60, args.timeout_ms / 1000),
        )

    data = {
        'capturedAtUtc': datetime.now(timezone.utc).isoformat(),
        'source': 'real iPhone screen via PyMobileDevice3' if args.mode == 'screen'
                  else 'real iOS Safari page via PyMobileDevice3 Web Inspector/CDP bridge',
        'imageScope': 'full-device-screen' if args.mode == 'screen' else 'web-content',
        'fidelityLevel': 'L2-real-safari',
        'cdpUsed': needs_cdp,
        'requestedUrl': args.url,
        'finalUrl': final_url,
        'pngSize': png_dimensions(output),
        'resourceStatus': readiness,
        'probe': details,
        'limitations': ('Native screenshot includes Safari chrome. An independent CDP connection '
                        'is only attempted with --inspect or --mode page.'),
    }
    metadata.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return data


def parse_heights(raw: str) -> list[int]:
    try:
        values = [int(value.strip()) for value in raw.split(',')]
    except ValueError:
        raise argparse.ArgumentTypeError('Expected comma-separated CSS pixel heights') from None
    if not values or len(values) != len(set(values)) or any(h < 100 or h > 2000 for h in values):
        raise argparse.ArgumentTypeError('Use unique CSS heights between 100 and 2000')
    return values


def sweep(args: argparse.Namespace) -> dict:
    """Reuse the capture and alignment implementations, no subprocess scripts."""
    from compare import compare_aligned

    output = args.output_dir.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for height in args.heights:
        png = output / f'{args.engine}-375x{height}-dpr3.png'
        capture_args = argparse.Namespace(
            url=args.url, output=str(png), metadata=None, orientation='portrait',
            viewport={'width': 375, 'height': height}, dpr=3, color_scheme=args.color_scheme,
            scale='device', full_page=False, ready_selector=args.ready_selector,
            ready_js=args.ready_js, scroll_y=args.scroll_y, timeout_ms=args.timeout_ms,
            resource_timeout_ms=args.resource_timeout_ms, settle_ms=args.settle_ms,
            locale=None, user_agent=None, wait_load=False, strict_resources=args.strict_resources,
            engine=args.engine, executable=args.executable, safe_area=args.safe_area,
        )
        entry = {'height_css_px': height, 'candidate_png': str(png), 'engine': args.engine,
                 'browserEngine': ENGINE_LABELS[args.engine], 'fidelityLevel': FIDELITY_LEVELS[args.engine]}
        try:
            captured = asyncio.run(capture_webkit(capture_args))
            status = captured.get('httpStatus')
            if status is not None and not 200 <= status < 300:
                entry.update(status='http_error', http_status=status,
                             details='Captured an HTTP error response, not the requested page')
            else:
                result = compare_aligned(
                    args.reference, png, output / f'compare-{height}', args.roi_top,
                    args.roi_bottom, args.threshold, args.min_inliers,
                )
                entry.update(status='compared', registration=result['registration'], diff=result['diff'])
        except Exception as exc:
            entry.update(status='failed', details=f'{type(exc).__name__}: {exc}')
        results.append(entry)
        print(f'height={height}: {entry["status"]}', flush=True)
    report = {
        'url': args.url, 'reference': str(args.reference), 'engine': args.engine,
        'browserEngine': ENGINE_LABELS[args.engine], 'fidelityLevel': FIDELITY_LEVELS[args.engine],
        'syntheticSafeArea': args.safe_area, 'results': results,
        'caveat': 'Viewport sweep is diagnostic; Safari DOM viewport height cannot be inferred from a screen crop. '
                  'Raw RGB errors are not perceptual fidelity scores.',
    }
    (output / 'sweep-report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    if not any(row['status'] == 'compared' for row in results):
        raise RuntimeError(f'No comparable captures. Check site access, state, geometry and the {args.engine} installation')
    return report


def add_common_capture_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--ready-selector', help='Selector of a visible ready element')
    parser.add_argument('--ready-js', help='Truthy JS expression indicating application readiness')
    parser.add_argument('--timeout-ms', type=int, default=20000)
    parser.add_argument('--resource-timeout-ms', type=int, default=8000)
    parser.add_argument('--settle-ms', type=int, default=200)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)

    webkit = commands.add_parser('local', aliases=['webkit'],
                                 help='Local headless screenshot + JSON (WebKit by default, Chromium on request)')
    webkit.add_argument('--engine', choices=('webkit', 'chromium'), default='webkit')
    webkit.add_argument('--executable', help='Chromium/Chrome binary for --engine chromium')
    webkit.add_argument('--safe-area', type=parse_safe_area,
                        help='Chromium only: synthetic env(safe-area-inset-*) TOP,RIGHT,BOTTOM,LEFT')
    webkit.add_argument('--url', required=True)
    webkit.add_argument('--output', type=Path, required=True)
    webkit.add_argument('--metadata', type=Path)
    webkit.add_argument('--orientation', choices=('portrait', 'landscape'), default='portrait')
    webkit.add_argument('--viewport', type=parse_viewport, help='Override viewport WIDTHxHEIGHT in CSS px')
    webkit.add_argument('--dpr', type=float)
    webkit.add_argument('--color-scheme', choices=('light', 'dark', 'no-preference'), default='light')
    webkit.add_argument('--scale', choices=('device', 'css'), default='device')
    webkit.add_argument('--full-page', action='store_true')
    webkit.add_argument('--scroll-y', type=int, default=0)
    webkit.add_argument('--locale')
    webkit.add_argument('--user-agent')
    webkit.add_argument('--wait-load', action='store_true', help='Additionally wait for full window load event')
    webkit.add_argument('--strict-resources', action='store_true', help='Fail if fonts/images are not ready')
    add_common_capture_flags(webkit)

    iphone = commands.add_parser('iphone', help='Native iPhone screen; optional Safari CDP metadata')
    iphone.add_argument('--output', type=Path, required=True)
    iphone.add_argument('--metadata', type=Path)
    iphone.add_argument('--mode', choices=('screen', 'page'), default='screen')
    iphone.add_argument('--inspect', action='store_true', help='Enable optional Safari CDP inspection for screen mode')
    iphone.add_argument('--cdp-url', default='http://127.0.0.1:9222')
    iphone.add_argument('--tab-url-contains')
    iphone.add_argument('--url', help='Navigate Safari tab; requires CDP (page mode or --inspect)')
    iphone.add_argument('--full-page', action='store_true', help='Only for CDP page mode')
    iphone.add_argument('--scroll-y', type=int, default=0)
    add_common_capture_flags(iphone)

    views = commands.add_parser('sweep', help='Capture candidate heights and align with iPhone reference')
    views.add_argument('--url', required=True)
    views.add_argument('--reference', type=Path, default=DEFAULT_REFERENCE)
    views.add_argument('--output-dir', type=Path, default=Path('out/sweep'))
    views.add_argument('--heights', type=parse_heights, default=parse_heights('629,684,700,728,812'))
    views.add_argument('--engine', choices=('webkit', 'chromium'), default='webkit')
    views.add_argument('--executable', help='Chromium/Chrome binary for --engine chromium')
    views.add_argument('--safe-area', type=parse_safe_area,
                       help='Chromium only: synthetic env(safe-area-inset-*) TOP,RIGHT,BOTTOM,LEFT')
    views.add_argument('--color-scheme', choices=('light', 'dark', 'no-preference'), default='dark')
    views.add_argument('--scroll-y', type=int, default=0)
    views.add_argument('--strict-resources', action='store_true')
    views.add_argument('--roi-top', type=int, default=135)
    views.add_argument('--roi-bottom', type=int, default=2187)
    views.add_argument('--threshold', type=int, default=16)
    views.add_argument('--min-inliers', type=int, default=10)
    add_common_capture_flags(views)

    args = parser.parse_args()
    if args.command == 'webkit':
        args.command = 'local'
    if args.timeout_ms <= 0 or args.resource_timeout_ms <= 0 or args.settle_ms < 0:
        parser.error('Timeouts must be positive and settle-ms nonnegative')
    if args.command != 'iphone' and args.scroll_y < 0:
        parser.error('--scroll-y must be >= 0')
    if args.command in ('local', 'sweep') and args.safe_area and args.engine != 'chromium':
        parser.error('--safe-area needs --engine chromium; WebKit has no confirmed env() override')
    if args.command == 'local' and args.dpr is not None and not 0 < args.dpr <= 10:
        parser.error('--dpr must be within (0, 10]')
    if args.command == 'iphone':
        if args.mode == 'screen' and args.full_page:
            parser.error('--full-page is only valid with --mode page')
        if args.mode == 'screen' and not args.inspect and any(
            (args.url, args.ready_selector, args.ready_js, args.tab_url_contains, args.scroll_y)
        ):
            parser.error('Use --inspect for Safari tab navigation, readiness, scroll or filtering')
        if args.scroll_y < 0:
            parser.error('--scroll-y must be >= 0')
    if args.command == 'sweep' and (not 0 <= args.threshold <= 255 or args.min_inliers < 4):
        parser.error('threshold must be 0..255 and min-inliers >= 4')

    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    try:
        if args.command == 'local':
            report = asyncio.run(capture_webkit(args))
        elif args.command == 'iphone':
            report = asyncio.run(capture_iphone(args))
        else:
            report = sweep(args)
        print(json.dumps(report if args.command != 'sweep' else {
            'report': str(args.output_dir / 'sweep-report.json'),
            'compared': sum(r['status'] == 'compared' for r in report['results']),
        }, ensure_ascii=False, indent=2))
        return 0
    except (PlaywrightError, OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
