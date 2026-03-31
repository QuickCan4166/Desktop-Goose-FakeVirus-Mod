"""
goose_watcher.py — Launched silently by GooseChaos_Pipe.py at Stage 6.
Runs hidden in the background. Watches for GooseDesktop.exe to die,
then runs the full finale with a fullscreen glitch overlay + looping MP3.

Usage (auto): python goose_watcher.py <goose_pid> <original_wallpaper> <mp3_path_or_NONE>
"""

import sys, os, time, subprocess, ctypes, random, threading
from pathlib import Path

# ── Hide own console window immediately ──────────────────────────────────────
ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# ── Args ─────────────────────────────────────────────────────────────────────
if len(sys.argv) < 4:
    sys.exit(1)

GOOSE_PID          = int(sys.argv[1])
ORIGINAL_WALLPAPER = sys.argv[2]
MP3_PATH           = sys.argv[3] if sys.argv[3] != "NONE" else None
TEMP               = Path(os.environ.get("TEMP", "."))

# ── Dependencies ──────────────────────────────────────────────────────────────
try:
    from PIL import Image, ImageDraw, ImageFont
    import win32gui, win32con, win32api, win32process
    from playsound import playsound
except ImportError as e:
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def is_pid_running(pid):
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW
        ).decode()
        return str(pid) in out
    except Exception:
        return False

def set_wallpaper(path):
    ctypes.windll.user32.SystemParametersInfoW(0x0014, 0, path, 3)

def screen_size():
    return (ctypes.windll.user32.GetSystemMetrics(0),
            ctypes.windll.user32.GetSystemMetrics(1))

def set_solid_wallpaper(r, g, b):
    sw, sh = screen_size()
    img = Image.new("RGB", (sw, sh), (r, g, b))
    out = str(TEMP / "goose_watcher_solid.png")
    img.save(out)
    set_wallpaper(out)

