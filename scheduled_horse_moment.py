"""
Scheduled_Horse_Moment.Exe
Runs silently in the background and pops up a Horse Moment
at a random interval between 15 minutes and 3 hours.

Requirements:
    pip install pillow

To build into an .exe (place horse.png + horse.ico beside the script first):
    pip install pyinstaller
    pyinstaller --onefile --noconsole --icon=horse.ico --add-data "horse.png;." --add-data "horse.ico;." scheduled_horse_moment.py
"""

import tkinter as tk
from tkinter import font
import threading
import time
import random
import sys
import os
import winsound

# ── Interval config ───────────────────────────────────────────────────────────
MIN_INTERVAL_SECONDS = 5 * 60      # 5 minutes
MAX_INTERVAL_SECONDS = 2 * 60 * 60  # 2 hours

CONTEMPLATION_MS = 10_000           # 10 seconds of mandatory reflection

# ── Variant odds ─────────────────────────────────────────────────────────────
UNOBTANIUM_CHANCE = 1 / 10_000      # 0.01% — rarest
GOLDEN_CHANCE     = 1 / 100        # 1%
HOWARD_CHANCE     = 1 / 10         # 10%

# ── Win9x palette ─────────────────────────────────────────────────────────────
WIN_BG        = "#C6C6C6"
TITLE_BG      = "#000080"
TITLE_FG      = "#ffffff"
BODY_FG       = "#000000"
BORDER_LIGHT  = "#ffffff"
BORDER_DARK   = "#808080"
BORDER_DARKER = "#404040"
BAR_FILL      = "#000080"
BAR_BG        = "#ffffff"

GOLDEN_BG        = "#FFD700"
GOLDEN_TITLE     = "#B8860B"
UNOBTANIUM_BG    = "#000000"
UNOBTANIUM_TITLE = "#1a1a2e"
UNOBTANIUM_FG    = "#00ffcc"

HORSE_EMOJI   = "🐴"


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_next_interval():
    return random.randint(MIN_INTERVAL_SECONDS, MAX_INTERVAL_SECONDS)


