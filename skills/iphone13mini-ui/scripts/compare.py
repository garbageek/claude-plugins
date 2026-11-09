#!/usr/bin/env python3
"""Compare iPhone Safari and Linux WebKit PNGs: strict raw diff or landmark alignment."""

from __future__ import annotations

import argparse
import io
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageCms, ImageEnhance, ImageStat

def crop_spec(value: str) -> tuple[int, int, int, int]:
    try:
        x, y, width, height = map(int, value.split(","))
        if min(x, y) < 0 or min(width, height) <= 0:
            raise ValueError
        return x, y, width, height
    except ValueError:
        raise argparse.ArgumentTypeError("Expected nonnegative X,Y and positive WIDTH,HEIGHT") from None


def load_image(path: Path, crop: tuple[int, int, int, int] | None) -> Image.Image:
    with Image.open(path) as source:
        if "icc_profile" in source.info:
            src_profile = ImageCms.ImageCmsProfile(io.BytesIO(source.info["icc_profile"]))
            image = ImageCms.profileToProfile(source.convert("RGB"), src_profile,
                                              ImageCms.createProfile("sRGB"), outputMode="RGB")
        else:
            image = source.convert("RGB")  # untagged source: assume sRGB
        if crop:
            x, y, width, height = crop
            if x + width > image.width or y + height > image.height:
                raise ValueError(f"Crop outside {path} ({image.width}x{image.height})")
            image = image.crop((x, y, x + width, y + height))
        return image


DEFAULT_TOP = 135
DEFAULT_BOTTOM = 2187
TARGET_WIDTH = 1125
TARGET_HEIGHT = 2436


