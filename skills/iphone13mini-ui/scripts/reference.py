#!/usr/bin/env python3
"""Prepare sRGB comparison images and optional ROI/landmarks from a supplied screenshot."""

from __future__ import annotations

import argparse
import io
import json
import shutil
from pathlib import Path

from PIL import Image, ImageCms, ImageDraw, ImageFont

from compare import SRGB, normalize_image

SKILL_DIR = Path(__file__).resolve().parent.parent


def named_rectangle(raw: str) -> tuple[str, tuple[int, int, int, int]]:
    try:
        name, coords = raw.split("=", 1)
        x, y, width, height = (int(value) for value in coords.split(","))
        if not name.strip() or min(x, y) < 0 or min(width, height) <= 0:
            raise ValueError
        return name.strip(), (x, y, width, height)
    except ValueError:
        raise argparse.ArgumentTypeError("Expected NAME=X,Y,WIDTH,HEIGHT") from None


def named_point(raw: str) -> tuple[str, tuple[int, int]]:
    try:
        name, coords = raw.split("=", 1)
        x, y = (int(value) for value in coords.split(","))
        if not name.strip() or min(x, y) < 0:
            raise ValueError
        return name.strip(), (x, y)
    except ValueError:
        raise argparse.ArgumentTypeError("Expected NAME=X,Y") from None


def hexpix(rgb: tuple[int, ...]) -> str:
    return "#" + "".join(f"{value:02X}" for value in rgb[:3])


def write_webp(image: Image.Image, path: Path, srgb: bytes) -> None:
    image.save(path, format="WEBP", lossless=True, quality=100, method=6, icc_profile=srgb)


def generate(args: argparse.Namespace) -> dict:
    source_path = args.reference.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    if not source_path.is_file():
        raise ValueError(f"Reference does not exist: {source_path}")
    if output_dir == SKILL_DIR or SKILL_DIR in output_dir.parents:
        raise ValueError("Output directory must be outside the installed skill")
    with Image.open(source_path) as source:
        width, height = source.size
        image_format = source.format
        original = source.convert("RGB")  # sRGB comparison is explicitly 8-bit per channel.
        icc_data = source.info.get("icc_profile")
        normalized = normalize_image(source)
        source_icc = (ImageCms.getProfileName(ImageCms.ImageCmsProfile(io.BytesIO(icc_data))).strip()
                      if icc_data else "untagged (sRGB assumed)")

    top = 0 if args.roi_top is None else args.roi_top
    bottom = height if args.roi_bottom is None else args.roi_bottom
    if not 0 <= top < bottom <= height:
        raise ValueError(f"ROI must satisfy 0 <= top < bottom <= image height ({height})")
    has_explicit_roi = args.roi_top is not None or args.roi_bottom is not None
    for entries in (args.anchor, args.sample):
        if len({name for name, _ in entries}) != len(entries):
            raise ValueError("Anchor and sample names must be unique within each group")
    for name, (x, y, w, h) in args.anchor:
        if x + w > width or y + h > height:
            raise ValueError(f"Anchor '{name}' is outside {width}x{height}")
    for name, (x, y) in args.sample:
        if x >= width or y >= height:
            raise ValueError(f"Sample '{name}' is outside {width}x{height}")

    reserved = {output_dir / name for name in (
        "reference-srgb.webp", "reference-roi-srgb.webp", "reference-annotated-srgb.webp")}
    if source_path in reserved:
        raise ValueError("Choose a different output directory to preserve the supplied source")
    output_dir.mkdir(parents=True, exist_ok=True)
    dest_source = output_dir / f"reference-original{source_path.suffix.lower()}"
    if source_path != dest_source:
        shutil.copy2(source_path, dest_source)
    srgb = SRGB
    derived_images = ["reference-srgb.webp"]
    write_webp(normalized, output_dir / derived_images[0], srgb)
    if has_explicit_roi:
        derived_images.append("reference-roi-srgb.webp")
        write_webp(normalized.crop((0, top, width, bottom)), output_dir / derived_images[-1], srgb)

    if has_explicit_roi or args.anchor:
        overlay = normalized.convert("RGBA")
        annotation = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(annotation)
        if has_explicit_roi:
            if top > 0:
                draw.rectangle((0, 0, width - 1, top - 1), fill=(235, 85, 80, 90))
            if bottom < height:
                draw.rectangle((0, bottom, width - 1, height - 1), fill=(235, 85, 80, 90))
            draw.line((0, top, width - 1, top), fill=(70, 207, 240, 255), width=3)
            draw.line((0, bottom - 1, width - 1, bottom - 1), fill=(70, 207, 240, 255), width=3)
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", max(12, min(27, width // 40)))
        except OSError:
            font = ImageFont.load_default()
        for name, (x, y, w, h) in args.anchor:
            draw.rectangle((x, y, x + w - 1, y + h - 1), outline=(70, 207, 240, 255), width=3)
            label_y = max(0, y - 28)
            draw.text((x + 4, label_y), name, font=font, fill=(255, 255, 255, 255),
                      stroke_fill=(0, 0, 0, 255), stroke_width=2)
        derived_images.append("reference-annotated-srgb.webp")
        write_webp(Image.alpha_composite(overlay, annotation).convert("RGB"),
                   output_dir / derived_images[-1], srgb)

    png_bit_depth = None
    if image_format == "PNG":
        with source_path.open("rb") as stream:
            header = stream.read(25)
        if header.startswith(b"\x89PNG\r\n\x1a\n") and len(header) >= 25:
            png_bit_depth = header[24]

    palette = {
        name: {"screen_position_px": [x, y],
               "original_profile_sample": hexpix(original.getpixel((x, y))),
               "converted_srgb_sample": hexpix(normalized.getpixel((x, y)))}
        for name, (x, y) in args.sample
    }
    profile = {
        "reference_image": dest_source.name,
        "source_format": image_format,
        "source_png_bit_depth_per_channel": png_bit_depth,
        "source_icc": source_icc,
        "reference_context": {"device": args.device, "url": args.url},
        "geometry": {
            "image_size_px": [width, height],
            "dpr_supplied_by_user": args.dpr,
            "comparison_roi_screen_px": {"x": 0, "y": top, "width": width, "height": bottom - top},
            "roi_user_supplied": has_explicit_roi,
        },
        "landmarks_screen_px": {name: {"box_px": list(box)} for name, box in args.anchor},
        "sampled_palette_not_authoritative_css": palette,
        "colorSpace": "8-bit sRGB; alpha on white; source copied unchanged",
    }
    path = output_dir / "calibration.json"
    path.write_text(json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"profile": str(path), "roi": profile["geometry"]["comparison_roi_screen_px"],
            "derived_images": sorted(derived_images)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True, help="Source screenshot")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--roi-top", type=int, help="Measured top edge in source image pixels")
    parser.add_argument("--roi-bottom", type=int, help="Measured exclusive bottom edge in source image pixels")
    parser.add_argument("--anchor", type=named_rectangle, action="append", default=[],
                        help="Optional named reference landmark NAME=X,Y,WIDTH,HEIGHT; repeatable")
    parser.add_argument("--sample", type=named_point, action="append", default=[],
                        help="Optional named color sample NAME=X,Y; repeatable")
    parser.add_argument("--device", help="Device description supplied by the operator")
    parser.add_argument("--url", help="URL/state supplied by the operator")
    parser.add_argument("--dpr", type=float, help="Measured/known DPR, not inferred from the PNG")
    args = parser.parse_args()
    if args.dpr is not None and not 0 < args.dpr <= 10:
        parser.error("--dpr must be within (0, 10]")
    try:
        print(json.dumps(generate(args), ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
