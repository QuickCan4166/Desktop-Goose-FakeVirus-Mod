"""
GooseChaos_Pipe.py  —  5-Stage Virus Goose (Extended)
------------------------------------------------------
Stage 1: Warning popup + taskbar vanishes
Stage 2: Wallpaper chaos + flickers + popups + fake CMD scan window
Stage 3: Icons flee cursor + random windows minimize/maximize
Stage 4: Intense chaos + color inversion + threats
Stage 5: Seizure flash burst + fake reboot notepad + clean exit

Run BEFORE Desktop Goose. Press ESC at any time to revert and exit early.

pip install pyautogui keyboard Pillow pywin32
"""

import os, sys, time, random, threading, ctypes, subprocess, math
from pathlib import Path

# ── Dependency check ──────────────────────────────────────────────────────────
missing = []
for pkg, imp in [("pyautogui","pyautogui"),("keyboard","keyboard"),
                 ("Pillow","PIL"),("pywin32","win32gui")]:
    try: __import__(imp)
    except ImportError: missing.append(pkg)
if missing:
    print(f"[!] Missing: pip install {' '.join(missing)}")
    input("Press Enter to exit..."); sys.exit(1)

import pyautogui, keyboard
from PIL import Image, ImageDraw, ImageFont
import win32gui, win32con, win32api
import win32pipe, win32file, pywintypes

pyautogui.FAILSAFE = False

TEMP      = Path(os.environ.get("TEMP", "."))
PIPE_NAME = r"\\.\pipe\GooseChaosControl"

state = {
    "running":            True,
    "stage":              0,
    "original_wallpaper": "",
    "chaos_wallpaper":    None,
    "wallpaper_applied":  False,
    "icon_flee_active":   False,
    "taskbar_hidden":     False,
    "colors_inverted":    False,
}

# ─────────────────────────────────────────────────────────────────────────────
#  WALLPAPER HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_wallpaper():
    buf = ctypes.create_unicode_buffer(512)
    ctypes.windll.user32.SystemParametersInfoW(0x0073, len(buf), buf, 0)
    return buf.value