def make_text_wallpaper(lines, bg=(0,0,0)):
    sw, sh = screen_size()
    img = Image.new("RGB", (sw, sh), bg)
    draw = ImageDraw.Draw(img)
    try:
        font_big = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 72)
        font_med = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 36)
    except:
        font_big = font_med = ImageFont.load_default()
    total_h = len(lines) * 100
    start_y = (sh - total_h) // 2
    for i, (text, color, big) in enumerate(lines):
        font = font_big if big else font_med
        bb = draw.textbbox((0,0), text, font=font)
        tw = bb[2] - bb[0]
        draw.text(((sw-tw)//2, start_y + i*100), text, fill=color, font=font)
    out = str(TEMP / "goose_watcher_text.png")
    img.save(out)
    return out

def show_taskbar():
    try:
        hwnd = win32gui.FindWindow("Shell_TrayWnd", None)
        if hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, 0,0,0,0,
                win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_SHOWWINDOW)
    except: pass

# ─────────────────────────────────────────────────────────────────────────────
#  FULLSCREEN GLITCH OVERLAY
#  A layered topmost window we draw random glitch rectangles onto every frame.
# ─────────────────────────────────────────────────────────────────────────────

_overlay_hwnd  = None
_overlay_active = False
_overlay_thread = None

GLITCH_COLORS = [
    (255, 0,   0),    # red
    (255, 255, 255),  # white
    (0,   0,   0),    # black
    (0,   255, 0),    # matrix green
    (0,   0,   255),  # blue
    (255, 0,   255),  # magenta
    (255, 255, 0),    # yellow
]

def _overlay_wnd_proc(hwnd, msg, wparam, lparam):
    if msg == win32con.WM_PAINT:
        try:
            sw, sh = screen_size()
            hdc, ps = win32gui.BeginPaint(hwnd)
            # Draw 30–60 random glitch rectangles each paint
            for _ in range(random.randint(30, 60)):
                x  = random.randint(0, sw)
                y  = random.randint(0, sh)
                w  = random.randint(5, sw // 2)
                h  = random.randint(1, 12)
                c  = random.choice(GLITCH_COLORS)
                br = win32gui.CreateSolidBrush(win32api.RGB(*c))
                win32gui.FillRect(hdc, (x, y, x+w, y+h), br)
                win32gui.DeleteObject(br)
            win32gui.EndPaint(hwnd, ps)
        except Exception:
            pass
        return 0
    if msg == win32con.WM_DESTROY:
        win32gui.PostQuitMessage(0)
        return 0
    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

def _overlay_loop():
    global _overlay_hwnd
    sw, sh = screen_size()
    class_name = "GooseGlitchOverlay"
    wc = win32gui.WNDCLASS()
    wc.hInstance    = win32api.GetModuleHandle(None)
    wc.lpszClassName = class_name
    wc.lpfnWndProc  = _overlay_wnd_proc
    wc.hbrBackground = win32gui.CreateSolidBrush(win32api.RGB(0,0,0))
    try: win32gui.RegisterClass(wc)
    except: pass

    # WS_EX_LAYERED + WS_EX_TRANSPARENT lets mouse clicks fall through
    _overlay_hwnd = win32gui.CreateWindowEx(
        win32con.WS_EX_TOPMOST | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_TOOLWINDOW,
        class_name, "",
        win32con.WS_POPUP | win32con.WS_VISIBLE,
        0, 0, sw, sh,
        0, 0, wc.hInstance, None)

    # 60% opacity so wallpaper glitches show through underneath
    ctypes.windll.user32.SetLayeredWindowAttributes(_overlay_hwnd, 0, 153, 2)  # LWA_ALPHA
    win32gui.UpdateWindow(_overlay_hwnd)

    # Pump WM_PAINT rapidly by calling InvalidateRect in a tight loop
    import win32event
    while _overlay_active:
        win32gui.InvalidateRect(_overlay_hwnd, None, True)
        # Process pending messages
        try:
            msg = win32gui.PeekMessage(_overlay_hwnd, 0, 0, win32con.PM_REMOVE)
            if msg and msg[1][1]:
                win32gui.TranslateMessage(msg[1])
                win32gui.DispatchMessage(msg[1])
        except Exception:
            pass
        time.sleep(0.033)   # ~30 fps glitch rate

    try:
        win32gui.DestroyWindow(_overlay_hwnd)
    except Exception:
        pass
    _overlay_hwnd = None

def start_overlay():
    global _overlay_active, _overlay_thread
    _overlay_active = True
    _overlay_thread = threading.Thread(target=_overlay_loop, daemon=True)
    _overlay_thread.start()

def stop_overlay():
    global _overlay_active
    _overlay_active = False
    if _overlay_thread:
        _overlay_thread.join(timeout=1.0)

# ─────────────────────────────────────────────────────────────────────────────
#  WALLPAPER CHAOS  (cycles behind the overlay)
# ─────────────────────────────────────────────────────────────────────────────

CHAOS_VARIANTS = [
    ((0,0,0),   "⚠  SYSTEM INTEGRITY FAILURE  ⚠", "0xDEADBEEF | GOOSE_FAULT"),
    ((10,0,20), "⚠  CRITICAL KERNEL PANIC  ⚠",    "0xC000021A | HONK_EXCEPTION"),
    ((20,0,0),  "⚠  VIRUS DETECTED  ⚠",           "0xBAD_G00SE | DATA_LOSS"),
    ((0,10,0),  "⚠  MEMORY CORRUPTION  ⚠",        "0xDEADC0DE | FOWL_ERROR"),
]

def make_chaos_wallpaper(variant=0):
    bg, title, code = CHAOS_VARIANTS[variant % len(CHAOS_VARIANTS)]
    sw, sh = screen_size()
    img = Image.new("RGB", (sw, sh), bg)
    draw = ImageDraw.Draw(img)
    for _ in range(500):
        x, y = random.randint(0,sw), random.randint(0,sh)
        w, h = random.randint(10,300), random.randint(1,6)
        c = random.choice([(0,255,0),(255,0,0),(0,180,255),(255,255,0),(255,255,255)])
        draw.rectangle([x,y,x+w,y+h], fill=c)
    try:
        fb = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 52)
        fs = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 18)
    except:
        fb = fs = ImageFont.load_default()
    for text, color, font, y in [
        (title, (255,0,0), fb, sh//2-100),
        (code,  (0,255,0), fs, sh//2+60),
    ]:
        bb = draw.textbbox((0,0), text, font=font)
        tw = bb[2]-bb[0]
        draw.text(((sw-tw)//2, y), text, fill=color, font=font)
    out = str(TEMP / f"goose_watcher_chaos_{variant}.png")
    img.save(out)
    return out

# ─────────────────────────────────────────────────────────────────────────────
#  AUDIO  — tight loop for short MP3s
# ─────────────────────────────────────────────────────────────────────────────

_audio_playing = False

def audio_loop():
    """Loop the MP3 continuously by replaying it immediately when it ends."""
    while _audio_playing:
        try:
            playsound(MP3_PATH, block=True)
        except Exception:
            time.sleep(0.05)

def start_audio():
    global _audio_playing
    if not MP3_PATH:
        return
    _audio_playing = True
    threading.Thread(target=audio_loop, daemon=True).start()

def stop_audio():
    global _audio_playing
    _audio_playing = False
    try:
        ctypes.windll.winmm.mciSendStringW("stop all", None, 0, None)
        ctypes.windll.winmm.mciSendStringW("close all", None, 0, None)
    except: pass

# ─────────────────────────────────────────────────────────────────────────────
#  FINALE SEQUENCE
# ─────────────────────────────────────────────────────────────────────────────

def finale():
    # ── 1. Black screen ──────────────────────────────────────────────────────
    set_solid_wallpaper(0, 0, 0)
    time.sleep(1.5)

    # ── 2. Red warning text ──────────────────────────────────────────────────
    wp = make_text_wallpaper([
        ("You've made the gravest mistake,", (180, 0, 0), False),
        ("now you pay the gravest price.",   (255, 0, 0), True),
    ])
    set_wallpaper(wp)
    time.sleep(3.0)

    # ── 3. Glitch storm — overlay + wallpaper cycling + MP3 ──────────────────
    start_audio()
    start_overlay()

    storm_end = time.time() + 8.0
    variant   = 0
    rbw       = [(255,0,0),(0,0,0),(255,255,255)]
    while time.time() < storm_end:
        # Rapidly cycle the wallpaper underneath the overlay
        action = random.choices(["solid","chaos"], weights=[40,60])[0]
        if action == "solid":
            r, g, b = random.choice(rbw)
            set_solid_wallpaper(r, g, b)
            time.sleep(random.uniform(0.04, 0.10))
        else:
            variant = (variant + 1) % len(CHAOS_VARIANTS)
            set_wallpaper(make_chaos_wallpaper(variant))
            time.sleep(random.uniform(0.06, 0.12))

    stop_overlay()
    stop_audio()

    # ── 4. "Die." screen ─────────────────────────────────────────────────────
    die_wp = make_text_wallpaper([("Die.", (255, 0, 0), True)])
    set_wallpaper(die_wp)
    time.sleep(3.0)

    # ── 5. Restore then shutdown ─────────────────────────────────────────────
    set_solid_wallpaper(0, 0, 0)
    time.sleep(0.5)
    if ORIGINAL_WALLPAPER and ORIGINAL_WALLPAPER != "NONE":
        try: set_wallpaper(ORIGINAL_WALLPAPER)
        except: pass
    show_taskbar()
    time.sleep(0.5)

    subprocess.call(["shutdown", "/s", "/t", "0", "/f"],
                    creationflags=subprocess.CREATE_NO_WINDOW)
    sys.exit(0)

# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY — poll for goose death
# ─────────────────────────────────────────────────────────────────────────────

while True:
    time.sleep(0.5)
    if not is_pid_running(GOOSE_PID):
        finale()
        break
