"""
GooseChaos_Pipe.py  —  6-Stage Virus Goose
-------------------------------------------
Stage 1: Warning popup + taskbar vanishes
Stage 2: Wallpaper chaos + flickers + popups + fake CMD scan
Stage 3: Icons flee cursor + windows minimize/maximize randomly
Stage 4: Intense chaos + screen color inversion + threats
Stage 5: Seizure flash burst + fake reboot notepad
Stage 6: Task Manager opens + taunting popup + if goose is killed via
         Task Manager → black screen → red warning text → RBW glitch
         storm + glitchy MP3 → "Die" → real PC shutdown

⚠ SEIZURE WARNING: Stage 6 contains rapid full-screen flashing.
  Do not use on anyone with photosensitive epilepsy.

Run BEFORE Desktop Goose. Press ESC at any time to revert and exit early.
MP3 path: <GooseDir>\\assets\\mods\\virus\\  (any .mp3 in that folder)

pip install pyautogui keyboard Pillow pywin32 playsound==1.2.2
"""

import os, sys, time, random, threading, ctypes, subprocess, math
from pathlib import Path

# ── Dependency check ──────────────────────────────────────────────────────────
missing = []
for pkg, imp in [("pyautogui","pyautogui"), ("keyboard","keyboard"),
                 ("Pillow","PIL"),           ("pywin32","win32gui"),
                 ("playsound","playsound")]:
    try: __import__(imp)
    except ImportError: missing.append(pkg)
if missing:
    print(f"[!] Missing: pip install {' '.join(missing)}")
    input("Press Enter to exit..."); sys.exit(1)

import pyautogui, keyboard
from PIL import Image, ImageDraw, ImageFont
from playsound import playsound
import win32gui, win32con, win32api
import win32pipe, win32file, pywintypes

pyautogui.FAILSAFE = False
_audio_thread = None

TEMP      = Path(os.environ.get("TEMP", "."))
PIPE_NAME = r"\\.\pipe\GooseChaosControl"

# ── Locate the MP3 ────────────────────────────────────────────────────────────
def find_mp3():
    """Find any .mp3 - checks hardcoded path first, then common locations."""
    # Check the exact known path first
    known_folder = Path(r"C:\Users\myabn\Documents\Projects\Desktop Goose Virus Mod\DesktopGoose v0.31\Assets\Mods\Virus")
    if known_folder.exists():
        mp3s = list(known_folder.glob("*.mp3"))
        if mp3s:
            return str(mp3s[0])

    # Fallback: scan common locations with all capitalisation variants
    base_candidates = [
        Path(os.path.expanduser("~")) / "Documents" / "Games" / "DesktopGoose v0.31",
        Path(os.path.expanduser("~")) / "Documents" / "Projects" / "Desktop Goose Virus Mod" / "DesktopGoose v0.31",
        Path(r"C:\Program Files (x86)\Desktop Goose"),
        Path(r"C:\Program Files\Desktop Goose"),
    ]
    subfolders = [
        Path("Assets") / "Mods" / "Virus",
        Path("assets") / "mods" / "virus",
    ]
    for base in base_candidates:
        for sub in subfolders:
            folder = base / sub
            if folder.exists():
                mp3s = list(folder.glob("*.mp3"))
                if mp3s:
                    return str(mp3s[0])
    return None

MP3_PATH = find_mp3()
if MP3_PATH:
    print(f"[✓] Found MP3: {MP3_PATH}")
else:
    print("[!] No MP3 found in assets/mods/virus — stage 6 will run silently")

state = {
    "running":            True,
    "stage":              0,
    "original_wallpaper": "",
    "chaos_wallpaper":    None,
    "wallpaper_applied":  False,
    "icon_flee_active":   False,
    "taskbar_hidden":     False,
    "colors_inverted":    False,
    "goose_pid":          None,   # tracked so we know if it gets killed
    "watching_for_kill":  False,
}

# ─────────────────────────────────────────────────────────────────────────────
#  WALLPAPER / SCREEN HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_wallpaper():
    buf = ctypes.create_unicode_buffer(512)
    ctypes.windll.user32.SystemParametersInfoW(0x0073, len(buf), buf, 0)
    return buf.value