def set_wallpaper(path):
    ctypes.windll.user32.SystemParametersInfoW(0x0014, 0, path, 3)

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
        ("Do NOT turn off your computer",  (200,200,200), fm, sh//2+0),
        (f"ERROR CODE: {code}",            (0,255,0),     fs, sh//2+60),
        ("Sending data to GOOSE.GOV...",   (180,180,180), fs, sh//2+90),
    ]
    for text,color,font,y in lines:
        bb = draw.textbbox((0,0), text, font=font)
        tw = bb[2]-bb[0]
        draw.text(((sw-tw)//2, y), text, fill=color, font=font)
    out = str(TEMP / f"goose_chaos_bg_{variant}.png")
    img.save(out)
    return out

# ─────────────────────────────────────────────────────────────────────────────
#  POPUP / FLASH / MOUSE HELPERS
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
    ".",
    "..",
    "...",
    "HONK",
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
        wc.lpfnWndProc = {win32con.WM_DESTROY: lambda h,m,w,l: win32gui.PostQuitMessage(0)}
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

# ─────────────────────────────────────────────────────────────────────────────
#  NEW EFFECT 1 — HIDE/SHOW TASKBAR  (Stage 1)
# ─────────────────────────────────────────────────────────────────────────────

def hide_taskbar():
    """Slide the taskbar off screen."""
    try:
        hwnd = win32gui.FindWindow("Shell_TrayWnd", None)
        if hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
            state["taskbar_hidden"] = True
            print("  [taskbar] Hidden")
    except Exception as e:
        print(f"  [taskbar] {e}")

def show_taskbar():
    """Restore the taskbar."""
    try:
        hwnd = win32gui.FindWindow("Shell_TrayWnd", None)
        if hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            # Nudge it to repaint
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
            state["taskbar_hidden"] = False
            print("  [taskbar] Restored")
    except Exception as e:
        print(f"  [taskbar restore] {e}")

# ─────────────────────────────────────────────────────────────────────────────
#  NEW EFFECT 2 — FAKE CMD SCAN WINDOW  (Stage 2)
# ─────────────────────────────────────────────────────────────────────────────

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

def fake_cmd_scan():
    """Open a CMD window and type fake scan output."""
    try:
        proc = subprocess.Popen(
            ["cmd.exe", "/K", "echo GOOSE SECURITY SCANNER v6.6.6"],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        time.sleep(1.0)
        # Find the new CMD window and bring it forward
        hwnd = None
        for _ in range(10):
            hwnd = win32gui.FindWindow("ConsoleWindowClass", None)
            if hwnd: break
            time.sleep(0.2)
        if hwnd:
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.3)
        # Type fake scan lines
        for line in FAKE_SCAN_LINES:
            if not state["running"]: break
            pyautogui.typewrite(f"echo {line}", interval=0.02)
            pyautogui.press("enter")
            time.sleep(random.uniform(0.2, 0.6))
    except Exception as e:
        print(f"  [cmd scan] {e}")

# ─────────────────────────────────────────────────────────────────────────────
#  NEW EFFECT 3 — RANDOM WINDOW CHAOS  (Stage 3)
# ─────────────────────────────────────────────────────────────────────────────

def window_chaos():
    """Randomly minimize and restore open windows."""
    try:
        windows = []
        def collect(hwnd, _):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                # Skip taskbar and desktop
                cls = win32gui.GetClassName(hwnd)
                if cls not in ("Shell_TrayWnd", "Progman", "WorkerW", "GooseFlash"):
                    windows.append(hwnd)
        win32gui.EnumWindows(collect, None)

        if not windows:
            return

        # Pick 1-3 random windows to harass
        targets = random.sample(windows, min(3, len(windows)))
        for hwnd in targets:
            try:
                if random.random() > 0.5:
                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                else:
                    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                time.sleep(0.1)
            except Exception:
                pass
        time.sleep(random.uniform(1.0, 2.5))
        # Restore them
        for hwnd in targets:
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            except Exception:
                pass
    except Exception as e:
        print(f"  [window chaos] {e}")

# ─────────────────────────────────────────────────────────────────────────────
#  NEW EFFECT 4 — COLOR INVERSION  (Stage 4)
# ─────────────────────────────────────────────────────────────────────────────

def invert_colors():
    """Invert screen colors using Windows Magnification API."""
    try:
        # Use the color inversion shortcut: Win+Ctrl+C toggles color filters
        # This is the built-in Windows accessibility color inversion
        import win32com.client
    except ImportError:
        pass

    try:
        # Fallback: use ctypes to toggle high contrast which inverts colors
        # HIGHCONTRAST structure
        HC_ON    = 0x00000001
        HC_OFF   = 0x00000000
        SPI_SETHIGHCONTRAST = 0x0043
        SPI_GETHIGHCONTRAST = 0x0042

        class HIGHCONTRAST(ctypes.Structure):
            _fields_ = [
                ("cbSize",         ctypes.c_uint),
                ("dwFlags",        ctypes.c_uint),
                ("lpszDefaultScheme", ctypes.c_wchar_p),
            ]

        hc = HIGHCONTRAST()
        hc.cbSize = ctypes.sizeof(HIGHCONTRAST)
        # Get current state
        ctypes.windll.user32.SystemParametersInfoW(
            SPI_GETHIGHCONTRAST, ctypes.sizeof(HIGHCONTRAST),
            ctypes.byref(hc), 0)

        # Toggle on
        hc.dwFlags |= HC_ON
        ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETHIGHCONTRAST, 0, ctypes.byref(hc), 0)
        state["colors_inverted"] = True
        print("  [invert] Colors inverted")

        time.sleep(random.uniform(3, 6))

        # Toggle off
        hc.dwFlags &= ~HC_ON
        ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETHIGHCONTRAST, 0, ctypes.byref(hc), 0)
        state["colors_inverted"] = False
        print("  [invert] Colors restored")
    except Exception as e:
        print(f"  [invert] {e}")

def restore_colors():
    """Make sure colors are restored on exit."""
    if not state["colors_inverted"]:
        return
    try:
        class HIGHCONTRAST(ctypes.Structure):
            _fields_ = [
                ("cbSize",            ctypes.c_uint),
                ("dwFlags",           ctypes.c_uint),
                ("lpszDefaultScheme", ctypes.c_wchar_p),
            ]
        hc = HIGHCONTRAST()
        hc.cbSize = ctypes.sizeof(HIGHCONTRAST)
        ctypes.windll.user32.SystemParametersInfoW(0x0042, ctypes.sizeof(HIGHCONTRAST), ctypes.byref(hc), 0)
        hc.dwFlags &= ~0x00000001
        ctypes.windll.user32.SystemParametersInfoW(0x0043, 0, ctypes.byref(hc), 0)
        state["colors_inverted"] = False
    except Exception as e:
        print(f"  [restore colors] {e}")

# ─────────────────────────────────────────────────────────────────────────────
#  NEW EFFECT 5 — SEIZURE FLASH BURST  (Stage 5 intro)
# ─────────────────────────────────────────────────────────────────────────────

def seizure_flash_burst(count=20):
    """Rapid-fire full screen flashes before the fake reboot."""
    colors = [(255,0,0),(255,255,255),(0,0,0),(255,255,0),(0,0,255),(255,0,255)]
    for i in range(count):
        if not True: break  # always run even after state["running"] = False
        do_flash(duration=0.04, color=colors[i % len(colors)])
        time.sleep(0.03)

# ─────────────────────────────────────────────────────────────────────────────
#  ICON FLEE  (Stage 3)
# ─────────────────────────────────────────────────────────────────────────────

def icon_flee_loop():
    def get_desktop_hwnd():
        hwnd = win32gui.FindWindow("Progman", None)
        hwnd = win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", None)
        hwnd = win32gui.FindWindowEx(hwnd, 0, "SysListView32", None)
        return hwnd

    desktop = get_desktop_hwnd()
    if not desktop:
        print("  [icons] Could not find desktop ListView")
        return

    print("  [icons] Icon flee loop started")
    while state["running"] and state["icon_flee_active"]:
        time.sleep(0.05)
    print("  [icons] Icon flee loop ended")

def start_icon_flee():
    if state["icon_flee_active"]: return
    state["icon_flee_active"] = True
    threading.Thread(target=icon_flee_loop, daemon=True).start()

def stop_icon_flee():
    state["icon_flee_active"] = False

# ─────────────────────────────────────────────────────────────────────────────
#  STAGE RUNNERS
# ─────────────────────────────────────────────────────────────────────────────

def run_stage_1():
    print("[STAGE 1] Warning issued")
    title, msg = random.choice(STAGE1_MESSAGES)
    show_popup(title, msg, win32con.MB_ICONWARNING | win32con.MB_OK | win32con.MB_TOPMOST)
    # NEW: Hide the taskbar for extra unease
    threading.Thread(target=hide_taskbar, daemon=True).start()

def run_stage_2():
    print("[STAGE 2] Chaos begins")
    wp = make_chaos_wallpaper(0)
    state["chaos_wallpaper"] = wp
    set_wallpaper(wp)
    state["wallpaper_applied"] = True

    # NEW: Launch fake CMD scan
    threading.Thread(target=fake_cmd_scan, daemon=True).start()

    def stage2_loop():
        variant = 0
        while state["running"] and state["stage"] == 2:
            interval = random.uniform(4, 10)
            time.sleep(interval)
            if not state["running"] or state["stage"] != 2: break
            action = random.choice(["flash", "popup", "wallpaper"])
            if action == "flash":
                do_flash(duration=random.uniform(0.08, 0.2))
            elif action == "popup":
                title, msg = random.choice(STAGE2_POPUPS)
                show_popup(title, msg)
            elif action == "wallpaper":
                variant = (variant + 1) % len(WALLPAPER_VARIANTS)
                wp = make_chaos_wallpaper(variant)
                state["chaos_wallpaper"] = wp
                set_wallpaper(wp)

    threading.Thread(target=stage2_loop, daemon=True).start()

def run_stage_3():
    print("[STAGE 3] Icons fleeing + window chaos")
    start_icon_flee()

    # NEW: Random window minimize/maximize loop
    def window_chaos_loop():
        while state["running"] and state["stage"] == 3:
            time.sleep(random.uniform(4, 8))
            if not state["running"] or state["stage"] != 3: break
            threading.Thread(target=window_chaos, daemon=True).start()

    threading.Thread(target=window_chaos_loop, daemon=True).start()

    def stage3_wallpaper():
        variant = 1
        while state["running"] and state["stage"] == 3:
            time.sleep(random.uniform(6, 12))
            if not state["running"] or state["stage"] != 3: break
            variant = (variant + 1) % len(WALLPAPER_VARIANTS)
            wp = make_chaos_wallpaper(variant)
            state["chaos_wallpaper"] = wp
            set_wallpaper(wp)
            do_flash(duration=0.1)

    threading.Thread(target=stage3_wallpaper, daemon=True).start()

def run_stage_4():
    print("[STAGE 4] INTENSE CHAOS + COLOR INVERSION")

    # NEW: Kick off a color inversion in the background
    threading.Thread(target=invert_colors, daemon=True).start()

    def stage4_loop():
        while state["running"] and state["stage"] == 4:
            interval = random.uniform(1.5, 5)
            time.sleep(interval)
            if not state["running"] or state["stage"] != 4: break
            action = random.choices(
                ["flash", "flash", "popup", "mouse", "wallpaper", "invert"],
                weights=[25, 25, 20, 15, 5, 10])[0]
            if action == "flash":
                for _ in range(random.randint(1, 4)):
                    do_flash(duration=random.uniform(0.05, 0.15))
                    time.sleep(0.05)
            elif action == "popup":
                title, msg = random.choice(STAGE4_POPUPS)
                show_popup(title, msg)
            elif action == "mouse":
                threading.Thread(target=do_mouse_chaos, args=(1.0,), daemon=True).start()
            elif action == "wallpaper":
                v = random.randint(0, len(WALLPAPER_VARIANTS)-1)
                wp = make_chaos_wallpaper(v)
                state["chaos_wallpaper"] = wp
                set_wallpaper(wp)
            elif action == "invert":
                threading.Thread(target=invert_colors, daemon=True).start()

    threading.Thread(target=stage4_loop, daemon=True).start()

    def threat_sequence():
        time.sleep(1)
        show_popup("🪿 GOOSE FINAL WARNING",
            "You have made a grave mistake.\n\n"
            "The goose is now in control of your computer.\n\n"
            "Prepare for termination.",
            win32con.MB_ICONSTOP | win32con.MB_OK | win32con.MB_TOPMOST)
        time.sleep(3)
        if state["running"] and state["stage"] == 4:
            show_popup("GOOSE.EXE — SYSTEM TAKEOVER",
                "Deleting System32...\n"
                "Formatting C:\\\n"
                "Uploading everything to GOOSE.GOV\n\n"
                "There is no escape.\n\nHONK.",
                win32con.MB_ICONSTOP | win32con.MB_OK | win32con.MB_TOPMOST)

    threading.Thread(target=threat_sequence, daemon=True).start()

def run_stage_5():
    print("[STAGE 5] FAKE REBOOT")
    state["running"] = False
    stop_icon_flee()
    restore_colors()

    # NEW: Seizure flash burst before the notepad
    seizure_flash_burst(count=25)

    try:
        subprocess.Popen(["notepad.exe"])
        time.sleep(1.2)
        hwnd = win32gui.FindWindow("Notepad", None)
        if hwnd:
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.3)
        for line in FAKE_REBOOT_LINES:
            pyautogui.typewrite(line + "\n", interval=0.04)
            time.sleep(0.3)
    except Exception as e:
        print(f"  [reboot notepad] {e}")

    time.sleep(1)
    ctypes.windll.user32.MessageBoxW(
        0,
        "The goose has finished.\n\nYour computer will now restart.\n\n(not really)",
        "GOOSE PROTOCOL COMPLETE",
        win32con.MB_ICONSTOP | win32con.MB_OK | win32con.MB_TOPMOST)

    restore_all()
    time.sleep(0.5)
    os._exit(0)

STAGE_RUNNERS = {1: run_stage_1, 2: run_stage_2, 3: run_stage_3,
                 4: run_stage_4, 5: run_stage_5}

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
                win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
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
                print(f"[pipe] Error: {e}")
                time.sleep(2)

# ─────────────────────────────────────────────────────────────────────────────
#  RESTORE & EXIT
# ─────────────────────────────────────────────────────────────────────────────

def restore_all():
    print("[→] Restoring everything...")
    stop_icon_flee()
    restore_colors()
    show_taskbar()
    if state["original_wallpaper"]:
        try:
            set_wallpaper(state["original_wallpaper"])
            print("  ✓ Wallpaper restored")
        except Exception as e:
            print(f"  ✗ Wallpaper failed: {e}")
    for i in range(len(WALLPAPER_VARIANTS)):
        p = TEMP / f"goose_chaos_bg_{i}.png"
        try:
            if p.exists(): p.unlink()
        except: pass
    try:
        subprocess.call(["taskkill","/F","/IM","Desktop Goose.exe"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(["taskkill","/F","/IM","notepad.exe"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(["taskkill","/F","/IM","cmd.exe"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("  ✓ Processes killed")
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
    print("=" * 55)
    print("  🪿  GooseChaos — 5 Stage Virus Edition (Extended)")
    print("  Click the goose to escalate through stages")
    print("  Press  ESC  to revert everything & exit")
    print("=" * 55)
    print()
    print("  Stage 1: Warning popup + taskbar vanishes")
    print("  Stage 2: Wallpaper + flickers + fake CMD scan")
    print("  Stage 3: Icons flee + windows minimize/maximize")
    print("  Stage 4: Full chaos + screen color inversion")
    print("  Stage 5: Seizure flash burst + fake reboot")
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
