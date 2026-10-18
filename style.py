# =====================================================================
#  style.py — GLOBAL THEME / STYLE MODULE  (the "CSS")
#  Edit colors, fonts, sizes here without touching app logic.
# =====================================================================

import tkinter as tk


# ---------------------------------------------------------------------
#  COLORS
# ---------------------------------------------------------------------

class Colors:
    BG = "#070A12"
    BG_SOFT = "#0B1020"
    SURFACE = "#101827"
    SURFACE_ALT = "#162034"
    SURFACE_HI = "#1C2A44"
    BORDER = "#22304A"
    BORDER_HI = "#2E405F"

    HEADER_1 = "#080B16"
    HEADER_2 = "#101B33"

    CYAN = "#00E5FF"
    CYAN_DIM = "#0A8FA5"
    CYAN_SOFT = "#0E3340"
    GREEN = "#00FFA3"
    GREEN_DIM = "#00B37A"
    GREEN_SOFT = "#0C3A2C"
    RED = "#FF3B5C"
    RED_DIM = "#C2273F"
    RED_SOFT = "#3A1220"
    AMBER = "#FFB020"
    AMBER_DIM = "#C7860B"
    AMBER_SOFT = "#3A2A0C"
    MAGENTA = "#B24BF3"
    MAGENTA_DIM = "#8B2FC9"
    MAGENTA_SOFT = "#2A1440"

    TEXT = "#EAF0FA"
    TEXT_MUTED = "#8394B0"
    TEXT_DIM = "#4A5878"


# ---------------------------------------------------------------------
#  FONTS
# ---------------------------------------------------------------------

class Fonts:
    FAMILY = "Segoe UI"
    MONO = "Consolas"


# ---------------------------------------------------------------------
#  LAYOUT SIZES (the "media queries" of Tkinter)
# ---------------------------------------------------------------------

class Layout:
    # Window sizes
    LOGIN_PANEL_W, LOGIN_PANEL_H = 460, 520
    REGISTER_PANEL_W, REGISTER_PANEL_H = 500, 560
    RENT_WINDOW_W, RENT_WINDOW_H = 620, 900
    PAYMENT_WINDOW_W, PAYMENT_WINDOW_H = 640, 760

    # Field sizes
    FIELD_W, FIELD_H = 500, 48
    LOGIN_FIELD_W, LOGIN_FIELD_H = 380, 44
    NARROW_FIELD_W, NARROW_FIELD_H = 360, 44

    # Grid
    CARD_COLS_WIDE = 5
    CARD_COLS_NARROW = 4
    CARD_W, CARD_H, CARD_RADIUS = 268, 356, 18

    # Header
    HEADER_H = 84


# ---------------------------------------------------------------------
#  FONT FACTORY FUNCTIONS
# ---------------------------------------------------------------------

def F(size, weight="normal"):
    """Standard UI font."""
    return (Fonts.FAMILY, size, weight)


def M(size, weight="normal"):
    """Monospaced font for prices/IDs."""
    return (Fonts.MONO, size, weight)


# ---------------------------------------------------------------------
#  SMALL UTILITIES
# ---------------------------------------------------------------------

def spaced(text):
    """Returns text with spaces between letters, e.g. 'RENT' -> 'R E N T'."""
    return " ".join(list(text))


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(c))) for c in rgb)


def lerp(c1, c2, t):
    """Linear interpolation between two hex colors."""
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return rgb_to_hex((
        r1 + (r2 - r1) * t,
        g1 + (g2 - g1) * t,
        b1 + (b2 - b1) * t,
    ))


# ---------------------------------------------------------------------
#  DRAWING PRIMITIVES  (these used to live in main.py)
# ---------------------------------------------------------------------

def round_rect(canvas, x1, y1, x2, y2, radius=16, **kwargs):
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def draw_h_gradient(canvas, width, height, c1, c2, steps=96):
    for i in range(steps):
        t = i / (steps - 1)
        color = lerp(c1, c2, t)
        x0 = width * i / steps
        x1 = width * (i + 1) / steps + 1
        canvas.create_rectangle(x0, 0, x1, height, fill=color, outline=color)


