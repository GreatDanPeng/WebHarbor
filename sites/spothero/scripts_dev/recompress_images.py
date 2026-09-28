"""Re-encode downloaded images to a compact, deterministic size.

Facility images: max 640x480 JPEG q=72.
Site images:     max 1200px wide JPEG q=78 (PNG icons/logos kept as PNG, resized to 512px).
"""
import pathlib
from io import BytesIO

from PIL import Image

BASE = pathlib.Path(__file__).resolve().parent.parent / "static" / "images"

for path in sorted(BASE.rglob("*")):
    if not path.is_file() or path.name == ".gitkeep":
        continue
    data = path.read_bytes()
    try:
        img = Image.open(BytesIO(data))
        img.load()
    except Exception as exc:
        print("skip (unreadable):", path, exc)
        continue
    rel = path.relative_to(BASE)
    is_png = path.suffix.lower() == ".png"
    is_ico = path.suffix.lower() == ".ico"
    is_svg = path.suffix.lower() == ".svg"
    if is_ico or is_svg:
        continue
    if "facilities" in rel.parts:
        max_w, max_h, q = 640, 480, 72
    else:
        max_w, max_h, q = 1200, 1200, 78
    w, h = img.size
    scale = min(1.0, max_w / w, max_h / h)
    if scale < 1.0:
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    if is_png:
        # keep icons as PNG when small; convert photos to JPEG
        if path.stat().st_size < 400_000 and max(img.size) <= 600:
            img.save(path, "PNG", optimize=True)
            continue
        # photo-like png -> jpg
        if img.mode in ("RGBA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = bg
        else:
            img = img.convert("RGB")
        newp = path.with_suffix(".jpg")
        img.save(newp, "JPEG", quality=q, optimize=True, progressive=True)
        if newp != path:
            path.unlink()
    else:
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(path, "JPEG", quality=q, optimize=True, progressive=True)
print("done")
