"""One-off: derive transparent Lion & Sun PNGs from the owner reference JPG."""
from __future__ import annotations

import os
from pathlib import Path

from PIL import Image

SRC = Path(
    r"C:\Users\Sniper\.cursor\projects\g-robat-ahos\assets"
    r"\c__Users_Sniper_AppData_Roaming_Cursor_User_workspaceStorage_aedc64d3234a2fb08a127a7e225bbd81_images"
    r"_____________-e2b9c826-4b17-407f-abd5-6378692d0334.jpg"
)
OUT_DIR = Path(__file__).resolve().parents[1] / "public" / "brand" / "logo"
LAUNCHER_SPLASH = Path(r"G:\robat\AHOS_Launcher\splash")


def remove_cream_background(im: Image.Image, tol: int = 28) -> Image.Image:
    im = im.convert("RGBA")
    w, h = im.size
    pixels = im.load()
    corners = [pixels[0, 0], pixels[w - 1, 0], pixels[0, h - 1], pixels[w - 1, h - 1]]
    avg = tuple(sum(c[i] for c in corners) // 4 for i in range(3))
    out = Image.new("RGBA", im.size)
    opx = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            dr, dg, db = abs(r - avg[0]), abs(g - avg[1]), abs(b - avg[2])
            if dr < tol and dg < tol and db < tol:
                dist = max(dr, dg, db)
                if dist < tol * 0.6:
                    opx[x, y] = (r, g, b, 0)
                else:
                    fade = int(255 * (dist - tol * 0.6) / (tol * 0.4))
                    opx[x, y] = (r, g, b, min(255, fade))
            else:
                opx[x, y] = (r, g, b, a)
    return out


def main() -> None:
    if not SRC.is_file():
        raise SystemExit(f"reference missing: {SRC}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    im = Image.open(SRC)
    print("source", im.size)
    im.save(OUT_DIR / "ahos-lion-sun-reference.png", "PNG", optimize=True)
    cut = remove_cream_background(im)
    bbox = cut.getbbox()
    if bbox:
        pad = 8
        bbox = (
            max(0, bbox[0] - pad),
            max(0, bbox[1] - pad),
            min(cut.width, bbox[2] + pad),
            min(cut.height, bbox[3] + pad),
        )
        cut = cut.crop(bbox)
    cut.save(OUT_DIR / "ahos-lion-sun-transparent.png", "PNG", optimize=True)
    for size, name in ((256, "ahos-lion-sun-256.png"), (512, "ahos-lion-sun-512.png")):
        scaled = cut.copy()
        scaled.thumbnail((size, size), Image.Resampling.LANCZOS)
        scaled.save(OUT_DIR / name, "PNG", optimize=True)
    LAUNCHER_SPLASH.mkdir(parents=True, exist_ok=True)
    cut.save(LAUNCHER_SPLASH / "ahos-lion-sun-transparent.png", "PNG", optimize=True)
    print("wrote transparent", cut.size)


if __name__ == "__main__":
    main()