def make_rounded_panel(parent, width, height, radius=20, fill=None, outline=None,
                       bg=None, outline_width=1.4):
    fill = fill or Colors.SURFACE
    outline = outline or Colors.BORDER
    bgc = bg if bg is not None else parent.cget("bg")
    canvas = tk.Canvas(parent, width=width, height=height, bg=bgc,
                       highlightthickness=0, bd=0)
    round_rect(canvas, 2, 2, width - 2, height - 2, radius,
               fill=fill, outline=outline, width=outline_width)
    content = tk.Frame(canvas, bg=fill)
    inset = radius + 8
    cw = max(width - 2 * inset, 10)
    ch = max(height - 2 * inset, 10)
    canvas.create_window(width / 2, height / 2, window=content, width=cw, height=ch)
    return canvas, content


def center_toplevel(win, parent, w, h):
    parent.update_idletasks()
    px = parent.winfo_rootx()
    py = parent.winfo_rooty()
    pw = parent.winfo_width()
    ph = parent.winfo_height()
    x = px + max((pw - w) // 2, 0)
    y = py + max((ph - h) // 2, 0)
    win.geometry(f"{w}x{h}+{x}+{y}")


# ---------------------------------------------------------------------
#  COMPOSITE STYLE HELPERS
# ---------------------------------------------------------------------

def field_label(parent, text):
    """Standard small uppercase label above an input field."""
    tk.Label(
        parent, text=text, font=F(8, "bold"), bg=parent.cget("bg"),
        fg=Colors.TEXT_MUTED
    ).pack(anchor="w", pady=(12, 5))


def section_title(parent, text, accent=None, size=14, subtitle=None):
    """Section header with an accent bar and optional subtitle."""
    accent = accent or Colors.CYAN
    outer = tk.Frame(parent, bg=parent.cget("bg"))
    row = tk.Frame(outer, bg=parent.cget("bg"))
    row.pack(anchor="w")
    tk.Frame(row, bg=accent, width=4, height=size + 10).pack(side="left", padx=(0, 10))
    tk.Label(
        row, text=spaced(text.upper()), font=F(size, "bold"),
        bg=parent.cget("bg"), fg=Colors.TEXT
    ).pack(side="left")
    if subtitle:
        tk.Label(
            outer, text=subtitle, font=F(9),
            bg=parent.cget("bg"), fg=Colors.TEXT_MUTED
        ).pack(anchor="w", padx=(14, 0), pady=(4, 0))
    return outer


def neon_badge(parent, text, color, bg=None):
    bgc = bg or Colors.SURFACE
    wrapper = tk.Frame(parent, bg=color)
    tk.Label(
        wrapper, text=("● " + text).upper(), font=F(8, "bold"),
        bg=bgc, fg=color, padx=10, pady=3
    ).pack(padx=1.2, pady=1.2)
    return wrapper


# ---------------------------------------------------------------------
#  TTK STYLE SETUP  (equivalent to CSS for ttk widgets)
# ---------------------------------------------------------------------

def apply_dark_ttk(root):
    from tkinter import ttk
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(
        "Modern.Treeview",
        background=Colors.SURFACE,
        fieldbackground=Colors.SURFACE,
        foreground=Colors.TEXT,
        rowheight=34,
        font=F(10),
        borderwidth=0,
    )
    style.configure(
        "Modern.Treeview.Heading",
        background=Colors.SURFACE_ALT,
        foreground=Colors.CYAN,
        font=F(9, "bold"),
        relief="flat",
        padding=10,
        borderwidth=0,
    )
    style.map("Modern.Treeview.Heading",
              background=[("active", Colors.SURFACE_HI)])
    style.map("Modern.Treeview",
              background=[("selected", Colors.CYAN_SOFT)],
              foreground=[("selected", Colors.CYAN)])

    style.configure(
        "Dark.Vertical.TScrollbar",
        background=Colors.SURFACE_ALT,
        troughcolor=Colors.BG,
        bordercolor=Colors.BG,
        arrowcolor=Colors.CYAN,
        relief="flat",
        width=12,
    )
    style.map("Dark.Vertical.TScrollbar",
              background=[("active", Colors.CYAN_DIM)])

    style.configure(
        "Dark.TCombobox",
        fieldbackground=Colors.SURFACE,
        background=Colors.SURFACE,
        foreground=Colors.TEXT,
        bordercolor=Colors.BORDER,
        arrowcolor=Colors.CYAN,
        padding=8,
        relief="flat",
    )
    style.map(
        "Dark.TCombobox",
        fieldbackground=[("readonly", Colors.SURFACE)],
        foreground=[("readonly", Colors.TEXT)],
        bordercolor=[("focus", Colors.CYAN)],
    )
    root.option_add("*TCombobox*Listbox.background", Colors.SURFACE)
    root.option_add("*TCombobox*Listbox.foreground", Colors.TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", Colors.CYAN_SOFT)
    root.option_add("*TCombobox*Listbox.selectForeground", Colors.CYAN)
    root.option_add("*TCombobox*Listbox.font", F(10))


# ---------------------------------------------------------------------
#  BACKWARDS-COMPAT ALIAS  (so old code using Theme.CYAN still works)
# ---------------------------------------------------------------------

class Theme:
    """Kept for backwards compatibility — mirrors Colors."""
    BG = Colors.BG
    BG_SOFT = Colors.BG_SOFT
    SURFACE = Colors.SURFACE
    SURFACE_ALT = Colors.SURFACE_ALT
    SURFACE_HI = Colors.SURFACE_HI
    BORDER = Colors.BORDER
    BORDER_HI = Colors.BORDER_HI
    HEADER_1 = Colors.HEADER_1
    HEADER_2 = Colors.HEADER_2
    CYAN = Colors.CYAN
    CYAN_DIM = Colors.CYAN_DIM
    CYAN_SOFT = Colors.CYAN_SOFT
    GREEN = Colors.GREEN
    GREEN_DIM = Colors.GREEN_DIM
    GREEN_SOFT = Colors.GREEN_SOFT
    RED = Colors.RED
    RED_DIM = Colors.RED_DIM
    RED_SOFT = Colors.RED_SOFT
    AMBER = Colors.AMBER
    AMBER_DIM = Colors.AMBER_DIM
    AMBER_SOFT = Colors.AMBER_SOFT
    MAGENTA = Colors.MAGENTA
    MAGENTA_DIM = Colors.MAGENTA_DIM
    MAGENTA_SOFT = Colors.MAGENTA_SOFT
    TEXT = Colors.TEXT
    TEXT_MUTED = Colors.TEXT_MUTED
    TEXT_DIM = Colors.TEXT_DIM
    FONT = Fonts.FAMILY
    MONO = Fonts.MONO


# ---------------------------------------------------------------------
#  CUSTOM WIDGETS  (NeonButton, NeonEntry, StatTile)
#  These are "styled components" — kept here so main.py stays logic-only.
# ---------------------------------------------------------------------

class NeonButton(tk.Canvas):
    """Rounded glowing button — ghost by default, fills on hover."""

    def __init__(self, parent, text, command=None, accent=None,
                 width=170, height=42, font=None, radius=10,
                 filled=False, bg=None, state="normal",
                 text_fill_color=None):
        accent = accent or Colors.CYAN
        self._bg = bg if bg is not None else parent.cget("bg")
        super().__init__(parent, width=width, height=height, bg=self._bg,
                         highlightthickness=0, bd=0)
        self.command = command
        self.accent = accent
        self.text = text
        self.radius = radius
        self.font = font or F(10, "bold")
        self.w = width
        self.h = height
        self.default_filled = filled
        self.text_fill_color = text_fill_color or Colors.BG
        self.enabled = (state == "normal")
        self._hovered = False
        self._render(filled)
        if self.enabled:
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)
            self.bind("<Button-1>", self._on_click)
            self.configure(cursor="hand2")

    def _on_enter(self, _e):
        self._hovered = True
        self._render(True)

    def _on_leave(self, _e):
        self._hovered = False
        self._render(self.default_filled)

    def _on_click(self, _e):
        if self.command:
            self.command()

    def _render(self, filled):
        self.delete("all")
        if not self.enabled:
            round_rect(self, 1.5, 1.5, self.w - 1.5, self.h - 1.5, self.radius,
                       fill=Colors.SURFACE_ALT, outline=Colors.BORDER, width=1.2)
            self.create_text(self.w / 2, self.h / 2, text=self.text,
                             fill=Colors.TEXT_DIM, font=self.font)
            return

        if filled:
            round_rect(self, 1.5, 1.5, self.w - 1.5, self.h - 1.5, self.radius,
                       fill=self.accent, outline=self.accent, width=1.4)
            round_rect(self, 3, 3, self.w - 3, self.h / 2 - 1, self.radius - 2,
                       fill=lerp(self.accent, "#FFFFFF", 0.18),
                       outline="", width=0)
            self.create_text(self.w / 2, self.h / 2, text=self.text,
                             fill=self.text_fill_color, font=self.font)
        else:
            round_rect(self, 1.5, 1.5, self.w - 1.5, self.h - 1.5, self.radius,
                       fill=self._bg, outline=self.accent, width=1.4)
            round_rect(self, 3, 3, self.w - 3, self.h - 3, self.radius - 2,
                       fill=lerp(self._bg, self.accent, 0.10),
                       outline="", width=0)
            self.create_text(self.w / 2, self.h / 2, text=self.text,
                             fill=self.accent, font=self.font)

    def disable(self):
        self.enabled = False
        self.unbind("<Enter>")
        self.unbind("<Leave>")
        self.unbind("<Button-1>")
        self.configure(cursor="arrow")
        self._render(False)


class NeonEntry(tk.Canvas):
    """Rounded entry with focus glow."""

    def __init__(self, parent, width=320, height=44, radius=10, show=None,
                 font=None, bg=None):
        self._bg = bg if bg is not None else parent.cget("bg")
        super().__init__(parent, width=width, height=height, bg=self._bg,
                         highlightthickness=0, bd=0)
        self.w = width
        self.h = height
        self.radius = radius
        self._draw_border(Colors.BORDER)

        self.entry = tk.Entry(
            self, show=show, font=font or F(11), bd=0, relief="flat",
            bg=Colors.SURFACE, fg=Colors.TEXT, insertbackground=Colors.CYAN,
            highlightthickness=0
        )
        self.create_window(width / 2, height / 2, window=self.entry,
                           width=width - 30, height=height - 18)

        self.entry.bind("<FocusIn>", lambda e: self._draw_border(Colors.CYAN))
        self.entry.bind("<FocusOut>", lambda e: self._draw_border(Colors.BORDER))

    def _draw_border(self, color):
        tk.Canvas.delete(self, "border")
        round_rect(self, 1.5, 1.5, self.w - 1.5, self.h - 1.5, self.radius,
                   fill=Colors.SURFACE, outline=color, width=1.6, tags="border")
        self.tag_lower("border")

    def get(self):
        return self.entry.get()

    def clear(self):
        self.entry.delete(0, "end")

    def set_text(self, string):
        self.entry.delete(0, "end")
        self.entry.insert(0, string)

    def focus(self):
        self.entry.focus_set()

    def bind_return(self, func):
        self.entry.bind("<Return>", func)


class StatTile(tk.Frame):
    """A compact KPI tile: big number, label, accent bar, glow outline."""

    def __init__(self, parent, label, value, accent, width=200, height=78):
        super().__init__(parent, bg=Colors.BG)
        self.canvas = tk.Canvas(self, width=width, height=height,
                                bg=Colors.BG, highlightthickness=0, bd=0)
        self.canvas.pack()
        w, h = width, height
        round_rect(self.canvas, 1.5, 1.5, w - 1.5, h - 1.5, 14,
                   fill=Colors.SURFACE, outline=Colors.BORDER, width=1.2)
        round_rect(self.canvas, 6, 10, 12, h - 10, 3,
                   fill=accent, outline=accent, width=0)
        self.canvas.create_text(30, 24, anchor="w", text=label.upper(),
                                fill=Colors.TEXT_MUTED, font=F(8, "bold"))
        self.canvas.create_text(30, 50, anchor="w", text=str(value),
                                fill=Colors.TEXT, font=F(20, "bold"))