def resource_path(filename):
    """Return path to a bundled resource (works for both script and .exe)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, filename)


def play_notification():
    """Play the Windows notification sound (non-blocking)."""
    try:
        winsound.PlaySound("SystemNotification",
                           winsound.SND_ALIAS | winsound.SND_ASYNC)
    except Exception:
        try:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass


# ── Win9x button ──────────────────────────────────────────────────────────────

class Win9xButton(tk.Canvas):
    """Raised Windows 9x-style button with optional disabled state."""

    def __init__(self, parent, text, command=None,
                 width=75, height=23, disabled=False, bg=WIN_BG, **kw):
        super().__init__(parent, width=width, height=height,
                         bg=bg, highlightthickness=0, **kw)
        self._bg      = bg
        self.command  = command
        self.text     = text
        self.disabled = disabled
        self._draw()
        self.bind("<ButtonPress-1>",   self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _body_font(self):
        try:
            return font.Font(family="Segoe UI", size=9)
        except Exception:
            return font.Font(family="MS Sans Serif", size=8)

    def _draw(self, pressed=False):
        self.delete("all")
        w, h = int(self["width"]), int(self["height"])

        if self.disabled:
            tl = br = BORDER_DARK
            fg = BORDER_DARK
            tx = ty = 1
        elif pressed:
            tl, br = BORDER_DARK, BORDER_LIGHT
            fg = BODY_FG
            tx = ty = 2
        else:
            tl, br = BORDER_LIGHT, BORDER_DARK
            fg = BODY_FG
            tx = ty = 1

        self.create_rectangle(0, 0, w, h, fill=self._bg, outline="")
        self.create_rectangle(0, 0, w-1, h-1, outline=BORDER_DARKER)
        self.create_line(1, h-2, 1, 1, w-2, 1, fill=tl)
        self.create_line(1, h-1, w-1, h-1, w-1, 1, fill=br)
        self.create_text(w//2 + tx, h//2 + ty, text=self.text,
                         font=self._body_font(), fill=fg)

    def enable(self):
        self.disabled = False
        self._draw()

    def disable(self):
        self.disabled = True
        self._draw()

    def _on_press(self, e):
        if not self.disabled:
            self._draw(pressed=True)

    def _on_release(self, e):
        if not self.disabled:
            self._draw(pressed=False)
            if self.command:
                self.command()


# ── Progress bar ──────────────────────────────────────────────────────────────

class Win9xProgressBar(tk.Canvas):
    """Classic segmented Win9x progress bar."""

    SEGMENT_W   = 11
    SEGMENT_GAP = 2

    def __init__(self, parent, width=300, height=16, **kw):
        super().__init__(parent, width=width, height=height,
                         bg=BAR_BG, highlightthickness=1,
                         highlightbackground=BORDER_DARK,
                         highlightcolor=BORDER_DARK, **kw)
        self._inner_w = width - 2
        self._bar_h   = height
        self._pct     = 0.0
        self._draw()

    def set(self, pct: float):
        self._pct = max(0.0, min(1.0, pct))
        self._draw()

    def _draw(self):
        self.delete("all")
        filled_px = int(self._inner_w * self._pct)
        x = 1
        while x + self.SEGMENT_W - self.SEGMENT_GAP <= filled_px:
            self.create_rectangle(
                x, 2,
                x + self.SEGMENT_W - self.SEGMENT_GAP,
                self._bar_h - 2,
                fill=BAR_FILL, outline=""
            )
            x += self.SEGMENT_W
        if self._pct >= 1.0:
            self.create_rectangle(
                x, 2,
                self._inner_w + 1,
                self._bar_h - 2,
                fill=BAR_FILL, outline=""
            )


# ── Main window ───────────────────────────────────────────────────────────────

class HorseMomentWindow:
    def __init__(self):
        # Roll for variants — unobtanium takes priority over golden
        roll = random.random()
        if roll < UNOBTANIUM_CHANCE:
            self.variant = 'unobtanium'
        elif roll < GOLDEN_CHANCE:
            self.variant = 'golden'
        else:
            self.variant = 'normal'

        self.is_golden     = self.variant == 'golden'
        self.is_unobtanium = self.variant == 'unobtanium'
        self.show_howard   = random.random() < HOWARD_CHANCE

        if self.is_unobtanium:
            self.bg       = UNOBTANIUM_BG
            self.title_bg = UNOBTANIUM_TITLE
            self.body_fg  = UNOBTANIUM_FG
        elif self.is_golden:
            self.bg       = GOLDEN_BG
            self.title_bg = GOLDEN_TITLE
            self.body_fg  = BODY_FG
        else:
            self.bg       = WIN_BG
            self.title_bg = TITLE_BG
            self.body_fg  = BODY_FG

        self.root = tk.Tk()
        self.root.title("")
        self.root.resizable(False, False)
        self.root.overrideredirect(True)
        self.root.configure(bg=self.bg)
        self.root.attributes("-topmost", True)
        # Force focus so it truly appears above everything (e.g. fullscreen apps)
        self.root.after(100, self._force_focus)

        # Block Alt-F4 and any WM close attempts
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        self._build_ui()

        # Set taskbar / window icon from horse.ico
        try:
            self.root.iconbitmap(resource_path("horse.ico"))
        except Exception:
            pass

        # Play notification sound (non-blocking)
        threading.Thread(target=play_notification, daemon=True).start()

        # Centre and force focus once the window is fully rendered, then start countdown
        self.root.after(10, self._centre_and_start)
        self.root.after(150, self._force_focus)

    def _force_focus(self):
        """Lift and grab focus so the window appears above everything."""
        self.root.lift()
        self.root.focus_force()
        # Re-assert topmost in case something stole it
        self.root.attributes("-topmost", True)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        bg = self.bg

        outer  = tk.Frame(self.root, bg=BORDER_DARKER, padx=2, pady=2)
        outer.pack()
        inner  = tk.Frame(outer, bg=BORDER_LIGHT, padx=1, pady=1)
        inner.pack()
        window = tk.Frame(inner, bg=bg, padx=1, pady=1)
        window.pack()

        # ── Title bar ─────────────────────────────────────────────────────────
        titlebar = tk.Frame(window, bg=self.title_bg, height=22)
        titlebar.pack(fill="x")
        titlebar.pack_propagate(False)

        try:
            from PIL import Image, ImageTk
            ico = Image.open(resource_path("horse.ico"))
            ico.thumbnail((16, 16), Image.LANCZOS)
            self._title_icon = ImageTk.PhotoImage(ico)
            icon_lbl = tk.Label(titlebar, image=self._title_icon,
                                bg=self.title_bg, padx=3)
        except Exception:
            icon_lbl = tk.Label(titlebar, text=HORSE_EMOJI, bg=self.title_bg,
                                fg=TITLE_FG, font=("Segoe UI Emoji", 12), padx=3)
        icon_lbl.pack(side="left")

        try:
            tf = font.Font(family="Segoe UI", size=9, weight="bold")
        except Exception:
            tf = font.Font(family="MS Sans Serif", size=9, weight="bold")

        if self.is_unobtanium:
            title_text = "holy crap... unobtanium horse"
        elif self.is_golden:
            title_text = "You found the magical golden horse!"
        else:
            title_text = "Scheduled_Horse_Moment.Exe"

        title_lbl = tk.Label(titlebar, text=title_text,
                             bg=self.title_bg, fg=TITLE_FG, font=tf, padx=2)
        title_lbl.pack(side="left", fill="y")

        Win9xButton(titlebar, "X", command=None,
                    width=16, height=14, disabled=True, bg=bg
                    ).pack(side="right", padx=2, pady=3)
        Win9xButton(titlebar, "?", command=self._show_help,
                    width=16, height=14, bg=bg
                    ).pack(side="right", padx=0, pady=3)

        for w in (titlebar, title_lbl, icon_lbl):
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>",     self._drag_move)

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(window, bg=bg, padx=10, pady=20)
        body.pack()

        try:
            bf = font.Font(family="Segoe UI", size=10)
        except Exception:
            bf = font.Font(family="MS Sans Serif", size=9)

        text_frame = tk.Frame(body, bg=bg)
        text_frame.pack(side="left", anchor="nw", padx=(0, 15))

        tk.Label(text_frame,
                 text="Please stand by for a scheduled Horse\nMoment.",
                 bg=bg, fg=self.body_fg, font=bf,
                 justify="left").pack(anchor="w", pady=(5, 20))

        tk.Label(text_frame,
                 text="You will now contemplate and reflect.\nThis is a time of seriousness.",
                 bg=bg, fg=self.body_fg, font=bf,
                 justify="left").pack(anchor="w")

        if self.show_howard:
            tk.Label(text_frame,
                     text="howard existed",
                     bg=bg, fg=self.body_fg, font=bf,
                     justify="left").pack(anchor="w", pady=(12, 0))

        self._load_horse_image(body, bg)

        # ── Bottom text ───────────────────────────────────────────────────────
        tk.Label(window,
                 text="You currently have scheduled Horse Moments turned on.\n"
                      "You can not change this in settings.",
                 bg=bg, fg=self.body_fg, font=bf,
                 justify="left", padx=10).pack(anchor="w", pady=(0, 12))

        # ── Progress bar ──────────────────────────────────────────────────────
        bar_frame = tk.Frame(window, bg=bg, padx=10)
        bar_frame.pack(fill="x", pady=(0, 4))

        self._progress = Win9xProgressBar(bar_frame, width=460, height=18)
        self._progress.pack(fill="x")

        try:
            sf = font.Font(family="Segoe UI", size=8)
        except Exception:
            sf = font.Font(family="MS Sans Serif", size=8)

        self._status_lbl = tk.Label(bar_frame,
                                    text="Contemplating…",
                                    bg=bg, fg=self.body_fg,
                                    font=sf, justify="left")
        self._status_lbl.pack(anchor="w", pady=(2, 0))

        btn_row = tk.Frame(window, bg=bg)
        btn_row.pack(pady=(6, 16))
        self._ok_btn = Win9xButton(btn_row, "OK", command=self._close,
                                   width=75, height=23, disabled=True, bg=bg)
        self._ok_btn.pack()

    # ── Horse image loader ────────────────────────────────────────────────────

    def _load_horse_image(self, parent, bg):
        try:
            from PIL import Image, ImageTk
            path = resource_path("horse.png")
            img  = Image.open(path)
            img.thumbnail((210, 210), Image.LANCZOS)
            self._horse_photo = ImageTk.PhotoImage(img)
            tk.Label(parent, image=self._horse_photo, bg=bg
                     ).pack(side="right", anchor="n")
        except Exception:
            self._draw_horse_canvas(parent, bg).pack(side="right", anchor="n")

    @staticmethod
    def _draw_horse_canvas(parent, bg=WIN_BG, size=200):
        c = tk.Canvas(parent, width=size, height=size,
                      bg=bg, highlightthickness=0)
        s = size / 220
        CH="#8B4513"; CHD="#6B3410"; CHL="#A0522D"
        MN="#3B1A08"; HF="#2b1a0a"; EY="#1a0a00"; SH="#b0a898"
        def ov(x1,y1,x2,y2,**k): c.create_oval(x1*s,y1*s,x2*s,y2*s,**k)
        def py(*pts,**k):
            sc=[]
            for x,y in pts: sc+=[x*s,y*s]
            c.create_polygon(sc,**k)
        def rc(x1,y1,x2,y2,**k): c.create_rectangle(x1*s,y1*s,x2*s,y2*s,**k)
        c.create_oval(60*s,195*s,185*s,210*s,fill=SH,outline="")
        py((95,150),(103,150),(105,195),(93,195),fill=CHD,outline="")
        py((115,148),(123,148),(125,195),(113,195),fill=CHD,outline="")
        rc(93,192,105,200,fill=HF,outline=""); rc(113,192,125,200,fill=HF,outline="")
        py((125,148),(133,148),(135,195),(123,195),fill=CH,outline="")
        py((143,145),(151,145),(153,195),(141,195),fill=CH,outline="")
        rc(123,192,135,200,fill=HF,outline=""); rc(141,192,153,200,fill=HF,outline="")
        py((80,100),(190,95),(200,145),(75,155),fill=CH,outline="")
        ov(85,90,195,160,fill=CH,outline=CHD,width=1)
        py((100,148),(180,143),(185,158),(95,163),fill=CHD,outline="")
        py((155,85),(175,90),(170,135),(148,140),fill=CH,outline=CHD,width=1)
        ov(158,55,200,100,fill=CH,outline=CHD,width=1)
        ov(162,88,194,112,fill=CHL,outline=CHD,width=1)
        ov(168,100,175,106,fill=CHD,outline=""); ov(180,99,187,105,fill=CHD,outline="")
        ov(182,63,193,72,fill=EY,outline="")
        c.create_oval(184*s,65*s,189*s,70*s,fill="#fff",outline="")
        py((183,55),(192,42),(198,57),fill=CH,outline=CHD,width=1)
        py((185,54),(191,46),(196,56),fill="#c06040",outline="")
        py((155,65),(163,60),(168,90),(156,95),fill=MN,outline="")
        py((155,70),(148,68),(150,100),(158,98),fill=MN,outline="")
        py((182,56),(186,42),(194,50),(190,62),fill=MN,outline="")
        py((82,100),(75,95),(55,130),(60,140),(80,125),(85,115),fill=MN,outline="")
        py((60,135),(50,155),(58,158),(68,140),(65,132),fill=CHD,outline="")
        return c

    # ── Countdown tick ────────────────────────────────────────────────────────

    def _tick(self):
        elapsed = (time.time() - self._start_time) * 1000
        pct     = min(elapsed / CONTEMPLATION_MS, 1.0)
        self._progress.set(pct)

        if pct < 1.0:
            remaining = max(0, (CONTEMPLATION_MS - elapsed) / 1000)
            self._status_lbl.config(
                text=f"Contemplating… ({remaining:.0f}s remaining)"
            )
            self.root.after(50, self._tick)
        else:
            self._status_lbl.config(text="Contemplation complete. You may proceed.")
            self._ok_btn.enable()

    # ── Window helpers ────────────────────────────────────────────────────────

    def _centre_and_start(self):
        self.root.update_idletasks()
        w  = self.root.winfo_width()
        h  = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x  = (sw - w) // 2
        y  = (sh - h) // 2
        self.root.geometry(f"+{x}+{y}")
        # Begin countdown now that position is set
        self._start_time = time.time()
        self._tick()

    def _centre(self):
        self.root.update_idletasks()
        w  = self.root.winfo_width()
        h  = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    def _drag_start(self, e):
        self._dx = e.x_root - self.root.winfo_x()
        self._dy = e.y_root - self.root.winfo_y()

    def _drag_move(self, e):
        self.root.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")

    def _close(self):
        self.root.destroy()

    def _show_help(self):
        hw = tk.Toplevel(self.root)
        hw.title("Help")
        hw.resizable(False, False)
        hw.configure(bg=self.bg)
        hw.attributes("-topmost", True)
        hw.protocol("WM_DELETE_WINDOW", hw.destroy)
        try:
            hf = font.Font(family="Segoe UI", size=10)
        except Exception:
            hf = font.Font(family="MS Sans Serif", size=9)
        tk.Label(hw,
                 text="There is no help.\nThe Horse Moment is mandatory.",
                 bg=self.bg, fg=self.body_fg, padx=20, pady=20, font=hf).pack()
        Win9xButton(hw, "OK", command=hw.destroy,
                    width=75, height=23, bg=self.bg).pack(pady=(0, 10))

    def run(self):
        self.root.mainloop()


# ── Scheduler ─────────────────────────────────────────────────────────────────

def show_horse():
    HorseMomentWindow().run()


def scheduler_loop():
    while True:
        secs = get_next_interval()
        print(f"[Horse Scheduler] Next moment in {secs//60}m {secs%60}s")
        time.sleep(secs)
        show_horse()


def main():
    print("[Horse Scheduler] Running. You can not change this in settings.")

    t = threading.Thread(target=show_horse, daemon=True)
    t.start()
    t.join()

    threading.Thread(target=scheduler_loop, daemon=True).start()

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
