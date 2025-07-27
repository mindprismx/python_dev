#!/usr/bin/env python3
# image_indexer.py
# Generates a thumbnails-based HTML index for images in a directory

import sys
from pathlib import Path
from PIL import Image
import urllib.parse

# ─── Config ──────────────────────────────────────────────────────────────
THUMB_DIR_NAME = "thumbnails"
THUMB_SIZE = (200, 200)  # max width, height in pixels
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif"}


# ─── Helpers ─────────────────────────────────────────────────────────────
def human_readable_size(size):
    for unit in ["B", "K", "M", "G", "T"]:
        if size < 1024.0 or unit == "T":
            return f"{size:3.1f}{unit}"
        size /= 1024.0


def make_thumbnail(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        img.thumbnail(THUMB_SIZE)
        img.save(dst)


# ─── Main logic ──────────────────────────────────────────────────────────
def generate_index(target: Path):
    # Find image files
    imgs = sorted(
        [p for p in target.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS],
        key=lambda p: p.name.lower(),
    )

    thumbs_dir = target / THUMB_DIR_NAME
    entries = []
    for img in imgs:
        thumb = thumbs_dir / img.name
        # Regenerate outdated or missing thumbs
        if not thumb.exists() or img.stat().st_mtime > thumb.stat().st_mtime:
            make_thumbnail(img, thumb)
        size_str = human_readable_size(img.stat().st_size)
        entries.append(
            (
                img.name,
                size_str,
                urllib.parse.quote(img.name),
                urllib.parse.quote(str(thumb.relative_to(target))),
            )
        )

    # Build HTML
    title = target.name or "/"
    html = []
    html.append("<!DOCTYPE html>")
    html.append("<html>")
    html.append("<head>")
    html.append("  <meta charset='utf-8'>")
    html.append(f"  <title>Index of {title}</title>")
    html.append("<style>")
    html.append("  html,body {margin:0;padding:0;background:black;color:lime}")
    html.append("  body {padding:20px;font-family:monospace}")
    html.append("  h1 {margin:0 0 20px 0;font-size:24pt}")
    html.append("  #gallery {")
    html.append("    display: grid;")
    html.append("    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));")
    html.append("    gap: 15px;")
    html.append("  }")
    html.append("  .thumb-cell {text-align:center}")
    html.append(
        "  .thumb-cell img {max-width:200px;height:auto;display:block;margin:0 auto}"
    )
    html.append("  .filename {font-size:10pt;margin-top:5px}")
    html.append("  .filesize {font-size:8pt}")
    html.append("  a, a:visited {color:lime;text-decoration:none}")
    html.append("  a:hover {text-decoration:underline}")
    html.append("</style>")
    html.append("</head>")
    html.append("<body>")
    html.append(f"  <h1>{title}/</h1>")
    html.append('  <div id="gallery">')
    for name, size_str, href, thumb in entries:
        html.append('    <div class="thumb-cell">')
        html.append(f'      <a href="{href}"><img src="{thumb}" alt="{name}"></a>')
        html.append(f'      <div class="filename">{name}</div>')
        html.append(f'      <div class="filesize">{size_str}</div>')
        html.append("    </div>")
    html.append("  </div>")
    html.append("</body>")
    html.append("</html>")

    # Write index.html
    out = target / "index.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    print(f"Generated {out}")


if __name__ == "__main__":
    dir_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    if not dir_arg.is_dir():
        print(f"Error: {dir_arg} is not a directory")
        sys.exit(1)
    generate_index(dir_arg)
