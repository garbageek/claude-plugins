#!/usr/bin/env python3
"""Regenerate lossless sRGB WebP references from the original 16-bit Display P3 PNG."""

from __future__ import annotations

import argparse
import io
import json
import shutil
from pathlib import Path

from PIL import Image, ImageCms, ImageDraw, ImageFont

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = SKILL_DIR / 'assets' / 'calibration' / 'real-safari-original-display-p3.png'
TOP, BOTTOM = 135, 2187
ANCHORS = {
    'target_card': [57, 440, 1011, 366],
    'selected_auto_method': [54, 947, 189, 160],
    'sulfur_summary_card': [54, 1131, 1017, 525],
    'save_plan_button': [622, 1794, 449, 144],
}
SAMPLES = {
    'page_background': [5, 450],
    'target_card_background': [200, 700],
    'selected_method_orange': [150, 1020],
    'summary_card_background': [700, 1390],
    'save_button_orange': [650, 1850],
    'safari_address_bar': [550, 2230],
}


def hexpix(rgb: tuple[int, int, int]) -> str:
    return '#' + ''.join(f'{value:02X}' for value in rgb[:3])


def generate(args: argparse.Namespace) -> None:
    source_path = args.reference.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    dest_source = output_dir / 'real-safari-original-display-p3.png'
    if source_path != dest_source:
        shutil.copy2(source_path, dest_source)

    with Image.open(source_path) as source:
        if source.size != (1125, 2436):
            raise SystemExit(f'ERROR: expected 1125x2436, got {source.size}. These bounds belong to one '
                             'specific screenshot; measure new bounds for a different frame')
        original = source.convert('RGB')
        exif = source.getexif()
        timestamp = exif.get(36867) or exif.get(306)
        icc_data = source.info.get('icc_profile')
        if icc_data:
            profile = ImageCms.ImageCmsProfile(io.BytesIO(icc_data))
            source_icc = ImageCms.getProfileName(profile).strip()
            normalized = ImageCms.profileToProfile(original, profile, ImageCms.createProfile('sRGB'),
                                                   outputMode='RGB')
        else:
            source_icc = 'untagged; sRGB assumed'
            normalized = original.copy()

    srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    normalized.save(output_dir / 'real-safari-srgb.webp', format='WEBP', lossless=True,
                    quality=100, method=6, icc_profile=srgb)
    normalized.crop((0, TOP, 1125, BOTTOM)).save(
        output_dir / 'real-safari-safe-comparison-roi-srgb.webp', format='WEBP',
        lossless=True, quality=100, method=6, icc_profile=srgb
    )

    overlay = normalized.convert('RGBA')
    annotation = Image.new('RGBA', overlay.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(annotation)
    draw.rectangle((0, 0, 1124, TOP-1), fill=(235, 85, 80, 90))
    draw.rectangle((0, BOTTOM, 1124, 2435), fill=(235, 85, 80, 90))
    draw.line((0, TOP, 1124, TOP), fill=(70, 207, 240, 255), width=5)
    draw.line((0, BOTTOM, 1124, BOTTOM), fill=(70, 207, 240, 255), width=5)
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 27)
    except OSError:
        font = ImageFont.load_default()
    for name, (x, y, w, h) in ANCHORS.items():
        draw.rectangle((x, y, x+w, y+h), outline=(70, 207, 240, 255), width=5)
        label = name.replace('_', ' ')
        bounds = draw.textbbox((x+8, y+10), label, font=font)
        draw.rectangle((bounds[0]-8, bounds[1]-5, bounds[2]+8, bounds[3]+5), fill=(10, 24, 28, 225))
        draw.text((x+8, y+10), label, font=font, fill=(255, 255, 255, 255))
    for text, pos in (
        ('STATUS BAR excluded', (40, 42)),
        ('Comparison ROI: screen Y=135..2186; NOT DOM viewport', (40, 142)),
        ('SAFARI TOOLBAR excluded', (40, 2372)),
    ):
        draw.text(pos, text, font=font, fill=(255,255,255,255),
                  stroke_fill=(0,0,0,255), stroke_width=2)
    Image.alpha_composite(overlay, annotation).convert('RGB').save(
        output_dir / 'real-safari-annotated-srgb.webp', format='WEBP',
        lossless=True, quality=100, method=6, icc_profile=srgb
    )

    source_bytes = source_path.read_bytes()
    palette = {
        name: {
            'screen_position_px': [x, y],
            'original_profile_sample': hexpix(original.getpixel((x, y))),
            'converted_srgb_sample': hexpix(normalized.getpixel((x, y))),
        }
        for name, (x, y) in SAMPLES.items()
    }
    profile = {
        'reference_image': dest_source.name,
        'source_png_bit_depth_per_channel': source_bytes[24],
        'source_icc': source_icc,
        'capture_timestamp_local_from_file_exif': timestamp,
        'reference_context': {
            'device': 'iPhone 13 mini (reported by user; image geometry consistent)',
            'browser': 'Safari, bottom floating toolbar',
            'url': 'https://rust-pocket-mini-ak.garbageek.chatgpt.site/#raid',
            'orientation': 'portrait', 'color_scheme': 'dark',
            'observed_state': {
                'target': 'Wooden door', 'quantity': 1, 'selected_method': 'Auto',
                'sulfur_cost': 900, 'ammo_count': 18, 'ammo_type': 'explosive 5.56',
            },
        },
        'geometry': {
            'screen_render_pixels': [1125, 2436],
            'screen_css_points': [375, 812],
            'screenshot_scale': 3,
            'physical_display_pixels_not_equal_screenshot': [1080, 2340],
            'status_bar_exclusion_y_px': [0, TOP],
            'safari_toolbar_visible_y_px_approx': [2190, 2334],
            'safari_toolbar_exclusion_y_px': [BOTTOM, 2436],
            'comparison_roi_screen_px': {'x': 0, 'y': TOP, 'width': 1125, 'height': BOTTOM-TOP},
            'comparison_roi_css_size_at_dpr3': [375, (BOTTOM-TOP)/3],
            'roi_warning': 'Browser-chrome-free SCREEN region, NOT measured DOM or visual viewport. '
                           'Do not use 684 as observed window.innerHeight.',
        },
        'sampled_palette_not_authoritative_css': palette,
        'landmarks_screen_px': {name: {'box_px': box} for name, box in ANCHORS.items()},
        'unknown_from_static_png': [
            'window.innerHeight', 'visualViewport.height', 'visualViewport.offsetTop',
            'safe-area-inset values', 'scrollY', 'computed CSS layout',
            'Safari toolbar expansion state',
        ],
        'normalization': 'Embedded ICC -> sRGB if present; otherwise assume sRGB; '
                         'converted to 8-bit per channel for pixel comparison',
        'live_site_status': 'Externally inaccessible (HTTP 401 at analysis time); no live Linux WebKit screenshot',
    }
    (output_dir / 'calibration.json').write_text(
        json.dumps(profile, indent=2, ensure_ascii=False) + '\n', encoding='utf-8'
    )
    print(json.dumps({
        'profile': str(output_dir / 'calibration.json'),
        'roi': profile['geometry']['comparison_roi_screen_px'],
        'palette': palette,
    }, indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, default=DEFAULT_INPUT)
    # Required: never write into the installed skill directory.
    parser.add_argument('--output-dir', type=Path, required=True)
    generate(parser.parse_args())


if __name__ == '__main__':
    main()
