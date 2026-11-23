# ============================================================
# make_icon.py  —  PNG -> multi-size Windows .ico   (reusable tool, NEW FILE)
# ============================================================
# Windows needs ONE .ico file that contains several sizes of the picture
# (16, 24, 32, 48, 64, 128 and 256 px), because it shows different sizes in
# the title bar, taskbar, Explorer and the Start Menu. This script makes that
# file with Pillow, which CustomTkinter already installs -- no extra tool.
#
# USAGE (run in a command prompt):
#     python make_icon.py logo.png                 -> creates logo.ico
#     python make_icon.py logo.png app.ico         -> creates app.ico
#     python make_icon.py --placeholder            -> draws a simple starter
#                                                     icon: app_icon.png + app.ico
#
# YOUR PNG SHOULD BE: square, at least 512 x 512 px (1024 is better), with a
# transparent background and a bold, simple shape (fine detail disappears at
# 16 px). If it is not square it is centred on a transparent square.
# ============================================================

import argparse
import os
import sys

from PIL import Image, ImageDraw

# The sizes stored inside the .ico (the maximum Windows supports is 256).
ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def png_to_ico(png_path: str, ico_path: str) -> None:
    """Read a PNG and write a multi-size .ico next to it."""
    image = Image.open(png_path).convert("RGBA")

    # Make the picture square by centring it on a transparent square.
    width, height = image.size
    if width != height:
        side = max(width, height)
        square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        square.paste(image, ((side - width) // 2, (side - height) // 2))
        image = square
        print(f"Note: the PNG was not square ({width}x{height}); it was centred.")

    if image.width < 256:
        print(f"Warning: the PNG is only {image.width} px wide. Sizes larger than "
              "that are skipped; use at least 256 px (512+ is better).")

    image.save(ico_path, format="ICO", sizes=ICO_SIZES)   # Pillow shrinks the picture for each size
    print(f"Created {ico_path}")


def make_placeholder(png_path: str) -> None:
    """
    Draw a simple starter icon: a blue rounded square with a white check mark.
    Replace it with your own artwork whenever you like.
    """
    scale = 2                                  # draw twice as large, then shrink = smooth edges
    size = 1024 * scale
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    margin = int(size * 0.04)
    draw.rounded_rectangle(
        (margin, margin, size - margin, size - margin),
        radius=int(size * 0.22), fill=(79, 142, 247, 255)          # the app's accent blue
    )
    # A slightly darker lower half gives the square a little depth.
    lower = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(lower).rounded_rectangle(
        (margin, int(size * 0.55), size - margin, size - margin),
        radius=int(size * 0.22), fill=(45, 111, 212, 255))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (margin, margin, size - margin, size - margin), radius=int(size * 0.22), fill=255)
    image.paste(lower, (0, 0), Image.composite(lower.getchannel("A"), Image.new("L", (size, size), 0), mask))

    # The white check mark: two thick strokes with round ends.
    width = int(size * 0.10)
    points = [(int(size * 0.27), int(size * 0.52)),
              (int(size * 0.43), int(size * 0.68)),
              (int(size * 0.74), int(size * 0.33))]
    draw = ImageDraw.Draw(image)
    draw.line(points, fill="white", width=width, joint="curve")
    for x, y in (points[0], points[2]):                         # round the two loose ends
        draw.ellipse((x - width // 2, y - width // 2, x + width // 2, y + width // 2), fill="white")

    image.resize((1024, 1024), Image.LANCZOS).save(png_path)
    print(f"Created {png_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Make a multi-size Windows .ico from a PNG.")
    parser.add_argument("png", nargs="?", help="input PNG file")
    parser.add_argument("ico", nargs="?", help="output .ico file (default: same name as the PNG)")
    parser.add_argument("--placeholder", action="store_true",
                        help="draw a simple starter icon (app_icon.png + app.ico) instead")
    args = parser.parse_args()

    if args.placeholder:
        make_placeholder("app_icon.png")
        png_to_ico("app_icon.png", "app.ico")
        return 0
    if not args.png:
        parser.print_help()
        return 1
    if not os.path.isfile(args.png):
        print(f"File not found: {args.png}")
        return 1
    png_to_ico(args.png, args.ico or os.path.splitext(args.png)[0] + ".ico")
    return 0


if __name__ == "__main__":
    sys.exit(main())
