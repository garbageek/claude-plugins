#!/usr/bin/env python3
"""Capture a mobile page, an iPhone screen, or a set of viewport heights."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import platform
import shutil
import struct
import subprocess
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

LOGGER = logging.getLogger("iphone13mini")
PROBE_JS = Path(__file__).with_name("safari_probe.js").read_text(encoding="utf-8")
ENGINE_LABELS = {"webkit": "Playwright WebKit", "chromium": "Chromium"}


def parse_viewport(raw: str) -> dict[str, int]:
    try:
        width, height = map(int, raw.lower().split("x"))
        if min(width, height) <= 0:
            raise ValueError
        return {"width": width, "height": height}
    except ValueError:
        raise argparse.ArgumentTypeError("Expected positive WIDTHxHEIGHT") from None


def parse_safe_area(raw: str) -> dict[str, int]:
    try:
        top, right, bottom, left = map(int, raw.split(","))
        if min(top, right, bottom, left) < 0:
            raise ValueError
        return dict(zip(("top", "right", "bottom", "left"), (top, right, bottom, left)))
    except ValueError:
        raise argparse.ArgumentTypeError("Expected nonnegative TOP,RIGHT,BOTTOM,LEFT CSS px") from None


def device_options(pw, args, orientation: str) -> tuple[str, dict]:
    name = "iPhone 13 Mini" + (" landscape" if orientation == "landscape" else "")
    device = dict(pw.devices[name])
    device.pop("default_browser_type", None)
    device.setdefault("screen", {"width": 375, "height": 812} if orientation == "portrait"
                      else {"width": 812, "height": 375})
    for flag, option in (("viewport", "viewport"), ("dpr", "device_scale_factor"),
                         ("color_scheme", "color_scheme"), ("locale", "locale"),
                         ("user_agent", "user_agent"), ("storage_state", "storage_state")):
        value = getattr(args, flag, None)
        if value is not None:
            device[option] = str(value) if isinstance(value, Path) else value
    return name, device


async def launch_local(pw, engine: str, executable: str | None):
    if executable and engine != "chromium":
        raise ValueError("--executable requires --engine chromium")
    options = {"headless": True}
    if executable:
        options["executable_path"] = executable
    return await getattr(pw, engine).launch(**options)


async def apply_safe_area(context, page, engine: str, insets: dict | None):
    if insets is None:
        return None
    if engine != "chromium":
        raise ValueError("--safe-area requires --engine chromium")
    session = await context.new_cdp_session(page)
    await session.send("Emulation.setSafeAreaInsetsOverride", {"insets": insets})
    return {"insetsCssPx": insets, "source": "synthetic-cdp-override"}


async def wait_resources(page, timeout_ms: int, full_page: bool = False) -> dict:
    return await page.evaluate(r"""async ({timeout, fullPage}) => {
      const bounded = async promise => {
        let timer;
        try {
          return await Promise.race([
            promise.then(() => 'ready', () => 'error'),
            new Promise(resolve => {timer = setTimeout(() => resolve('timeout'), timeout);}),
          ]);
        } finally {clearTimeout(timer);}
      };
      const images = [...document.images].filter(img => {
        if (!(img.currentSrc || img.getAttribute('src') || img.srcset)) return false;
        const r = img.getBoundingClientRect();
        return fullPage || img.loading !== 'lazy' ||
          (r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth);
      });
      const failedImages = [];
      const [fontStatus, imageStatus] = await Promise.all([
        document.fonts ? bounded(document.fonts.ready) : Promise.resolve('unsupported'),
        bounded(Promise.all(images.map(async img => {
          try {await img.decode();}
          catch {failedImages.push(img.currentSrc || img.src || img.srcset);}
        }))),
      ]);
      const failedFonts = document.fonts ? [...document.fonts]
        .filter(font => font.status === 'error').map(font => font.family) : [];
      return {
        fonts: failedFonts.length ? 'error' : fontStatus,
        images: failedImages.length ? 'error' : imageStatus,
        imageCount: images.length, failedImages, failedFonts,
      };
    }""", {"timeout": timeout_ms, "fullPage": full_page})


def resources_ready(resources: dict) -> bool:
    return all(resources[key] in ("ready", "unsupported") for key in ("fonts", "images"))


async def warm_lazy_images(page) -> None:
    original_y = await page.evaluate("scrollY")
    height = await page.evaluate("Math.max(innerHeight, 1)")
    length = await page.evaluate("document.documentElement.scrollHeight")
    try:
        for y in range(0, min(length, height * 100), height):
            await page.evaluate("y => scrollTo(0, y)", y)
            await page.wait_for_timeout(100)
    finally:
        await page.evaluate("y => scrollTo(0, y)", original_y)


async def prepare_page(page, args, url: str | None = None) -> tuple[int | None, dict]:
    page.set_default_timeout(args.timeout_ms)
    status = None
    if url:
        response = await page.goto(url, wait_until="domcontentloaded")
        status = response.status if response else None
        if status is not None and status >= 400 and not getattr(args, "allow_http_error", False):
            raise RuntimeError(f"HTTP {status}: {page.url}")
    if getattr(args, "wait_load", False):
        await page.wait_for_load_state("load")
    if args.ready_selector:
        await page.locator(args.ready_selector).first.wait_for(state="visible")
    if args.ready_js:
        await page.wait_for_function(args.ready_js)
    if getattr(args, "full_page", False):
        await warm_lazy_images(page)
    if getattr(args, "scroll_y", None) is not None:
        await page.evaluate("y => scrollTo(0, y)", args.scroll_y)
    if args.settle_ms:
        await page.wait_for_timeout(args.settle_ms)
    resources = await wait_resources(page, args.resource_timeout_ms, getattr(args, "full_page", False))
    if not resources_ready(resources):
        if args.strict_resources:
            raise RuntimeError(f"Resources incomplete: {resources}")
        LOGGER.warning("Resources incomplete: %s", resources)
    return status, resources


def png_dimensions(path: Path) -> dict[str, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"Not a PNG: {path}")
    width, height = struct.unpack(">II", header[16:24])
    return {"width": width, "height": height}


def output_paths(args) -> tuple[Path, Path]:
    image = Path(args.output).expanduser().resolve()
    metadata = Path(args.metadata).expanduser().resolve() if args.metadata else image.with_suffix(".json")
    if image.suffix.lower() != ".png" or image == metadata:
        raise ValueError("Use a .png output and a separate metadata file")
    image.parent.mkdir(parents=True, exist_ok=True)
    metadata.parent.mkdir(parents=True, exist_ok=True)
    return image, metadata


def save_report(image: Path, metadata: Path, data: dict) -> dict:
    data.update(capturedAtUtc=datetime.now(timezone.utc).isoformat(), output=str(image),
                metadata=str(metadata), pngSize=png_dimensions(image))
    metadata.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data


async def capture_local(args) -> dict:
    from playwright.async_api import async_playwright

    image, metadata = output_paths(args)
    async with async_playwright() as pw:
        name, device = device_options(pw, args, args.orientation)
        browser = await launch_local(pw, args.engine, args.executable)
        try:
            context = await browser.new_context(**device)
            page = await context.new_page()
            safe_area = await apply_safe_area(context, page, args.engine, args.safe_area)
            status, resources = await prepare_page(page, args, args.url)
            await page.screenshot(path=str(image), type="png", full_page=args.full_page,
                                  animations="disabled", caret="hide", scale=args.scale)
            return save_report(image, metadata, {
                "source": "playwright", "engine": args.engine, "hostPlatform": platform.system(),
                "playwrightVersion": version("playwright"), "browserVersion": browser.version,
                "profile": name, "appliedContext": device, "syntheticSafeArea": safe_area,
                "requestedUrl": args.url, "finalUrl": page.url, "httpStatus": status,
                "fullPage": args.full_page, "screenshotScale": args.scale,
                "resourceStatus": resources, "probe": await page.evaluate(PROBE_JS),
            })
        finally:
            await browser.close()


async def capture_iphone(args) -> dict:
    image, metadata = output_paths(args)
    data = {"source": "pymobiledevice3-screen" if args.mode == "screen" else "cdp-page",
            "imageScope": "full-device-screen" if args.mode == "screen" else "web-content"}
    if args.mode == "page" or args.inspect:
        from playwright.async_api import async_playwright

        async with async_playwright() as pw:
            browser = await pw.chromium.connect_over_cdp(args.cdp_url, timeout=args.timeout_ms)
            try:
                pages = [p for context in browser.contexts for p in context.pages]
                matches = [p for p in pages if not args.tab_url_contains or args.tab_url_contains in p.url]
                if len(matches) != 1:
                    raise ValueError(f"Expected one matching tab; available: {[p.url for p in pages]}")
                page = matches[0]
                status, resources = await prepare_page(page, args, args.url)
                if args.mode == "page":
                    await page.screenshot(path=str(image), type="png", full_page=args.full_page,
                                          animations="disabled", caret="hide")
                data.update(cdpEndpoint=args.cdp_url, inspectedUrl=page.url, httpStatus=status,
                            browserVersion=browser.version, playwrightVersion=version("playwright"),
                            resourceStatus=resources, probe=await page.evaluate(PROBE_JS))
            finally:
                await browser.close()
    if args.mode == "screen":
        cli = shutil.which("pymobiledevice3")
        if not cli:
            raise RuntimeError("pymobiledevice3 is not installed")
        await asyncio.sleep(args.settle_ms / 1000)
        subprocess.run([cli, "developer", "core-device", "screen-capture", "screenshot", str(image)],
                       check=True, timeout=max(60, args.timeout_ms / 1000))
    return save_report(image, metadata, data)


def parse_heights(raw: str) -> list[int]:
    try:
        values = [int(value) for value in raw.split(",")]
        if not values or min(values) <= 0 or len(values) != len(set(values)):
            raise ValueError
        return values
    except ValueError:
        raise argparse.ArgumentTypeError("Expected unique positive heights separated by commas") from None


async def sweep(args) -> dict:
    from compare import compare_aligned

    reference = args.reference.expanduser().resolve()
    if not reference.is_file():
        raise ValueError(f"Reference does not exist: {reference}")
    output = args.output_dir.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for height in args.heights:
        image = output / f"{args.engine}-375x{height}-dpr3.png"
        capture_args = argparse.Namespace(**vars(args))
        capture_args.output, capture_args.metadata = image, None
        capture_args.orientation, capture_args.viewport = "portrait", {"width": 375, "height": height}
        capture_args.dpr, capture_args.scale, capture_args.full_page = 3, "device", False
        row = {"heightCssPx": height, "candidate": str(image)}
        try:
            captured = await capture_local(capture_args)
            if not resources_ready(captured["resourceStatus"]):
                raise RuntimeError("Incomplete resources; see capture metadata")
            result = compare_aligned(reference, image, output / f"compare-{height}",
                                     args.roi_top, args.roi_bottom, args.threshold, args.min_inliers, dpr=3)
            row.update(status="compared", registration=result["registration"], diff=result["diff"])
        except Exception as exc:
            row.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        results.append(row)
    path = output / "sweep-report.json"
    report = {"url": args.url, "reference": str(reference), "engine": args.engine, "results": results}
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    compared = sum(row["status"] == "compared" for row in results)
    if not compared:
        raise RuntimeError(f"No comparable captures; see {path}")
    return {"report": str(path), "compared": compared, "failed": len(results) - compared}


def add_common_capture_flags(parser) -> None:
    parser.add_argument("--ready-selector")
    parser.add_argument("--ready-js", help="JS predicate or expression for application readiness")
    parser.add_argument("--timeout-ms", type=int, default=20000)
    parser.add_argument("--resource-timeout-ms", type=int, default=8000)
    parser.add_argument("--settle-ms", type=int, default=200)
    parser.add_argument("--scroll-y", type=int, help="Explicit scroll position; otherwise retain page state")
    parser.add_argument("--wait-load", action="store_true")
    parser.add_argument("--strict-resources", action="store_true")
    parser.add_argument("--allow-http-error", action="store_true", help="Capture an HTTP error page intentionally")


def validate_common(parser, args) -> None:
    if min(args.timeout_ms, args.resource_timeout_ms) <= 0 or args.settle_ms < 0:
        parser.error("Timeouts must be positive and settle-ms nonnegative")
    if args.scroll_y is not None and args.scroll_y < 0:
        parser.error("--scroll-y must be nonnegative")
    if getattr(args, "engine", None) != "chromium" and (
        getattr(args, "safe_area", None) is not None or getattr(args, "executable", None)
    ):
        parser.error("--safe-area and --executable require --engine chromium")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    local = commands.add_parser("local", aliases=["webkit"], help="Local screenshot and browser metadata")
    iphone = commands.add_parser("iphone", help="Native screen or a page through a CDP bridge")
    views = commands.add_parser("sweep", help="Compare explicitly chosen viewport heights")
    for cmd in (local, views):
        cmd.add_argument("--url", required=True)
        cmd.add_argument("--engine", choices=("webkit", "chromium"), default="webkit")
        cmd.add_argument("--executable")
        cmd.add_argument("--safe-area", type=parse_safe_area)
        cmd.add_argument("--color-scheme", choices=("light", "dark", "no-preference"), default="light")
        cmd.add_argument("--locale")
        cmd.add_argument("--user-agent")
        cmd.add_argument("--storage-state", type=Path, help="Existing Playwright storage-state JSON")
    for cmd in (local, iphone, views):
        add_common_capture_flags(cmd)
    for cmd in (local, iphone):
        cmd.add_argument("--output", type=Path, required=True)
        cmd.add_argument("--metadata", type=Path)
        cmd.add_argument("--full-page", action="store_true")
    local.add_argument("--orientation", choices=("portrait", "landscape"), default="portrait")
    local.add_argument("--viewport", type=parse_viewport)
    local.add_argument("--dpr", type=float)
    local.add_argument("--scale", choices=("device", "css"), default="device")
    iphone.add_argument("--mode", choices=("screen", "page"), default="screen")
    iphone.add_argument("--inspect", action="store_true", help="Inspect a CDP tab alongside native capture")
    iphone.add_argument("--cdp-url", default="http://127.0.0.1:9222")
    iphone.add_argument("--tab-url-contains")
    iphone.add_argument("--url", help="Navigate the selected CDP tab")
    views.add_argument("--reference", type=Path, required=True)
    views.add_argument("--output-dir", type=Path, default=Path("out/sweep"))
    views.add_argument("--heights", type=parse_heights, required=True)
    views.add_argument("--roi-top", type=int)
    views.add_argument("--roi-bottom", type=int)
    views.add_argument("--threshold", type=int, default=16)
    views.add_argument("--min-inliers", type=int, default=10)
    args = parser.parse_args()
    validate_common(parser, args)
    if getattr(args, "dpr", None) is not None and not 0 < args.dpr <= 10:
        parser.error("--dpr must be within (0, 10]")
    if args.command == "iphone" and args.mode == "screen":
        if args.full_page:
            parser.error("--full-page requires --mode page")
        if not args.inspect and (args.url or args.tab_url_contains or args.ready_selector or args.ready_js
                                 or args.scroll_y is not None or args.wait_load or args.strict_resources):
            parser.error("Tab operations require --mode page or --inspect")
    if args.command == "sweep" and (not 0 <= args.threshold <= 255 or args.min_inliers < 4):
        parser.error("threshold must be 0..255 and min-inliers >= 4")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        if args.command == "sweep":
            result = asyncio.run(sweep(args))
        else:
            action = capture_iphone if args.command == "iphone" else capture_local
            report = asyncio.run(action(args))
            result = {key: report[key] for key in ("output", "metadata", "source", "pngSize")}
            if "engine" in report:
                result["engine"] = report["engine"]
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
