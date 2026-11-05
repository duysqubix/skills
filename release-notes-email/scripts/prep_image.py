#!/usr/bin/env python3
"""Crop, resize and compress screenshots for email, or build a contact sheet.

  python prep_image.py IN OUT [--crop x0,y0,x1,y1] [--width 1120]
      --crop values <= 1 are fractions of the image size; larger values are pixels
      (real pixels, not the scaled-down size shown in a chat preview).
      Desktop shots: --width 1120 (shown at 536px). Phone shots: --width 440 (shown at 230px).

  python prep_image.py --sheet OUT IMG [IMG ...]
      Stacks images vertically (max 1120 wide) so you can review all crops at once.
"""
import argparse, os, sys
from PIL import Image, ImageOps  # needs Pillow 9.1+


def prep(src, dst, crop, width):
    # Apply EXIF rotation (phone photos), and put transparent areas on white instead of black.
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGBA")
    im = Image.alpha_composite(Image.new("RGBA", im.size, "white"), im).convert("RGB")
    W, H = im.size
    if crop:
        vals = [float(v) for v in crop.split(",")]
        if len(vals) != 4:
            sys.exit("--crop needs x0,y0,x1,y1")
        if all(v <= 1 for v in vals):
            vals = [vals[0] * W, vals[1] * H, vals[2] * W, vals[3] * H]
        box = tuple(int(round(v)) for v in vals)
        x0, y0, x1, y1 = box
        if not (0 <= x0 < x1 <= W and 0 <= y0 < y1 <= H) or x1 - x0 < 16 or y1 - y0 < 16:
            sys.exit(f"--crop {crop} gives box {box}, which is under 16px or outside the {W}x{H} image. "
                     "Use all fractions (0-1) or all real pixels.")
        im = im.crop(box)
    if width and im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    os.makedirs(os.path.dirname(os.path.abspath(dst)) or ".", exist_ok=True)
    if dst.lower().endswith((".jpg", ".jpeg")):
        im.save(dst, quality=88, optimize=True)
    else:
        # UI screenshots compress very well to a 256-color palette without visible loss
        im.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(dst, optimize=True)
    print(f"{dst}: {im.size[0]}x{im.size[1]}, {os.path.getsize(dst) // 1024} KB")


def sheet(dst, paths):
    paths = [p for p in paths if os.path.abspath(p) != os.path.abspath(dst)]  # don't stack an old sheet
    if not paths:
        sys.exit("--sheet needs OUT plus at least one image")
    ims = [Image.open(p).convert("RGB") for p in paths]
    ims = [i if i.width <= 1120 else i.resize((1120, round(i.height * 1120 / i.width))) for i in ims]
    W = max(i.width for i in ims)
    H = sum(i.height for i in ims) + 30 * len(ims)
    c = Image.new("RGB", (W, H), (200, 200, 200))
    y = 0
    for i in ims:
        c.paste(i, (0, y))
        y += i.height + 30
    c.save(dst)
    print(f"Sheet: {dst}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", nargs="+", metavar=("OUT", "IMG"))
    ap.add_argument("src", nargs="?")
    ap.add_argument("dst", nargs="?")
    ap.add_argument("--crop")
    ap.add_argument("--width", type=int, default=1120)
    a = ap.parse_args()
    if a.sheet:
        sheet(a.sheet[0], a.sheet[1:])
    elif a.src and a.dst:
        prep(a.src, a.dst, a.crop, a.width)
    else:
        ap.print_help()
