#!/usr/bin/env python3
import sys, os, time, atexit, shutil, argparse, termios, tty, fcntl, select, signal, traceback, errno
import numpy as np
import cv2
from datetime import datetime
import html as htmlmod

DEFAULT_RAMP = (
    " .'`^\",:;Il!i><~+_-?][}{1)(|\\/*tfjrxnuvczXYUJCLQ0OZ"
    "mwqpdbkhao*#MW&8%B@$"
)

# ---------- robust stdout writing ----------
_STDOUT_FD = sys.stdout.fileno()
def write_all(s: str):
    if not s:
        return
    data = s.encode("utf-8", "replace")
    n = 0
    while n < len(data):
        try:
            n += os.write(_STDOUT_FD, data[n:])
        except BlockingIOError:
            select.select([], [_STDOUT_FD], [])
            continue
        except InterruptedError:
            continue
        except OSError as e:
            if e.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                select.select([], [_STDOUT_FD], [])
                continue
            raise

def enter_alt():
    write_all("\x1b[?1049h\x1b[?25l")

def exit_alt():
    write_all("\x1b[0m\x1b[?25h\x1b[?1049l")

class RawStdin:
    def __init__(self):
        self.fd = sys.stdin.fileno()
        self.old_tc = termios.tcgetattr(self.fd)
        self.old_fl = fcntl.fcntl(self.fd, fcntl.F_GETFL)
    def __enter__(self):
        tty.setcbreak(self.fd)
        fcntl.fcntl(self.fd, fcntl.F_SETFL, self.old_fl | os.O_NONBLOCK)
        return self
    def __exit__(self, exc_type, exc, tb):
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_tc)
        fcntl.fcntl(self.fd, fcntl.F_SETFL, self.old_fl)

def get_term_size():
    size = shutil.get_terminal_size(fallback=(80, 24))
    return size.columns, max(1, size.lines)

def center_crop(frame, target_aspect):
    h, w = frame.shape[:2]
    aspect = w / h
    if aspect > target_aspect:
        new_w = int(h * target_aspect)
        x0 = (w - new_w) // 2
        return frame[:, x0:x0 + new_w]
    else:
        new_h = int(w / target_aspect)
        y0 = (h - new_h) // 2
        return frame[y0:y0 + new_h, :]

def apply_tonemap(gray_u8, contrast, brightness, gamma):
    g = gray_u8.astype(np.float32) / 255.0
    g = contrast * g + brightness
    g = np.clip(g, 0.0, 1.0)
    if abs(gamma - 1.0) > 1e-3:
        g = np.power(g, 1.0 / gamma)
    return (g * 255.0 + 0.5).astype(np.uint8)

def img_to_ascii(gray, lut):
    idx = (gray.astype(np.uint16) * (lut.size - 1)) // 255
    return lut[idx]  # HxW '<U1'

def set_xterm_font_px(px):
    write_all(f"\x1b]50;xft:Monospace:pixelsize={px}\x07")

# ---- xterm-256 color helpers ----
def _to_6cube(v): return int(round(v * (5.0/255.0)))
def _cube_level(i): return [0, 95, 135, 175, 215, 255][i]
def _grey_index(v):
    if v < 8: return 16  # push near-black to cube black
    if v > 248: return 231  # cube white
    return 232 + int(round(((v - 8) / 247.0) * 24))