def report_path(directory: Path, name: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    return directory / name


def compare_aligned(reference_path: Path, candidate_path: Path, output_dir: Path,
               top: int, bottom: int, threshold: int, min_inliers: int) -> dict:
    import cv2
    import numpy as np

    real = np.asarray(load_image(reference_path, None))
    candidate = np.asarray(load_image(candidate_path, None))
    h, w = real.shape[:2]
    hc, wc = candidate.shape[:2]
    if w != TARGET_WIDTH or h != TARGET_HEIGHT:
        raise ValueError(f"Reference geometry {w}x{h}: expected {TARGET_WIDTH}x{TARGET_HEIGHT}; adjust calibration source")
    if wc != w:
        raise ValueError(f"Candidate width {wc}px != reference {w}px; capture at 375 CSS px and DPR 3 (do NOT resize)")
    if not 0 <= top < bottom <= h:
        raise ValueError("Comparison ROI must satisfy 0 <= top < bottom <= screenshot height")

    reference_gray = cv2.cvtColor(real, cv2.COLOR_RGB2GRAY)
    actual_gray = cv2.cvtColor(candidate, cv2.COLOR_RGB2GRAY)
    roi = np.zeros((h, w), dtype=np.uint8)
    roi[top:bottom] = 255
    detector = cv2.SIFT_create(nfeatures=4000, contrastThreshold=0.015)
    reference_keypoints, ref_descriptors = detector.detectAndCompute(reference_gray, roi)
    candidate_keypoints, actual_descriptors = detector.detectAndCompute(actual_gray, None)
    if ref_descriptors is None or actual_descriptors is None:
        raise ValueError("Not enough distinct image details to align captures; use equivalent page state")

    matches = cv2.BFMatcher(cv2.NORM_L2).knnMatch(actual_descriptors, ref_descriptors, k=2)
    good = [pair[0] for pair in matches if len(pair) == 2 and pair[0].distance < 0.74 * pair[1].distance]
    if len(good) < min_inliers:
        raise ValueError(f"Only {len(good)} reliable feature matches; need {min_inliers}. "
                         "Check URL, target, selected method, quantity, viewport and scroll position")

    actual_points = np.float32([candidate_keypoints[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    reference_points = np.float32([reference_keypoints[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    estimated, inlier_mask = cv2.estimateAffinePartial2D(
        actual_points, reference_points, method=cv2.RANSAC,
        ransacReprojThreshold=5.0, maxIters=10000, confidence=0.995, refineIters=20
    )
    if estimated is None or inlier_mask is None:
        raise ValueError("Could not establish a reliable alignment; wrong page state or insufficient shared content")
    inliers = inlier_mask.ravel().astype(bool)
    count = int(inliers.sum())
    if count < min_inliers:
        raise ValueError(f"Only {count} inliers among {len(good)} matches; need {min_inliers}")

    scale = float(math.hypot(estimated[0, 0], estimated[1, 0]))
    angle = float(math.degrees(math.atan2(estimated[1, 0], estimated[0, 0])))
    tx, ty = float(estimated[0, 2]), float(estimated[1, 2])
    if not (0.98 <= scale <= 1.02 and abs(angle) <= 1):
        raise ValueError(f"Scale/rotation mismatch: scale={scale:.4f}, rotation={angle:.3f} deg; "
                         "not normalizing away a real geometry difference. Verify DPR, CSS width and app zoom")
    transformed = cv2.transform(actual_points[inliers], estimated)
    median_residual_px = float(np.median(np.linalg.norm(transformed - reference_points[inliers], axis=2)))
    if median_residual_px > 3.0:
        raise ValueError(f"Too much landmark misalignment ({median_residual_px:.2f}px): compare the same app state")

    # Integer shift only. Do NOT silently scale/rotate actual, which would erase layout differences.
    shift_x, shift_y = round(tx), round(ty)
    translate = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
    aligned = cv2.warpAffine(candidate, translate, (w, h), flags=cv2.INTER_NEAREST,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    valid = cv2.warpAffine(np.full((hc, wc), 255, np.uint8), translate, (w, h),
                           flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    valid = (valid > 0) & (roi > 0)
    pixel_count = int(valid.sum())
    if pixel_count < 200000:
        raise ValueError(f"Overlap too small ({pixel_count}px); cannot compare")

    abs_diff = cv2.absdiff(real, aligned)
    max_diff = abs_diff.max(axis=2)
    diff_mask = valid & (max_diff > threshold)
    rgb_mad = float(abs_diff[valid].mean())
    changed_percent = float(100 * diff_mask.sum() / pixel_count)
    valid_mask = np.zeros((h, w), dtype=np.uint8)
    valid_mask[valid] = 255
    error_mask = np.zeros((h, w), dtype=np.uint8)
    error_mask[diff_mask] = 255
    diff_rgb = np.zeros_like(real)
    diff_rgb[valid] = np.minimum(255, abs_diff[valid].astype(np.uint16) * 3).astype(np.uint8)
    blended = ((real.astype(np.uint16) + aligned.astype(np.uint16)) // 2).astype(np.uint8)
    blended[~valid] = real[~valid]

    output_dir.mkdir(parents=True, exist_ok=True)
    Image.fromarray(aligned).save(report_path(output_dir, "aligned-candidate.png"))
    Image.fromarray(blended).save(report_path(output_dir, "overlay.png"))
    Image.fromarray(diff_rgb).save(report_path(output_dir, "diff-3x.png"))
    Image.fromarray(error_mask).save(report_path(output_dir, "error-mask.png"))
    Image.fromarray(valid_mask).save(report_path(output_dir, "valid-mask.png"))
    report = {
        "reference": str(reference_path),
        "candidate": str(candidate_path),
        "reference_size_px": [w, h],
        "candidate_size_px": [wc, hc],
        "roi_reference_screen_px": {"x": 0, "y": top, "width": w, "height": bottom-top},
        "registration": {
            "method": "SIFT + RANSAC; integer translation ONLY for image diff",
            "matching_features": len(good), "inliers": count,
            "estimated_scale_diagnostic_only": round(scale, 6),
            "estimated_rotation_degrees_diagnostic_only": round(angle, 4),
            "estimated_translation_screen_px": [round(tx, 3), round(ty, 3)],
            "used_translation_screen_px": [shift_x, shift_y],
            "used_translation_css_px_at_dpr3": [round(shift_x / 3, 3), round(shift_y / 3, 3)],
            "median_registration_residual_px": round(median_residual_px, 3),
        },
        "diff": {
            "overlap_pixels": pixel_count,
            "changed_pixels_above_threshold": int(diff_mask.sum()),
            "threshold_max_rgb": threshold,
            "changed_percent": round(changed_percent, 4),
            "mean_absolute_rgb_difference": round(rgb_mad, 4),
        },
        "warnings": [
            "Alignment compensates global translation; evaluate the translation separately as a possible layout defect.",
            "Raw RGB errors are not a perceptual similarity metric and do not prove Safari compatibility.",
            "The reference ROI excludes obvious Safari chrome; it is NOT a measurement of DOM or visual viewport.",
            "Compare equivalent state: same route, quantity, method, theme, scroll position and loaded assets.",
        ],
    }
    report_path(output_dir, "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report



def compare_raw(reference_path: Path, candidate_path: Path, output_dir: Path,
                reference_crop: tuple[int, int, int, int] | None = None,
                candidate_crop: tuple[int, int, int, int] | None = None,
                resize_candidate: bool = False, threshold: int = 16) -> dict:
    """Raw RGB difference on strictly matching geometry (unless resizing is explicit)."""
    reference = load_image(reference_path, reference_crop)
    candidate = load_image(candidate_path, candidate_crop)
    if candidate.size != reference.size:
        if not resize_candidate:
            raise ValueError(f'Sizes differ: reference={reference.size}, candidate={candidate.size}; '
                             'crop to the same content area, or explicitly use --resize-candidate')
        candidate = candidate.resize(reference.size, Image.Resampling.LANCZOS)

    difference = ImageChops.difference(reference, candidate)
    red, green, blue = difference.split()
    max_delta = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    mask = max_delta.point(lambda value: 255 if value > threshold else 0)
    total = reference.width * reference.height
    changed = mask.histogram()[255]
    mean = ImageStat.Stat(difference).mean
    report = {
        'reference': str(reference_path), 'candidate': str(candidate_path),
        'alignedSize': list(reference.size), 'threshold': threshold,
        'changedPixels': changed, 'totalPixels': total,
        'changedPercent': round(100 * changed / total, 4),
        'meanAbsoluteRgbDifference': round(sum(mean) / 3, 4),
        'resampledCandidate': resize_candidate,
        'referenceCrop': reference_crop, 'candidateCrop': candidate_crop,
        'note': 'Raw pixel statistics, not a perceptual similarity score or Safari fidelity benchmark.',
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    ImageEnhance.Contrast(difference).enhance(3).save(output_dir / 'diff-3x.png')
    mask.save(output_dir / 'error-mask.png')
    Image.blend(reference, candidate, 0.5).save(output_dir / 'overlay.png')
    (output_dir / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n',
                                            encoding='utf-8')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='mode', required=True)
    for mode in ('raw', 'align'):
        cmd = commands.add_parser(mode, help=('Pixel diff on matched dimensions' if mode == 'raw'
                                              else 'SIFT/RANSAC alignment with integer translation only'))
        cmd.add_argument('--reference', type=Path, required=True)
        cmd.add_argument('--candidate', '--actual', dest='candidate', type=Path, required=True)
        cmd.add_argument('--output-dir', type=Path, default=Path('out/compare'))
        cmd.add_argument('--threshold', type=int, default=16)
        if mode == 'raw':
            cmd.add_argument('--reference-crop', type=crop_spec)
            cmd.add_argument('--candidate-crop', '--actual-crop', type=crop_spec, dest='candidate_crop')
            cmd.add_argument('--resize-candidate', action='store_true',
                             help='Explicit resizing may conceal real geometry differences')
        else:
            cmd.add_argument('--roi-top', type=int, default=DEFAULT_TOP)
            cmd.add_argument('--roi-bottom', type=int, default=DEFAULT_BOTTOM)
            cmd.add_argument('--min-inliers', type=int, default=10)
    args = parser.parse_args()
    if not 0 <= args.threshold <= 255:
        parser.error('--threshold must be 0..255')
    if args.mode == 'align' and args.min_inliers < 4:
        parser.error('--min-inliers must be >= 4')
    try:
        if args.mode == 'raw':
            report = compare_raw(args.reference, args.candidate, args.output_dir,
                                 args.reference_crop, args.candidate_crop,
                                 args.resize_candidate, args.threshold)
        else:
            report = compare_aligned(args.reference, args.candidate, args.output_dir,
                                     args.roi_top, args.roi_bottom, args.threshold, args.min_inliers)
    except (ValueError, OSError, ImportError) as exc:
        parser.exit(1, f'ERROR: {exc}\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
