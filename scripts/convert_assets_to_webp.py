"""Generate WebP siblings for every photographic asset.

Usage:
    python3 scripts/convert_assets_to_webp.py [--force] [--max-width 2000]

Behaviour:
    - Walks ``assets/`` and looks at every ``.jpg``, ``.jpeg``, ``.png`` file.
    - Writes a sibling ``.webp`` next to it. Existing WebPs are reused unless the
      source is newer or ``--force`` is set.
    - JPEG sources are encoded with quality 82 (visually indistinguishable on
      photographs but ~30% smaller).
    - PNG sources keep their alpha channel and are encoded losslessly so logos,
      screenshots and transparent badges stay crisp.
    - Anything wider than ``--max-width`` (default 2000 px) is downscaled.
      The hero image renders at most ~1100 px CSS-wide; 2000 px gives plenty of
      retina headroom while preventing 4000+ px source files from shipping.

The script does not delete the originals: they remain the editable masters and
GitHub Pages does not serve them because nothing in the rendered HTML links to
them. If you want to clean them out later, you can move them to ``assets/_originals/``
and exclude that folder from the deploy.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "Pillow is required. Install it with:\n"
        "    python3 -m pip install -r requirements.txt\n"
    )
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT / "assets"
SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png"}

JPEG_QUALITY = 82
PNG_LOSSLESS = True


def needs_rebuild(source: Path, target: Path) -> bool:
    if not target.exists():
        return True
    return source.stat().st_mtime > target.stat().st_mtime


def has_meaningful_alpha(img: "Image.Image") -> bool:
    """Return True if the image has an alpha channel with at least one pixel
    that is not fully opaque. PNG team photos exported from screenshots usually
    carry a redundant alpha channel that we can safely drop."""
    if "A" not in img.getbands():
        return False
    alpha = img.getchannel("A")
    return alpha.getextrema()[0] < 255


def convert(source: Path, max_width: int, force: bool) -> tuple[bool, int, int]:
    target = source.with_suffix(".webp")
    if not force and not needs_rebuild(source, target):
        return False, source.stat().st_size, target.stat().st_size

    with Image.open(source) as img:
        is_png = source.suffix.lower() == ".png"
        keep_alpha = is_png and has_meaningful_alpha(img)

        if keep_alpha:
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        if img.width > max_width:
            new_height = round(img.height * max_width / img.width)
            img = img.resize((max_width, new_height), Image.LANCZOS)

        save_kwargs: dict = {"method": 6}
        if keep_alpha:
            # Preserve exact pixels for logos and transparent badges.
            save_kwargs.update(lossless=PNG_LOSSLESS, quality=100)
        else:
            save_kwargs.update(quality=JPEG_QUALITY)

        img.save(target, format="WEBP", **save_kwargs)

    return True, source.stat().st_size, target.stat().st_size


def human(num_bytes: int) -> str:
    """Render a byte count in B/KB/MB at the largest sensible unit."""
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.0f} KB"
    return f"{num_bytes / 1024 / 1024:.2f} MB"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Re-encode even if the WebP looks fresh.")
    parser.add_argument(
        "--max-width",
        type=int,
        default=2000,
        help="Cap output width in pixels (default: 2000).",
    )
    args = parser.parse_args()

    if not ASSETS_DIR.exists():
        sys.stderr.write(f"assets directory not found: {ASSETS_DIR}\n")
        raise SystemExit(1)

    sources = sorted(
        p for p in ASSETS_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
    )

    if not sources:
        print("No raster assets found.")
        return

    total_src = 0
    total_dst = 0
    rebuilt = 0
    skipped = 0
    print(f"Converting {len(sources)} assets to WebP (max width {args.max_width}px)…")
    for source in sources:
        rebuilt_now, src_bytes, dst_bytes = convert(source, args.max_width, args.force)
        total_src += src_bytes
        total_dst += dst_bytes
        if rebuilt_now:
            rebuilt += 1
            saved = src_bytes - dst_bytes
            pct = saved / src_bytes * 100 if src_bytes else 0
            print(f"  {source.name:36s}  {human(src_bytes):>8s} -> {human(dst_bytes):>8s}  (-{pct:.0f}%)")
        else:
            skipped += 1

    if rebuilt:
        saved = total_src - total_dst
        pct = saved / total_src * 100 if total_src else 0
        print(
            f"Done. Rebuilt {rebuilt}, skipped {skipped}. "
            f"Total {human(total_src)} -> {human(total_dst)} (-{pct:.0f}%)."
        )
    else:
        print(f"Done. Nothing to rebuild ({skipped} up to date).")


if __name__ == "__main__":
    main()