def rgb_to_xterm256(r, g, b):
    r6, g6, b6 = _to_6cube(r), _to_6cube(g), _to_6cube(b)
    idx_cube = 16 + 36*r6 + 6*g6 + b6
    if abs(r - g) + abs(g - b) + abs(b - r) < 24:
        return _grey_index((r + g + b) // 3)
    return idx_cube

def xterm256_to_rgb(idx):
    if 16 <= idx <= 231:
        c = idx - 16
        r6 = c // 36
        g6 = (c % 36) // 6
        b6 = c % 6
        return _cube_level(r6), _cube_level(g6), _cube_level(b6)
    if 232 <= idx <= 255:
        level = 8 + 10 * (idx - 232)
        level = max(0, min(255, level))
        return level, level, level
    # 0..15: only 16 (black) should occur from our mapper; fall back to black
    return 0, 0, 0

def build_color_row(chars_row, rgb_row):
    Wc = chars_row.shape[0]
    Wr = rgb_row.shape[0]
    W = min(Wc, Wr)
    out = []
    last_idx = -1
    for i in range(W):
        r, g, b = map(int, rgb_row[i])
        idx = rgb_to_xterm256(r, g, b)
        if idx != last_idx:
            out.append(f"\x1b[38;5;{idx}m")
            last_idx = idx
        out.append(chars_row[i])
    out.append("\x1b[0m")
    return "".join(out)

def timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

# ---- NEW: save HTML with color support ----
def save_ascii_html(chars, rgb_image, path, bg="#000000", font_family="monospace", font_px=16, quantize_xterm=True):
    """
    chars: HxW array of 1-char strings (unicode)
    rgb_image: HxWx3 uint8, same grid size as chars (already resized)
    Writes an HTML file with colored ASCII using grouped <span> runs.
    """
    H, W = chars.shape
    with open(path, "w", encoding="utf-8") as f:
        f.write("<!doctype html><meta charset='utf-8'>")
        f.write(
            "<style>"
            "body{margin:0;background:%s;}"
            "pre{line-height:1; font-family:%s; font-size:%dpx;}"
            "</style><pre>" % (bg, font_family, font_px)
        )
        for r in range(H):
            last_hex = None
            run = []
            def flush():
                nonlocal run, last_hex
                if not run: return
                text = htmlmod.escape("".join(run))
                if last_hex:
                    f.write(f"<span style=\"color:{last_hex}\">{text}</span>")
                else:
                    f.write(text)
                run = []
            for i in range(W):
                R, G, B = map(int, rgb_image[r, i])
                if quantize_xterm:
                    idx = rgb_to_xterm256(R, G, B)
                    R, G, B = xterm256_to_rgb(idx)
                hexcol = f"#{R:02x}{G:02x}{B:02x}"
                if hexcol != last_hex:
                    flush()
                    last_hex = hexcol
                run.append(chars[r, i])
            flush()
            if r < H - 1:
                f.write("\n")
        f.write("</pre>")

def main():
    ap = argparse.ArgumentParser(description="Live ASCII camera in your terminal.")
    ap.add_argument("-d", "--device", type=int, default=0)
    ap.add_argument("-f", "--fps", type=float, default=30.0)
    ap.add_argument("-a", "--char-aspect", type=float, default=2.0)
    ap.add_argument("-r", "--ramp", type=str, default=DEFAULT_RAMP)
    ap.add_argument("-i", "--invert", action="store_true")
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--height", type=int, default=480)
    ap.add_argument("--no-mirror", action="store_true")
    ap.add_argument("--xterm-small", type=int)
    ap.add_argument("--xterm-restore", type=int)
    ap.add_argument("--color", action="store_true")
    ap.add_argument("--outdir", type=str, default="captures")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    # Tone
    contrast, brightness, gamma = 1.0, 0.0, 1.0
    step_c, step_b, step_g = 0.10, 0.05, 0.10
    c_min, c_max = 0.1, 4.0
    b_min, b_max = -1.0, 1.0
    g_min, g_max = 0.2, 5.0

    base_ramp = args.ramp
    invert_chars = args.invert
    mirror = not args.no_mirror
    color_enabled = args.color

    def current_lut():
        r = base_ramp[::-1] if invert_chars else base_ramp
        return np.array(list(r), dtype="<U1")
    lut = current_lut()

    os.makedirs(args.outdir, exist_ok=True)
    log_path = "ascii_cam.log"

    cap = cv2.VideoCapture(args.device, cv2.CAP_V4L2)
    if not cap.isOpened():
        print(f"Could not open camera {args.device}", file=sys.stderr)
        sys.exit(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    cap.set(cv2.CAP_PROP_FPS, args.fps)

    running, need_resize = True, True
    want_save = False
    last_error = ""
    error_until = 0.0

    def on_sigint(sig, frm):
        nonlocal running
        running = False
    def on_winch(sig, frm):
        nonlocal need_resize
        need_resize = True
    signal.signal(signal.SIGINT, on_sigint)
    try:
        signal.signal(signal.SIGWINCH, on_winch)
    except Exception:
        pass

    enter_alt()
    atexit.register(exit_alt)

    if args.xterm_small:
        set_xterm_font_px(args.xterm_small)
        if args.xterm_restore:
            atexit.register(set_xterm_font_px, args.xterm_restore)

    cols = rows = 0
    hud_enabled = True
    fps_smoothed = args.fps
    frame_budget = 1.0 / max(1e-6, args.fps)

    with RawStdin():
        try:
            while running:
                t0 = time.perf_counter()

                # input
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    ch = sys.stdin.read(1)
                    if ch:
                        if ch.lower() == "q":
                            break
                        elif ch == "-":
                            contrast = max(c_min, contrast - step_c)
                        elif ch in ("=", "+"):
                            contrast = min(c_max, contrast + step_c)
                        elif ch == "[":
                            brightness = max(b_min, brightness - step_b)
                        elif ch == "]":
                            brightness = min(b_max, brightness + step_b)
                        elif ch == ",":
                            gamma = max(g_min, gamma - step_g)
                        elif ch == ".":
                            gamma = min(g_max, gamma + step_g)
                        elif ch.lower() == "m":
                            mirror = not mirror
                        elif ch.lower() == "i":
                            invert_chars = not invert_chars
                            lut = current_lut()
                        elif ch.lower() == "c":
                            color_enabled = not color_enabled
                        elif ch == "0":
                            contrast, brightness, gamma = 1.0, 0.0, 1.0
                        elif ch == " ":
                            want_save = True

                # snap terminal size once per frame
                if need_resize:
                    need_resize = False
                    cols, rows = get_term_size()
                    write_all("\x1b[2J\x1b[H")

                rows_for_image = max(1, rows - (1 if rows >= 3 and hud_enabled else 0))
                target_aspect = cols / (rows_for_image * args.char_aspect)

                # capture
                ret, frame = cap.read()
                if not ret:
                    continue
                if mirror:
                    frame = cv2.flip(frame, 1)

                # crop & prep
                cropped = center_crop(frame, target_aspect)
                gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
                gray_tm = apply_tonemap(gray, contrast, brightness, gamma)

                # downsample to snapped size
                W = max(1, cols)
                H = rows_for_image
                gray_small = cv2.resize(gray_tm, (W, H), interpolation=cv2.INTER_AREA)
                chars = img_to_ascii(gray_small, lut)

                # color buffer to same snapped size (for terminal and for HTML)
                try:
                    rgb_small = cv2.cvtColor(
                        cv2.resize(cropped, (W, H), interpolation=cv2.INTER_AREA),
                        cv2.COLOR_BGR2RGB
                    )
                except Exception:
                    rgb_small = np.repeat(gray_small[..., None], 3, axis=2)

                # render
                write_all("\x1b[H")
                if color_enabled:
                    try:
                        for r in range(H):
                            write_all(build_color_row(chars[r], rgb_small[r]))
                            if r < H - 1:
                                write_all("\n")
                    except Exception as e:
                        color_enabled = False
                        last_error = f"color off: {type(e).__name__}"
                        error_until = time.perf_counter() + 3.0
                        write_all("\x1b[H" + "\n".join("".join(row) for row in chars))
                else:
                    write_all("\n".join("".join(row) for row in chars))

                # save?
                if want_save:
                    want_save = False
                    ts = timestamp()
                    png_path = os.path.join(args.outdir, f"ascii_cam_{ts}.png")
                    txt_path = os.path.join(args.outdir, f"ascii_cam_{ts}.txt")
                    html_path = os.path.join(args.outdir, f"ascii_cam_{ts}.html")
                    try:
                        cv2.imwrite(png_path, cropped)
                        with open(txt_path, "w", encoding="utf-8") as f:
                            f.write("\n".join("".join(row) for row in chars))
                        # HTML: quantize to xterm-256 for the look/size
                        save_ascii_html(chars, rgb_small, html_path, bg="#000000", font_px=8, quantize_xterm=True)
                        last_error = "saved"
                    except Exception as e:
                        last_error = f"save err: {type(e).__name__}"
                        if args.debug:
                            with open(log_path, "a") as log:
                                traceback.print_exc(file=log)
                    error_until = time.perf_counter() + 1.0

                # HUD
                show_hud = hud_enabled and rows >= 3
                if show_hud:
                    fps_inst = 1.0 / max(1e-6, (time.perf_counter() - t0))
                    fps_smoothed = 0.85 * fps_smoothed + 0.15 * fps_inst
                    status = last_error if time.perf_counter() < error_until else ""
                    hud = (
                        f" FPS {fps_smoothed:5.1f}  "
                        f"C {contrast:5.2f}  B {brightness:+5.2f}  G {gamma:5.2f}  "
                        f"{'MIRROR' if mirror else 'TRUE  '}  "
                        f"{'INV' if invert_chars else 'NORM'}  "
                        f"{'COLOR' if color_enabled else 'MONO '}  "
                        f"{status:<10}  "
                        "keys: [-/+]B  (-/=)C  (,/.)G  c color  m mirror  i invert  0 reset  SPACE save  q quit "
                    )
                    write_all("\x1b[0m")
                    if len(hud) < cols: hud = hud + " " * (cols - len(hud))
                    write_all("\n" + hud[:cols])

                # pace
                dt = time.perf_counter() - t0
                if dt < frame_budget:
                    time.sleep(frame_budget - dt)

        except Exception:
            if args.debug:
                with open(log_path, "a") as log:
                    traceback.print_exc(file=log)
            raise
        finally:
            cap.release()

if __name__ == "__main__":
    main()
