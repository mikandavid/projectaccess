"""Export flyer-bootcamp-2026.html to a print-ready A5 PDF.

Renders the on-screen flyer in headless Chromium, then saves a high-DPI
screenshot as PDF via Pillow. This avoids Chromium's print/PDF gradient bugs
(semi-transparent stops turning pink/magenta) while keeping colours faithful
to the browser preview.

Setup (once):
    python3 -m pip install playwright Pillow
    playwright install chromium

Usage:
    python3 scripts/export_flyer.py
    python3 scripts/export_flyer.py -o flyer-bootcamp-2026.pdf
    python3 scripts/export_flyer.py --open
"""

from __future__ import annotations

import argparse
import io
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_HTML = ROOT / "flyer-bootcamp-2026.html"
DEFAULT_OUTPUT = ROOT / "flyer-bootcamp-2026.pdf"

# A5 at 96 CSS px/in — keeps mm-based layout stable before capture.
A5_VIEWPORT = {"width": 559, "height": 794}
# 300 dpi → 1748 × 2480 px for a true A5 print target.
PRINT_DPI = 300
A5_PRINT_PX = (
    round(148 / 25.4 * PRINT_DPI),
    round(210 / 25.4 * PRINT_DPI),
)

# Drop the on-screen "paper on a desk" frame; keep screen rendering otherwise.
EXPORT_STYLE = """
html,
body {
  margin: 0 !important;
  padding: 0 !important;
  background: #fff !important;
  overflow: hidden !important;
}

.flyer-stage {
  display: block !important;
  min-height: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
}

.flyer-page {
  box-shadow: none !important;
}
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=DEFAULT_HTML,
        help=f"Flyer HTML file (default: {DEFAULT_HTML.name})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output PDF path (default: {DEFAULT_OUTPUT.name})",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=PRINT_DPI,
        help=f"Print resolution (default: {PRINT_DPI})",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the PDF after export (macOS)",
    )
    return parser.parse_args()


def ensure_playwright():
    try:
        from playwright.sync_api import sync_playwright

        return sync_playwright
    except ImportError:
        sys.stderr.write(
            "Playwright is required for PDF export. Install it with:\n"
            "    python3 -m pip install playwright\n"
            "    playwright install chromium\n"
        )
        raise SystemExit(1) from None


def ensure_pillow():
    try:
        from PIL import Image

        return Image
    except ImportError:
        sys.stderr.write(
            "Pillow is required for PDF export. Install it with:\n"
            "    python3 -m pip install -r requirements.txt\n"
        )
        raise SystemExit(1) from None


def export_pdf(html_path: Path, output_path: Path, dpi: int) -> None:
    if not html_path.is_file():
        sys.stderr.write(f"Flyer not found: {html_path}\n")
        raise SystemExit(1)

    Image = ensure_pillow()
    sync_playwright = ensure_playwright()
    url = html_path.resolve().as_uri()
    target_px = (
        round(148 / 25.4 * dpi),
        round(210 / 25.4 * dpi),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Scale viewport capture so the PNG lands near the final print pixel size.
    device_scale_factor = max(1, round(target_px[0] / A5_VIEWPORT["width"]))

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            args=["--force-color-profile=srgb"],
        )
        page = browser.new_page(
            viewport=A5_VIEWPORT,
            device_scale_factor=device_scale_factor,
        )
        page.goto(url, wait_until="networkidle")
        page.wait_for_function("document.fonts.ready")
        page.emulate_media(media="screen")
        page.add_style_tag(content=EXPORT_STYLE)
        png_bytes = page.locator(".flyer-page").screenshot(type="png")
        browser.close()

    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    if img.size != target_px:
        img = img.resize(target_px, Image.Resampling.LANCZOS)
    img.save(str(output_path.resolve()), "PDF", resolution=dpi)

    print(f"Wrote {output_path}")


def maybe_open(path: Path) -> None:
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)


def main() -> None:
    args = parse_args()
    export_pdf(args.input.resolve(), args.output.resolve(), args.dpi)
    if args.open:
        maybe_open(args.output.resolve())


if __name__ == "__main__":
    main()
