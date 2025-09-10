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
    html.append('  <link rel="icon" type="image/x-icon" href="/favicon.ico?v=2">')
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
    html.append("  .folder-icon {")
    html.append("        width: 90px;")
    html.append("        height: 60px;")
    html.append("      }")
    html.append("      .folder-icon path {")
    html.append("        stroke: lime;")
    html.append("        fill: none;")
    html.append("        stroke-width: 2;")
    html.append("      }")
    html.append("      .folder-icon text {")
    html.append("        fill: lime;")
    html.append("        font-family: sans-serif;")
    html.append("        font-size: 12px;")
    html.append("      }")
    html.append("</style>")
    html.append("</head>")
    html.append("<body>")
    html.append(
        '<svg class="folder-icon" viewBox="0 0 24 24" style="height: 1em; width: auto; '
        "vertical-align: middle; stroke: lime; fill: none; stroke-width: 1; stroke-linejoin: round;"
        'stroke-linecap: round; font-size: 36px;">'
    )
    html.append('   <path d="M3 7h6l2 2h10v11H3z"/>')
    html.append(" </svg>")
    html.append(
        f'<span style="color:lime; margin-left:4px; font-weight: bold; font-family:monospace; font-size:36px; line-height: 1; vertical-align: middle;">{title}/<br><br>'
    )
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

    out = target / "index.html"
    new_content = "\n".join(html)

    # Check if file exists and compare content
    should_write = True
    if out.exists():
        try:
            with open(out, "r", encoding="utf-8") as f:
                existing_content = f.read()
            
            if existing_content == new_content:
                should_write = False
                print(f"Skipped {out} (no changes)")
        except (IOError, UnicodeDecodeError) as e:
            print(f"Warning: Could not read existing {out}: {e}")
            # Continue with write if we can't read the existing file

    if should_write:
        with open(out, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Generated {out}")

if __name__ == "__main__":
    dir_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    if not dir_arg.is_dir():
        print(f"Error: {dir_arg} is not a directory")
        sys.exit(1)
    generate_index(dir_arg)