def set_wallpaper(path):
    ctypes.windll.user32.SystemParametersInfoW(0x0014, 0, path, 3)

def set_solid_wallpaper(r, g, b):
    """Generate and apply a solid-colour wallpaper."""
    sw, sh = pyautogui.size()
    img = Image.new("RGB", (sw, sh), (r, g, b))
    out = str(TEMP / "goose_solid_bg.png")
    img.save(out)
    set_wallpaper(out)
    return out

WALLPAPER_VARIANTS = [
    ((0,0,0),   "⚠  SYSTEM INTEGRITY FAILURE  ⚠", "All user data is being encrypted...",      "0xDEADBEEF | GOOSE_FAULT"),
    ((10,0,20), "⚠  CRITICAL KERNEL PANIC  ⚠",    "Filesystem corruption detected...",        "0xC000021A | HONK_EXCEPTION"),
    ((20,0,0),  "⚠  VIRUS DETECTED  ⚠",           "HONKVIRUS.EXE spreading to all drives...", "0xBAD_G00SE | DATA_LOSS"),
    ((0,10,0),  "⚠  MEMORY CORRUPTION  ⚠",        "RAM modules 1-4 failing...",               "0xDEADC0DE | FOWL_ERROR"),
]

def make_chaos_wallpaper(variant=0):
    v = WALLPAPER_VARIANTS[variant % len(WALLPAPER_VARIANTS)]
    bg, title, subtitle, code = v
    sw, sh = pyautogui.size()
    img = Image.new("RGB", (sw, sh), bg)
    draw = ImageDraw.Draw(img)
    for _ in range(500):
        x, y = random.randint(0,sw), random.randint(0,sh)
        w, h = random.randint(10,300), random.randint(1,6)
        c = random.choice([(0,255,0),(255,0,0),(0,180,255),(255,255,0),(255,255,255)])
        draw.rectangle([x,y,x+w,y+h], fill=c)
    try:
        fb = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 52)
        fm = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 28)
        fs = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 18)
    except:
        fb = fm = fs = ImageFont.load_default()
    lines = [
        (title,    (255,0,0),     fb, sh//2-140),
        (subtitle, (255,255,0),   fm, sh//2-60),
        ("Do NOT turn off your computer",  (200,200,200), fm, sh//2),
        (f"ERROR CODE: {code}",            (0,255,0),     fs, sh//2+60),
        ("Sending data to GOOSE.GOV...",   (180,180,180), fs, sh//2+90),
    ]
    for text, color, font, y in lines:
        bb = draw.textbbox((0,0), text, font=font)
        tw = bb[2]-bb[0]
        draw.text(((sw-tw)//2, y), text, fill=color, font=font)
    out = str(TEMP / f"goose_chaos_bg_{variant}.png")
    img.save(out)
    return out

def make_text_wallpaper(lines, bg=(0,0,0)):
    """Make a full-screen wallpaper with centred text lines."""
    sw, sh = pyautogui.size()
    img = Image.new("RGB", (sw, sh), bg)
    draw = ImageDraw.Draw(img)
    try:
        font_big = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 72)
        font_med = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 36)
    except:
        font_big = font_med = ImageFont.load_default()
    total_h = len(lines) * 90
    start_y = (sh - total_h) // 2
    for i, (text, color, big) in enumerate(lines):
        font = font_big if big else font_med
        bb = draw.textbbox((0,0), text, font=font)
        tw = bb[2]-bb[0]
        draw.text(((sw-tw)//2, start_y + i*90), text, fill=color, font=font)
    out = str(TEMP / "goose_text_bg.png")
    img.save(out)
    return out

# ─────────────────────────────────────────────────────────────────────────────
#  POPUP / FLASH / MOUSE / TASKBAR / INVERSION HELPERS
# ─────────────────────────────────────────────────────────────────────────────

STAGE1_MESSAGES = [
    ("🪿 WARNING", "I have been watching you.\n\nDo not click me again."),
    ("🪿 NOTICE",  "This is your only warning.\n\nStep away from the goose."),
]
STAGE2_POPUPS = [
    ("SYSTEM WARNING",  "Unauthorized access detected.\nInitiating countermeasures..."),
    ("DISK ERROR",      "C:\\ drive failure imminent.\nBacking up to goose.gov..."),
    ("FIREWALL BREACH", "Connection from GOOSE.LOCAL\nTransferring files to remote server..."),
]
STAGE4_POPUPS = [
    ("GOOSE PROTOCOL ENGAGED", "Your resistance is futile.\nAll your files belong to goose."),
    ("FINAL WARNING",          "You have angered the goose.\nYour computer will be destroyed."),
    ("IMMINENT DELETION",      "Deleting System32...\n[████████████░░] 90%"),
    ("GOOSE.EXE",              "HONK HONK HONK HONK HONK\nHONK HONK HONK HONK HONK\nHONK"),
    ("CRITICAL THREAT",        "The goose has your IP address.\nThe goose knows where you live."),
]
FAKE_REBOOT_LINES = [
    "Saving your files... just kidding.",
    "Uninstalling everything...",
    "Sending browser history to goose.gov...",
    "FORMAT C: /FS:GOOSE /Q",
    "rm -rf / --no-preserve-root",
    "Encrypting Documents... [██████████] 100%",
    ".", "..", "...", "HONK",
]
FAKE_SCAN_LINES = [
    "Initializing GOOSE_SCAN v6.6.6...",
    "Scanning C:\\Users\\... [OK]",
    "Scanning C:\\Windows\\System32\\... [OK]",
    "Scanning C:\\Users\\AppData\\... [WARNING]",
    "Found: HONKVIRUS.EXE in C:\\Users\\Downloads\\",
    "Found: GOOSE_TROJAN.DLL in C:\\Windows\\System32\\",
    "Encrypting personal files... [████████░░] 80%",
    "Contacting GOOSE.GOV...",
    "Uploading browser history... [DONE]",
    "Uploading passwords... [DONE]",
    "SCAN COMPLETE. 847 threats found.",
    "Recommended action: surrender to the goose.",
]

def show_popup(title, msg, flags=None):
    if flags is None:
        flags = win32con.MB_ICONERROR | win32con.MB_OK | win32con.MB_TOPMOST
    threading.Thread(
        target=lambda: ctypes.windll.user32.MessageBoxW(0, msg, title, flags),
        daemon=True).start()

def do_flash(duration=0.12, color=None):
    try:
        sw, sh = pyautogui.size()
        if color is None:
            color = random.choice([(255,0,0),(255,255,0),(0,0,0),(255,255,255),(0,100,255)])
        class_name = "GooseFlash"
        wc = win32gui.WNDCLASS()
        wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = class_name
        def wnd_proc(hwnd, msg, wparam, lparam):
            if msg == win32con.WM_DESTROY:
                win32gui.PostQuitMessage(0)
            return 0
        wc.lpfnWndProc = wnd_proc
        wc.hbrBackground = win32gui.CreateSolidBrush(win32api.RGB(*color))
        try: win32gui.RegisterClass(wc)
        except: pass
        hwnd = win32gui.CreateWindowEx(
            win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW,
            class_name, "", win32con.WS_POPUP | win32con.WS_VISIBLE,
            0, 0, sw, sh, 0, 0, wc.hInstance, None)
        win32gui.UpdateWindow(hwnd)
        time.sleep(duration)
        win32gui.DestroyWindow(hwnd)
    except Exception as e:
        print(f"  [flash] {e}")

def do_mouse_chaos(seconds=1.5):
    sw, sh = pyautogui.size()
    end = time.time() + seconds
    while time.time() < end and state["running"]:
        pyautogui.moveTo(random.randint(80,sw-80), random.randint(80,sh-80), duration=0.05)

def hide_taskbar():
    try:
        hwnd = win32gui.FindWindow("Shell_TrayWnd", None)
        if hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
            state["taskbar_hidden"] = True
    except Exception as e:
        print(f"  [taskbar hide] {e}")

def show_taskbar():
    try:
        hwnd = win32gui.FindWindow("Shell_TrayWnd", None)
        if hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, 0,0,0,0,
                win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_SHOWWINDOW)
            state["taskbar_hidden"] = False
    except Exception as e:
        print(f"  [taskbar show] {e}")

def fake_cmd_scan():
    try:
        subprocess.Popen(["cmd.exe","/K","echo GOOSE SECURITY SCANNER v6.6.6"],
                         creationflags=subprocess.CREATE_NEW_CONSOLE)
        time.sleep(1.0)
        hwnd = None
        for _ in range(10):
            hwnd = win32gui.FindWindow("ConsoleWindowClass", None)
            if hwnd: break
            time.sleep(0.2)
        if hwnd:
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.3)
        for line in FAKE_SCAN_LINES:
            if not state["running"]: break
            pyautogui.typewrite(f"echo {line}", interval=0.02)
            pyautogui.press("enter")
            time.sleep(random.uniform(0.2, 0.6))
    except Exception as e:
        print(f"  [cmd scan] {e}")

def window_chaos():
    try:
        windows = []
        def collect(hwnd, _):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                cls = win32gui.GetClassName(hwnd)
                if cls not in ("Shell_TrayWnd","Progman","WorkerW","GooseFlash"):
                    windows.append(hwnd)
        win32gui.EnumWindows(collect, None)
        if not windows: return
        targets = random.sample(windows, min(3, len(windows)))
        for hwnd in targets:
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE if random.random()>0.5 else win32con.SW_MAXIMIZE)
                time.sleep(0.1)
            except: pass
        time.sleep(random.uniform(1.0, 2.5))
        for hwnd in targets:
            try: win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            except: pass
    except Exception as e:
        print(f"  [window chaos] {e}")

def invert_colors():
    try:
        class HIGHCONTRAST(ctypes.Structure):
            _fields_ = [("cbSize",ctypes.c_uint),("dwFlags",ctypes.c_uint),("lpszDefaultScheme",ctypes.c_wchar_p)]
        hc = HIGHCONTRAST(); hc.cbSize = ctypes.sizeof(HIGHCONTRAST)
        ctypes.windll.user32.SystemParametersInfoW(0x0042, ctypes.sizeof(HIGHCONTRAST), ctypes.byref(hc), 0)
        hc.dwFlags |= 0x1
        ctypes.windll.user32.SystemParametersInfoW(0x0043, 0, ctypes.byref(hc), 0)
        state["colors_inverted"] = True
        time.sleep(random.uniform(3,6))
        hc.dwFlags &= ~0x1
        ctypes.windll.user32.SystemParametersInfoW(0x0043, 0, ctypes.byref(hc), 0)
        state["colors_inverted"] = False
    except Exception as e:
        print(f"  [invert] {e}")

def restore_colors():
    if not state["colors_inverted"]: return
    try:
        class HIGHCONTRAST(ctypes.Structure):
            _fields_ = [("cbSize",ctypes.c_uint),("dwFlags",ctypes.c_uint),("lpszDefaultScheme",ctypes.c_wchar_p)]
        hc = HIGHCONTRAST(); hc.cbSize = ctypes.sizeof(HIGHCONTRAST)
        ctypes.windll.user32.SystemParametersInfoW(0x0042, ctypes.sizeof(HIGHCONTRAST), ctypes.byref(hc), 0)
        hc.dwFlags &= ~0x1
        ctypes.windll.user32.SystemParametersInfoW(0x0043, 0, ctypes.byref(hc), 0)
        state["colors_inverted"] = False
    except Exception as e:
        print(f"  [restore colors] {e}")

def seizure_flash_burst(count=20):
    colors = [(255,0,0),(255,255,255),(0,0,0),(255,255,0),(0,0,255),(255,0,255)]
    for i in range(count):
        do_flash(duration=0.04, color=colors[i % len(colors)])
        time.sleep(0.03)

def start_icon_flee():
    if state["icon_flee_active"]: return
    state["icon_flee_active"] = True
    def loop():
        print("  [icons] flee loop started")
        while state["running"] and state["icon_flee_active"]:
            time.sleep(0.05)
        print("  [icons] flee loop ended")
    threading.Thread(target=loop, daemon=True).start()

def stop_icon_flee():
    state["icon_flee_active"] = False

# ─────────────────────────────────────────────────────────────────────────────
#  STAGE 6 — THE FINALE
# ─────────────────────────────────────────────────────────────────────────────

def get_goose_pid():
    """Return the PID of GooseDesktop.exe if it's running, else None."""
    for name in ["GooseDesktop.exe", "Desktop Goose.exe"]:
        try:
            out = subprocess.check_output(
                ["tasklist","/FI",f"IMAGENAME eq {name}","/FO","CSV","/NH"],
                stderr=subprocess.DEVNULL).decode()
            for line in out.strip().splitlines():
                parts = line.strip('"').split('","')
                if len(parts) >= 2:
                    try: return int(parts[1])
                    except: pass
        except Exception:
            pass
    return None

def is_pid_running(pid):
    try:
        out = subprocess.check_output(
            ["tasklist","/FI",f"PID eq {pid}","/FO","CSV","/NH"],
            stderr=subprocess.DEVNULL).decode()
        return str(pid) in out
    except Exception:
        return False

def watch_for_goose_kill():
    """Launch goose_watcher.py as a completely separate process."""
    pid = get_goose_pid()
    if not pid:
        print("  [watch] Could not find Goose PID — retrying for 10s...")
        for _ in range(20):
            time.sleep(0.5)
            pid = get_goose_pid()
            if pid: break
    if not pid:
        print("  [watch] Still no PID found, finale won't trigger")
        return

    state["goose_pid"] = pid
    print(f"  [watch] Goose PID: {pid} — launching watcher process")

    # Find goose_watcher.py next to this script
    watcher_path = Path(__file__).parent / "goose_watcher.py"
    mp3_arg = MP3_PATH if MP3_PATH else "NONE"
    wp_arg  = state["original_wallpaper"] if state["original_wallpaper"] else "NONE"

    try:
        subprocess.Popen(
            [sys.executable, str(watcher_path), str(pid), wp_arg, mp3_arg],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        print("  [watch] Watcher process launched — it will survive goose dying")
    except Exception as e:
        print(f"  [watch] Failed to launch watcher: {e}")

def play_mp3():
    global _audio_thread
    if not MP3_PATH:
        print("  [audio] No MP3 found, skipping")
        return
    try:
        # playsound is blocking, so run it in a daemon thread on loop
        def _loop():
            while state.get("_audio_playing", True):
                try: playsound(MP3_PATH)
                except: break
        state["_audio_playing"] = True
        _audio_thread = threading.Thread(target=_loop, daemon=True)
        _audio_thread.start()
        print(f"  [audio] Playing {MP3_PATH}")
    except Exception as e:
        print(f"  [audio] {e}")

def stop_mp3():
    state["_audio_playing"] = False
    # playsound has no stop API — killing via Windows MCI
    try:
        import ctypes
        ctypes.windll.winmm.mciSendStringW("stop all", None, 0, None)
        ctypes.windll.winmm.mciSendStringW("close all", None, 0, None)
    except Exception:
        pass

def finale_sequence():
    """
    The full Stage 6 death sequence:
    1. Black screen
    2. Red warning text wallpaper
    3. Glitchy RBW flash storm + MP3
    4. "Die" wallpaper
    5. Real shutdown
    """
    print("[FINALE] Starting death sequence")
    state["running"] = False
    stop_icon_flee()
    restore_colors()

    # ── 1. Snap to black ─────────────────────────────────────────────────────
    set_solid_wallpaper(0, 0, 0)
    time.sleep(1.5)

    # ── 2. Red warning text ──────────────────────────────────────────────────
    warning_wp = make_text_wallpaper([
        ("You've made the gravest mistake,", (180,0,0), False),
        ("now you pay the gravest price.",   (255,0,0), True),
    ], bg=(0,0,0))
    set_wallpaper(warning_wp)
    time.sleep(3.0)

    # ── 3. Glitch storm + MP3 ────────────────────────────────────────────────
    play_mp3()

    rbw_colors = [(255,0,0), (0,0,0), (255,255,255)]
    glitch_end = time.time() + 8.0   # 8 seconds of chaos
    variant = 0
    while time.time() < glitch_end:
        # Alternate between full-screen flash and chaos wallpaper
        action = random.choices(["flash","flash","wallpaper"], weights=[60,30,10])[0]
        if action == "flash":
            color = rbw_colors[random.randint(0, len(rbw_colors)-1)]
            do_flash(duration=random.uniform(0.03, 0.10), color=color)
            time.sleep(random.uniform(0.02, 0.06))
        else:
            variant = (variant+1) % len(WALLPAPER_VARIANTS)
            wp = make_chaos_wallpaper(variant)
            set_wallpaper(wp)
            time.sleep(0.08)

    # ── 4. "Die" screen ──────────────────────────────────────────────────────
    stop_mp3()
    die_wp = make_text_wallpaper([
        ("Die.", (255,0,0), True),
    ], bg=(0,0,0))
    set_wallpaper(die_wp)
    time.sleep(3.0)

    # ── 5. Black out then shut down ──────────────────────────────────────────
    set_solid_wallpaper(0, 0, 0)
    time.sleep(1.0)

    # Restore wallpaper BEFORE shutdown so it's fine on reboot
    if state["original_wallpaper"]:
        try:
            set_wallpaper(state["original_wallpaper"])
        except Exception:
            pass
    show_taskbar()

    print("[FINALE] Shutting down...")
    # /s = shutdown, /t 0 = immediately, /f = force close apps
    subprocess.call(["shutdown","/s","/t","0","/f"])
    os._exit(0)

def run_stage_6():
    """Stage 6: Open Task Manager + taunting popup, watch for Goose kill."""
    print("[STAGE 6] Finale armed")

    # Open Task Manager via ShellExecute so it gets elevation automatically
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", "taskmgr.exe", None, None, 1)
        time.sleep(1.2)
    except Exception as e:
        print(f"  [taskmgr] {e}")
        # Fallback — try without elevation
        try:
            subprocess.Popen(["taskmgr.exe"])
        except Exception as e2:
            print(f"  [taskmgr fallback] {e2}")

    # Taunting popup right next to it
    show_popup(
        "🪿 go on, close me =)",
        "I dare you.\n\nOpen Task Manager.\nFind 'GooseDesktop'.\nEnd the task.\n\nI'll be waiting. =)",
        win32con.MB_ICONQUESTION | win32con.MB_OK | win32con.MB_TOPMOST
    )

    # Start watching for the goose process to be killed
    state["watching_for_kill"] = True
    threading.Thread(target=watch_for_goose_kill, daemon=True).start()

# ─────────────────────────────────────────────────────────────────────────────
#  STAGES 1–5
# ─────────────────────────────────────────────────────────────────────────────

def run_stage_1():
    print("[STAGE 1] Warning + taskbar hide")
    title, msg = random.choice(STAGE1_MESSAGES)
    show_popup(title, msg, win32con.MB_ICONWARNING | win32con.MB_OK | win32con.MB_TOPMOST)
    threading.Thread(target=hide_taskbar, daemon=True).start()

def run_stage_2():
    print("[STAGE 2] Chaos begins")
    wp = make_chaos_wallpaper(0)
    state["chaos_wallpaper"] = wp
    set_wallpaper(wp)
    state["wallpaper_applied"] = True
    threading.Thread(target=fake_cmd_scan, daemon=True).start()
    def loop():
        variant = 0
        while state["running"] and state["stage"] == 2:
            time.sleep(random.uniform(4,10))
            if not state["running"] or state["stage"] != 2: break
            action = random.choice(["flash","popup","wallpaper"])
            if action == "flash": do_flash(duration=random.uniform(0.08,0.2))
            elif action == "popup":
                t,m = random.choice(STAGE2_POPUPS); show_popup(t,m)
            elif action == "wallpaper":
                variant = (variant+1) % len(WALLPAPER_VARIANTS)
                wp = make_chaos_wallpaper(variant)
                state["chaos_wallpaper"] = wp; set_wallpaper(wp)
    threading.Thread(target=loop, daemon=True).start()

def run_stage_3():
    print("[STAGE 3] Icons flee + window chaos")
    start_icon_flee()
    def wcloop():
        while state["running"] and state["stage"] == 3:
            time.sleep(random.uniform(4,8))
            if not state["running"] or state["stage"] != 3: break
            threading.Thread(target=window_chaos, daemon=True).start()
    threading.Thread(target=wcloop, daemon=True).start()
    def wploop():
        variant = 1
        while state["running"] and state["stage"] == 3:
            time.sleep(random.uniform(6,12))
            if not state["running"] or state["stage"] != 3: break
            variant = (variant+1) % len(WALLPAPER_VARIANTS)
            wp = make_chaos_wallpaper(variant)
            state["chaos_wallpaper"] = wp; set_wallpaper(wp); do_flash(0.1)
    threading.Thread(target=wploop, daemon=True).start()

def run_stage_4():
    print("[STAGE 4] INTENSE CHAOS + inversion")
    threading.Thread(target=invert_colors, daemon=True).start()
    def loop():
        while state["running"] and state["stage"] == 4:
            time.sleep(random.uniform(1.5,5))
            if not state["running"] or state["stage"] != 4: break
            action = random.choices(
                ["flash","flash","popup","mouse","wallpaper","invert"],
                weights=[25,25,20,15,5,10])[0]
            if action == "flash":
                for _ in range(random.randint(1,4)):
                    do_flash(duration=random.uniform(0.05,0.15)); time.sleep(0.05)
            elif action == "popup": t,m=random.choice(STAGE4_POPUPS); show_popup(t,m)
            elif action == "mouse": threading.Thread(target=do_mouse_chaos,args=(1.0,),daemon=True).start()
            elif action == "wallpaper":
                v=random.randint(0,len(WALLPAPER_VARIANTS)-1)
                wp=make_chaos_wallpaper(v); state["chaos_wallpaper"]=wp; set_wallpaper(wp)
            elif action == "invert": threading.Thread(target=invert_colors,daemon=True).start()
    threading.Thread(target=loop, daemon=True).start()
    def threats():
        time.sleep(1)
        show_popup("🪿 GOOSE FINAL WARNING",
            "You have made a grave mistake.\n\nThe goose is now in control.\n\nPrepare for termination.",
            win32con.MB_ICONSTOP|win32con.MB_OK|win32con.MB_TOPMOST)
        time.sleep(3)
        if state["running"] and state["stage"] == 4:
            show_popup("GOOSE.EXE — SYSTEM TAKEOVER",
                "Deleting System32...\nFormatting C:\\\nUploading everything to GOOSE.GOV\n\nThere is no escape.\n\nHONK.",
                win32con.MB_ICONSTOP|win32con.MB_OK|win32con.MB_TOPMOST)
    threading.Thread(target=threats, daemon=True).start()

def run_stage_5():
    print("[STAGE 5] Fake reboot")
    # Stage 5 no longer exits — it just does the fake notepad sequence
    # and then waits for the 6th click to arm stage 6
    seizure_flash_burst(count=25)
    try:
        subprocess.Popen(["notepad.exe"])
        time.sleep(1.2)
        hwnd = win32gui.FindWindow("Notepad", None)
        if hwnd:
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.3)
        for line in FAKE_REBOOT_LINES:
            pyautogui.typewrite(line+"\n", interval=0.04)
            time.sleep(0.3)
    except Exception as e:
        print(f"  [stage5 notepad] {e}")
    # Show a fake "rebooting" popup that dismisses after a moment
    show_popup("REBOOTING...",
        "Preparing to restart...\n\nActually... the goose has one more thing to say.\n\nClick me one more time. If you dare.",
        win32con.MB_ICONWARNING|win32con.MB_OK|win32con.MB_TOPMOST)

# ─────────────────────────────────────────────────────────────────────────────
#  STAGE DISPATCH
# ─────────────────────────────────────────────────────────────────────────────

STAGE_RUNNERS = {
    1: run_stage_1,
    2: run_stage_2,
    3: run_stage_3,
    4: run_stage_4,
    5: run_stage_5,
    6: run_stage_6,
}

def handle_stage(new_stage):
    state["stage"] = new_stage
    print(f"[→] Entering Stage {new_stage}")
    fn = STAGE_RUNNERS.get(new_stage)
    if fn:
        threading.Thread(target=fn, daemon=True).start()

# ─────────────────────────────────────────────────────────────────────────────
#  NAMED PIPE SERVER
# ─────────────────────────────────────────────────────────────────────────────

def pipe_server():
    while state["running"]:
        try:
            pipe = win32pipe.CreateNamedPipe(
                PIPE_NAME,
                win32pipe.PIPE_ACCESS_INBOUND,
                win32pipe.PIPE_TYPE_MESSAGE|win32pipe.PIPE_READMODE_MESSAGE|win32pipe.PIPE_WAIT,
                win32pipe.PIPE_UNLIMITED_INSTANCES,
                4096, 4096, 0, None)
            print("[pipe] Waiting for Desktop Goose mod to connect...")
            win32pipe.ConnectNamedPipe(pipe, None)
            print("[pipe] Mod connected!")
            while state["running"]:
                try:
                    result, data = win32file.ReadFile(pipe, 4096)
                    if result == 0 and data:
                        cmd = data.decode("utf-8").strip()
                        print(f"[pipe] Command: {cmd}")
                        if cmd.startswith("stage:"):
                            handle_stage(int(cmd.split(":")[1]))
                except pywintypes.error as e:
                    if e.args[0] == 109:
                        print("[pipe] Mod disconnected, reconnecting...")
                        break
                    raise
            win32file.CloseHandle(pipe)
        except Exception as e:
            if state["running"]:
                print(f"[pipe] Error: {e}"); time.sleep(2)

# ─────────────────────────────────────────────────────────────────────────────
#  RESTORE & EXIT  (ESC path — does NOT shut down the PC)
# ─────────────────────────────────────────────────────────────────────────────

def restore_all():
    print("[→] Restoring everything...")
    state["watching_for_kill"] = False
    stop_icon_flee()
    restore_colors()
    show_taskbar()
    stop_mp3()
    if state["original_wallpaper"]:
        try:
            set_wallpaper(state["original_wallpaper"])
            print("  ✓ Wallpaper restored")
        except Exception as e:
            print(f"  ✗ Wallpaper: {e}")
    for i in range(len(WALLPAPER_VARIANTS)):
        for p in [TEMP/f"goose_chaos_bg_{i}.png", TEMP/"goose_solid_bg.png",
                  TEMP/"goose_text_bg.png"]:
            try:
                if p.exists(): p.unlink()
            except: pass
    for proc in ["GooseDesktop.exe","Desktop Goose.exe","notepad.exe","cmd.exe"]:
        try:
            subprocess.call(["taskkill","/F","/IM",proc],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except: pass
    print("[✓] All done!")

def on_escape():
    if not state["running"]: return
    state["running"] = False
    restore_all()
    time.sleep(0.4)
    os._exit(0)

# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 57)
    print("  🪿  GooseChaos — 6 Stage Virus Edition")
    print("  Click the goose to escalate through stages")
    print("  Press  ESC  to revert everything & exit (no shutdown)")
    print("=" * 57)
    print()
    print("  Stage 1: Warning popup + taskbar vanishes")
    print("  Stage 2: Wallpaper + flickers + fake CMD scan")
    print("  Stage 3: Icons flee + windows go haywire")
    print("  Stage 4: Full chaos + screen color inversion")
    print("  Stage 5: Seizure flash burst + fake reboot")
    print("  Stage 6: Task Manager + if goose is killed →")
    print("           black screen → red warning → RBW glitch")
    print("           storm + MP3 → 'Die' → REAL SHUTDOWN")
    print()
    print("  ⚠ SEIZURE WARNING: Stages 5 & 6 contain rapid")
    print("    full-screen flashing. Use responsibly.")
    print()

    state["original_wallpaper"] = get_wallpaper()
    print(f"[✓] Saved wallpaper: {state['original_wallpaper']}")
    keyboard.add_hotkey("esc", on_escape, suppress=False)
    print("[✓] ESC hotkey registered")
    threading.Thread(target=pipe_server, daemon=True).start()

    try:
        while state["running"]:
            time.sleep(0.1)
    except KeyboardInterrupt:
        on_escape()

if __name__ == "__main__":
    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        print("[!] Tip: Run as Administrator for best results\n")
    main()
