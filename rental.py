# =====================================================================
#  main.py — APPLICATION LOGIC
# =====================================================================

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
from datetime import datetime
import qrcode
import os
import sys

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

from style import (
    Colors, Fonts, Layout, Theme,
    F, M, spaced,
    round_rect, draw_h_gradient, make_rounded_panel,
    center_toplevel,
    field_label, section_title, neon_badge,
    apply_dark_ttk,
    NeonButton, NeonEntry, StatTile,
)


# =====================================================================
#  QR CODE HELPER
# =====================================================================

def generate_qr_image(data, size=(120, 120)):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize(size, Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(img)


# =====================================================================
#  MAIN APPLICATION
# =====================================================================

class MotorcycleRentalSystem:

    def __init__(self, root):
        self.root = root
        self.root.title("GV Motorcycle Rental System")
        self.root.configure(bg=Colors.BG)
        self.root.minsize(1024, 640)

        try:
            self.root.attributes("-fullscreen", True)
        except tk.TclError:
            try:
                self.root.state("zoomed")
            except tk.TclError:
                self.root.geometry("1280x800")

        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))
        self.root.bind("<F11>", self._toggle_fullscreen)

        apply_dark_ttk(self.root)

        self.users = [{"username": "admin", "password": "1234", "role": "Admin"}]

        self.motorcycles = [
            {"id": "M001", "name": "Honda Click 125i", "rate": 500, "status": "Available", "image": "image/M001.jpg"},
            {"id": "M002", "name": "Yamaha Mio Sporty", "rate": 450, "status": "Available", "image": "image/M002.jpg"},
            {"id": "M003", "name": "Honda Beat", "rate": 400, "status": "Available", "image": "image/M003.jpg"},
            {"id": "M004", "name": "Yamaha Aerox", "rate": 700, "status": "Available", "image": "image/M004.jpg"},
            {"id": "M005", "name": "Honda ADV 160", "rate": 800, "status": "Available", "image": "image/M005.jpg"},
            {"id": "M006", "name": "Yamaha NMAX", "rate": 750, "status": "Available", "image": "image/M006.jpg"},
            {"id": "M007", "name": "Honda PCX 160", "rate": 750, "status": "Available", "image": "image/M007.jpg"},
            {"id": "M008", "name": "Suzuki Raider 150", "rate": 600, "status": "Available", "image": "image/M008.jpg"},
            {"id": "M009", "name": "Honda XRM 125", "rate": 550, "status": "Available", "image": "image/M009.jpg"},
            {"id": "M010", "name": "Yamaha Sniper 155", "rate": 650, "status": "Available", "image": "image/M010.jpg"},
            {"id": "M011", "name": "Honda CBR150R", "rate": 900, "status": "Available", "image": "image/M011.jpg"},
            {"id": "M012", "name": "Yamaha R15", "rate": 950, "status": "Available", "image": "image/M012.jpg"},
            {"id": "M013", "name": "Kawasaki Ninja 400", "rate": 1200, "status": "Available", "image": "image/M013.jpg"},
            {"id": "M014", "name": "Yamaha MT-15", "rate": 850, "status": "Available", "image": "image/M014.jpg"},
            {"id": "M015", "name": "Honda CB150R", "rate": 800, "status": "Available", "image": "image/M015.jpg"},
            {"id": "M016", "name": "Suzuki Burgman Street", "rate": 550, "status": "Available", "image": "image/M016.jpg"},
            {"id": "M017", "name": "Yamaha Fazzio", "rate": 500, "status": "Available", "image": "image/M017.jpg"},
            {"id": "M018", "name": "Honda Airblade 160", "rate": 700, "status": "Available", "image": "image/M018.jpg"},
            {"id": "M019", "name": "Kawasaki Rouser NS160", "rate": 700, "status": "Available", "image": "image/M019.jpg"},
            {"id": "M020", "name": "Suzuki Raider R150", "rate": 650, "status": "Available", "image": "image/M020.jpg"}
        ]

        self.rentals = []
        self.return_requests = []
        self.current_user = None

        self.login_screen()

    # ================= FULLSCREEN TOGGLE =================

    def _toggle_fullscreen(self, _event=None):
        try:
            current = self.root.attributes("-fullscreen")
            self.root.attributes("-fullscreen", not current)
        except tk.TclError:
            pass

    # ================= LOGIN =================

    def login_screen(self):
        for w in self.root.winfo_children():
            w.destroy()
        self.root.configure(bg=Colors.BG)

        bg_frame = tk.Frame(self.root, bg=Colors.BG)
        bg_frame.pack(fill="both", expand=True)

        shell = tk.Frame(bg_frame, bg=Colors.BG)
        shell.place(relx=0.5, rely=0.5, anchor="center")

        brand = tk.Frame(shell, bg=Colors.BG)
        brand.pack(side="left", padx=(0, 24), anchor="n")

        brand_canvas = tk.Canvas(brand, width=420, height=520, bg=Colors.BG,
                                 highlightthickness=0, bd=0)
        brand_canvas.pack()
        round_rect(brand_canvas, 2, 2, 418, 518, 24,
                   fill=Colors.SURFACE, outline=Colors.CYAN_DIM, width=1.4)

        for i in range(40):
            t = i / 39
            c = _lerp_color(Colors.CYAN, Colors.MAGENTA, t)
            brand_canvas.create_rectangle(30 + i * 9, 40, 30 + i * 9 + 9, 46,
                                          fill=c, outline=c)

        brand_canvas.create_text(40, 100, anchor="w", text="◆",
                                 font=("Segoe UI", 30), fill=Colors.CYAN)
        brand_canvas.create_text(80, 100, anchor="w", text="GV MOTORCYCLE",
                                 font=F(20, "bold"), fill=Colors.TEXT)
        brand_canvas.create_text(40, 148, anchor="w",
                                 text=spaced("RENTAL SYSTEM"),
                                 font=F(13, "bold"), fill=Colors.CYAN)

        brand_canvas.create_text(
            40, 210, anchor="w", justify="left",
            text=("A next-gen rental platform for\n"
                  "scooters, sportbikes, and street\n"
                  "machines — book, ride, return."),
            font=F(11), fill=Colors.TEXT_MUTED
        )

        feats = [
            ("Real-time fleet status", Colors.GREEN),
            ("Instant booking & returns", Colors.AMBER),
            ("Admin analytics dashboard", Colors.MAGENTA),
        ]
        y = 300
        for label, color in feats:
            brand_canvas.create_oval(40, y - 4, 48, y + 4, fill=color, outline=color)
            brand_canvas.create_text(60, y, anchor="w", text=label,
                                     font=F(10), fill=Colors.TEXT)
            y += 34

        brand_canvas.create_oval(40, 470, 48, 478,
                                 fill=Colors.GREEN, outline=Colors.GREEN)
        brand_canvas.create_text(60, 474, anchor="w",
                                 text="SYSTEM ONLINE", font=F(9, "bold"),
                                 fill=Colors.GREEN)

        canvas, inner = make_rounded_panel(
            shell, Layout.LOGIN_PANEL_W, Layout.LOGIN_PANEL_H, radius=22,
            fill=Colors.SURFACE, outline=Colors.CYAN_DIM, bg=Colors.BG
        )
        canvas.pack(side="left")

        tk.Label(inner, text=spaced("SIGN IN"), font=F(20, "bold"),
                 bg=Colors.SURFACE, fg=Colors.TEXT).pack(anchor="w")
        tk.Label(inner, text="Enter your credentials to continue", font=F(9),
                 bg=Colors.SURFACE, fg=Colors.TEXT_MUTED).pack(anchor="w", pady=(4, 22))

        field_label(inner, "USERNAME")
        self.username_field = NeonEntry(inner, width=Layout.LOGIN_FIELD_W,
                                        height=Layout.LOGIN_FIELD_H, bg=Colors.SURFACE)
        self.username_field.pack()
        self.username_entry = self.username_field.entry

        field_label(inner, "PASSWORD")
        self.password_field = NeonEntry(inner, width=Layout.LOGIN_FIELD_W,
                                        height=Layout.LOGIN_FIELD_H, show="*",
                                        bg=Colors.SURFACE)
        self.password_field.pack()
        self.password_entry = self.password_field.entry
        self.password_field.bind_return(lambda e: self.login())

        tk.Frame(inner, bg=Colors.SURFACE, height=14).pack()

        NeonButton(inner, "LOG IN  →", command=self.login, accent=Colors.CYAN,
                   width=Layout.LOGIN_FIELD_W, height=48, filled=True,
                   bg=Colors.SURFACE).pack(pady=(0, 10))

        NeonButton(inner, "CREATE AN ACCOUNT", command=self.register_screen,
                   accent=Colors.GREEN, width=Layout.LOGIN_FIELD_W, height=48,
                   bg=Colors.SURFACE).pack()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        for user in self.users:
            if user["username"] == username and user["password"] == password:
                self.current_user = user
                if user["role"] == "Admin":
                    self.admin_dashboard()
                else:
                    self.client_dashboard()
                return
        messagebox.showerror("Login Failed", "Incorrect username or password.")

    # ================= REGISTER =================

    def register_screen(self):
        for w in self.root.winfo_children():
            w.destroy()
        self.root.configure(bg=Colors.BG)

        bg_frame = tk.Frame(self.root, bg=Colors.BG)
        bg_frame.pack(fill="both", expand=True)

        outer = tk.Frame(bg_frame, bg=Colors.BG)
        outer.place(relx=0.5, rely=0.5, anchor="center")

        canvas, inner = make_rounded_panel(
            outer, Layout.REGISTER_PANEL_W, Layout.REGISTER_PANEL_H, radius=22,
            fill=Colors.SURFACE, outline=Colors.GREEN_DIM, bg=Colors.BG
        )
        canvas.pack()

        tk.Label(inner, text="✦", font=("Segoe UI", 26),
                 bg=Colors.SURFACE, fg=Colors.GREEN).pack(pady=(4, 6))

        tk.Label(inner, text=spaced("CREATE ACCOUNT"), font=F(18, "bold"),
                 bg=Colors.SURFACE, fg=Colors.TEXT).pack()
        tk.Label(inner, text="Register a new client profile", font=F(9),
                 bg=Colors.SURFACE, fg=Colors.TEXT_MUTED).pack(pady=(4, 22))

        field_label(inner, "USERNAME")
        self.reg_username_field = NeonEntry(inner, width=Layout.LOGIN_FIELD_W,
                                            height=Layout.LOGIN_FIELD_H,
                                            bg=Colors.SURFACE)
        self.reg_username_field.pack()
        self.reg_username = self.reg_username_field.entry

        field_label(inner, "PASSWORD")
        self.reg_password_field = NeonEntry(inner, width=Layout.LOGIN_FIELD_W,
                                            height=Layout.LOGIN_FIELD_H, show="*",
                                            bg=Colors.SURFACE)
        self.reg_password_field.pack()
        self.reg_password = self.reg_password_field.entry
        self.reg_password_field.bind_return(lambda e: self.register())

        tk.Frame(inner, bg=Colors.SURFACE, height=16).pack()

        NeonButton(inner, "REGISTER  ✓", command=self.register, accent=Colors.GREEN,
                   width=Layout.LOGIN_FIELD_W, height=48, filled=True,
                   bg=Colors.SURFACE).pack(pady=(0, 10))

        NeonButton(inner, "← BACK TO LOGIN", command=self.login_screen,
                   accent=Colors.TEXT_MUTED, width=Layout.LOGIN_FIELD_W, height=48,
                   bg=Colors.SURFACE).pack()

    def register(self):
        username = self.reg_username.get()
        password = self.reg_password.get()
        if username == "" or password == "":
            messagebox.showwarning("Missing Information",
                                   "Please enter username and password.")
            return
        for user in self.users:
            if user["username"] == username:
                messagebox.showerror("Error", "Username already exists.")
                return
        self.users.append({"username": username, "password": password, "role": "Client"})
        messagebox.showinfo("Success", "Account registered successfully!")
        self.login_screen()

    # ================= HEADER =================

    def build_header(self, title, subtitle, buttons,
                     c1=Colors.HEADER_1, c2=Colors.HEADER_2):
        canvas = tk.Canvas(self.root, height=Layout.HEADER_H,
                           highlightthickness=0, bd=0, bg=Colors.BG)
        canvas.pack(fill="x")

        btn_frame = tk.Frame(canvas, bg=c2)
        for text, accent, command in buttons:
            NeonButton(
                btn_frame, text, command=command, accent=accent,
                width=140, height=38, font=F(9, "bold"), bg=c2
            ).pack(side="left", padx=5)

        def _redraw(_event=None):
            canvas.delete("all")
            w = max(canvas.winfo_width(), 1)
            h = Layout.HEADER_H
            draw_h_gradient(canvas, w, h, c1, c2)
            canvas.create_rectangle(0, h - 2, w, h,
                                    fill=Colors.CYAN, outline=Colors.CYAN)
            for x in range(0, w, 6):
                canvas.create_line(x, 0, x, h,
                                   fill=_lerp_color(c1, "#FFFFFF", 0.02))
            canvas.create_text(34, 30, anchor="w", text="◆",
                               font=("Segoe UI", 16), fill=Colors.CYAN)
            canvas.create_text(60, 30, anchor="w", text=spaced(title),
                               font=F(14, "bold"), fill=Colors.TEXT)
            canvas.create_text(60, 56, anchor="w", text=subtitle,
                               font=F(9), fill=Colors.TEXT_MUTED)
            canvas.delete("btns")
            canvas.create_window(w - 26, h / 2, anchor="e",
                                 window=btn_frame, tags="btns")

        canvas.bind("<Configure>", _redraw)
        return canvas

    # ================= CLIENT DASHBOARD =================

    def client_dashboard(self):
        for w in self.root.winfo_children():
            w.destroy()
        self.root.configure(bg=Colors.BG)

        self.build_header(
            "GV MOTORCYCLE RENTAL",
            f"Signed in as {self.current_user['username']} — Client",
            [
                ("MY RENTALS", Colors.GREEN, self.view_my_rentals),
                ("RETURN RENT", Colors.AMBER, self.return_rent),
                ("LOGOUT", Colors.RED, self.logout),
            ],
        )

        top = tk.Frame(self.root, bg=Colors.BG)
        top.pack(fill="x", padx=28, pady=(20, 6))

        left = tk.Frame(top, bg=Colors.BG)
        left.pack(side="left", anchor="w")
        section_title(
            left, "Available Motorcycles",
            accent=Colors.CYAN,
            subtitle="Select a unit below and complete the rental form"
        ).pack(anchor="w")

        right = tk.Frame(top, bg=Colors.BG)
        right.pack(side="right", anchor="e")

        available = sum(1 for b in self.motorcycles if b["status"] == "Available")
        rented = sum(1 for b in self.motorcycles if b["status"] == "Rented")

        StatTile(right, "Available", available, Colors.GREEN,
                 width=150, height=70).pack(side="left", padx=6)
        StatTile(right, "Rented", rented, Colors.RED,
                 width=150, height=70).pack(side="left", padx=6)

        container = tk.Frame(self.root, bg=Colors.BG)
        container.pack(fill="both", expand=True, padx=22, pady=12)

        canvas = tk.Canvas(container, bg=Colors.BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical",
                                  command=canvas.yview,
                                  style="Dark.Vertical.TScrollbar")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        card_frame = tk.Frame(canvas, bg=Colors.BG)
        canvas.create_window((0, 0), window=card_frame, anchor="nw")
        card_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        def _on_mousewheel(event):
            if any(isinstance(w, tk.Toplevel) and w.winfo_exists()
                   for w in self.root.winfo_children()):
                return "break"
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.client_images = []

        cols = (Layout.CARD_COLS_WIDE if self.root.winfo_width() >= 1400
                else Layout.CARD_COLS_NARROW)

        for index, bike in enumerate(self.motorcycles):
            row, col = divmod(index, cols)
            card = self._build_bike_card(card_frame, bike)
            card.grid(row=row, column=col, padx=14, pady=14)

    def _build_bike_card(self, parent, bike):
        W, H, radius = Layout.CARD_W, Layout.CARD_H, Layout.CARD_RADIUS
        is_available = bike["status"] == "Available"
        accent = Colors.CYAN if is_available else Colors.RED

        wrapper = tk.Frame(parent, bg=Colors.BG)

        canvas, content = make_rounded_panel(
            wrapper, W, H, radius=radius, fill=Colors.SURFACE,
            outline=Colors.BORDER, bg=Colors.BG, outline_width=1.4
        )
        canvas.pack()

        def on_enter(_e):
            canvas.delete("border")
            round_rect(canvas, 2, 2, W - 2, H - 2, radius,
                       fill=Colors.SURFACE, outline=accent, width=2.0,
                       tags="border")
            canvas.tag_lower("border")

        def on_leave(_e):
            canvas.delete("border")
            round_rect(canvas, 2, 2, W - 2, H - 2, radius,
                       fill=Colors.SURFACE, outline=Colors.BORDER, width=1.4,
                       tags="border")
            canvas.tag_lower("border")

        def bind_all_recursive(widget):
            widget.bind("<Enter>", on_enter, add="+")
            widget.bind("<Leave>", on_leave, add="+")
            for child in widget.winfo_children():
                bind_all_recursive(child)

        image_frame = tk.Frame(content, bg=Colors.SURFACE_ALT,
                               width=220, height=140)
        image_frame.pack(pady=(6, 10))
        image_frame.pack_propagate(False)

        try:
            image = Image.open(bike["image"])
            image.thumbnail((210, 130), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.client_images.append(photo)
            tk.Label(image_frame, image=photo, bg=Colors.SURFACE_ALT).place(
                relx=0.5, rely=0.5, anchor="center"
            )
        except Exception:
            tk.Label(image_frame, text="🏍\nNO IMAGE", font=F(13, "bold"),
                     bg=Colors.SURFACE_ALT, fg=Colors.CYAN_DIM,
                     justify="center").place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(content, text=bike["id"], font=M(8, "bold"),
                 bg=Colors.SURFACE, fg=Colors.TEXT_DIM).pack()

        tk.Label(content, text=bike["name"], font=F(12, "bold"),
                 bg=Colors.SURFACE, fg=Colors.TEXT).pack(pady=(2, 0))

        tk.Label(content, text=f"₱{bike['rate']} / day", font=M(12, "bold"),
                 bg=Colors.SURFACE, fg=Colors.CYAN).pack(pady=(4, 8))

        neon_badge(content, bike["status"],
                   Colors.GREEN if is_available else Colors.RED,
                   bg=Colors.SURFACE).pack()

        btn = NeonButton(
            content, "SELECT  →",
            command=lambda b=bike: self.rent_motorcycle(b),
            accent=Colors.CYAN, width=190, height=38, font=F(9, "bold"),
            bg=Colors.SURFACE, filled=is_available
        )
        btn.pack(pady=(10, 0))
        if not is_available:
            btn.disable()

        bind_all_recursive(wrapper)
        return wrapper

    # ================= RENT MOTORCYCLE =================

    def rent_motorcycle(self, bike):
        if bike["status"] != "Available":
            messagebox.showerror("Unavailable", "This motorcycle is currently rented.")
            return

        window = tk.Toplevel(self.root)
        window.title("Rent Motorcycle")
        window.configure(bg=Colors.BG)
        window.resizable(False, False)

        screen_w = window.winfo_screenwidth()
        screen_h = window.winfo_screenheight()

        win_w = min(Layout.RENT_WINDOW_W, screen_w - 40)
        win_h = screen_h - 80

        x = (screen_w - win_w) // 2
        y = 40
        window.geometry(f"{win_w}x{win_h}+{x}+{y}")

        container = tk.Frame(window, bg=Colors.BG)
        container.pack(fill="both", expand=True)

        outer_canvas = tk.Canvas(container, bg=Colors.BG, highlightthickness=0, bd=0)
        outer_canvas.pack(side="left", fill="both", expand=True)

        content = tk.Frame(outer_canvas, bg=Colors.BG)
        outer_canvas.create_window((0, 0), window=content, anchor="nw")

        def _update_scrollregion(_e=None):
            outer_canvas.configure(scrollregion=outer_canvas.bbox("all"))
            cw = outer_canvas.winfo_width()
            fw = content.winfo_reqwidth()
            if fw < cw:
                outer_canvas.coords(1, (cw - fw) // 2, 0)
            else:
                outer_canvas.coords(1, 0, 0)

        content.bind("<Configure>", _update_scrollregion)
        outer_canvas.bind("<Configure>", _update_scrollregion)

        def _rent_mousewheel(event):
            outer_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"

        window.bind("<MouseWheel>", _rent_mousewheel)
        window.bind("<Button-4>", lambda e: (outer_canvas.yview_scroll(-1, "units"), "break")[1])
        window.bind("<Button-5>", lambda e: (outer_canvas.yview_scroll(1, "units"), "break")[1])

        section_title(
            content, "Rent Motorcycle", accent=Colors.CYAN, size=15,
            subtitle="Confirm the details below to book this unit"
        ).pack(pady=(22, 14), padx=40, anchor="w")

        image_holder = tk.Frame(content, bg=Colors.SURFACE_ALT, width=320, height=180,
                                highlightthickness=1, highlightbackground=Colors.BORDER)
        image_holder.pack(pady=4)
        image_holder.pack_propagate(False)

        try:
            image = Image.open(bike["image"])
            image.thumbnail((310, 170), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            window.image_reference = photo
            tk.Label(image_holder, image=photo, bg=Colors.SURFACE_ALT).place(
                relx=0.5, rely=0.5, anchor="center"
            )
        except Exception:
            tk.Label(image_holder, text="🏍 NO IMAGE", font=F(14, "bold"),
                     bg=Colors.SURFACE_ALT, fg=Colors.CYAN_DIM).place(
                relx=0.5, rely=0.5, anchor="center")

        tk.Label(content, text=bike["name"], font=F(16, "bold"),
                 bg=Colors.BG, fg=Colors.TEXT).pack(pady=(14, 2))
        tk.Label(content, text=f"₱{bike['rate']} per day", font=M(12),
                 bg=Colors.BG, fg=Colors.CYAN).pack()

        qr_frame = tk.Frame(content, bg=Colors.SURFACE, padx=10, pady=10,
                            highlightthickness=1, highlightbackground=Colors.BORDER)
        qr_frame.pack(pady=(12, 6))

        qr_data = (
            f"Motorcycle: {bike['name']}\n"
            f"ID: {bike['id']}\n"
            f"Rate: ₱{bike['rate']}/day\n"
            f"Status: {bike['status']}\n"
            f"Terms: Valid ID required. Late returns subject to extra fees."
        )

        try:
            qr_photo = generate_qr_image(qr_data, size=(110, 110))
            qr_frame.qr_photo = qr_photo
            tk.Label(qr_frame, image=qr_photo, bg=Colors.SURFACE).pack()
            tk.Label(qr_frame, text="SCAN FOR DETAILS", font=F(7, "bold"),
                     bg=Colors.SURFACE, fg=Colors.TEXT_MUTED).pack(pady=(4, 0))
        except Exception:
            tk.Label(qr_frame, text="QR Unavailable", bg=Colors.SURFACE,
                     fg=Colors.RED, font=F(9)).pack()

        form = tk.Frame(content, bg=Colors.BG)
        form.pack(pady=10, padx=60, fill="x")

        FIELD_W, FIELD_H = Layout.FIELD_W, Layout.FIELD_H

        field_label(form, "CONTACT NUMBER")
        contact_field = NeonEntry(form, width=FIELD_W, height=FIELD_H, bg=Colors.BG)
        contact_field.pack()
        contact_entry = contact_field.entry

        field_label(form, "RENTAL DAYS")
        days_field = NeonEntry(form, width=FIELD_W, height=FIELD_H, bg=Colors.BG)
        days_field.pack()
        days_entry = days_field.entry

        # ============================================================
        #  ID / DRIVER'S LICENSE ATTACHMENT SECTION (VERTICAL LAYOUT)
        # ============================================================
        field_label(form, "VALID ID / DRIVER'S LICENSE")

        id_container = tk.Frame(form, bg=Colors.BG)
        id_container.pack(fill="x", pady=(0, 4))

        # Row 1: status text on its own line (full width)
        id_status = tk.Label(
            id_container, text="No ID selected",
            font=F(9), bg=Colors.BG, fg=Colors.TEXT_MUTED,
            anchor="w", justify="left"
        )
        id_status.pack(fill="x", anchor="w", pady=(0, 8))

        # Row 2: buttons on their own line (left-aligned, full width)
        id_buttons = tk.Frame(id_container, bg=Colors.BG)
        id_buttons.pack(fill="x", anchor="w")

        id_path_var = tk.StringVar(value="")

        def _short_name(path, limit=40):
            name = os.path.basename(path)
            return name if len(name) <= limit else name[: limit - 1] + "…"

        def _bring_window_front():
            try:
                window.deiconify()
                window.lift()
                window.attributes("-topmost", True)
                window.after(200, lambda: window.attributes("-topmost", False))
                window.focus_force()
            except tk.TclError:
                pass

        def _rebuild_id_buttons():
            for w in id_buttons.winfo_children():
                w.destroy()

            NeonButton(
                id_buttons, "◉  CAPTURE ID", command=capture_id,
                accent=Colors.AMBER, width=160, height=42, bg=Colors.BG
            ).pack(side="left", padx=(0, 8))

            NeonButton(
                id_buttons, "UPLOAD ID / LICENSE", command=upload_id,
                accent=Colors.MAGENTA, width=210, height=42, bg=Colors.BG
            ).pack(side="left", padx=(0, 8))

            if id_path_var.get().strip() != "":
                NeonButton(
                    id_buttons, "✕  REMOVE", command=remove_id,
                    accent=Colors.RED, width=150, height=42, bg=Colors.BG
                ).pack(side="left", padx=(0, 8))

        def _set_id(path):
            id_path_var.set(path)
            id_status.config(
                text=f"Selected: {_short_name(path)}",
                fg=Colors.GREEN
            )
            _rebuild_id_buttons()

        def _clear_id():
            id_path_var.set("")
            id_status.config(text="No ID selected", fg=Colors.TEXT_MUTED)
            _rebuild_id_buttons()

        def upload_id():
            path = filedialog.askopenfilename(
                parent=window,
                title="Select Valid ID / Driver's License",
                filetypes=[
                    ("ID Images", "*.png *.jpg *.jpeg *.webp"),
                    ("PDF Documents", "*.pdf"),
                    ("All Files", "*.*")
                ]
            )
            _bring_window_front()
            if path:
                _set_id(path)

        def remove_id():
            if id_path_var.get().strip() == "":
                return
            answer = messagebox.askyesno(
                "Remove Attachment",
                "Remove the currently attached ID / license?"
            )
            # Bring the rent form back to the front after the dialog closes.
            _bring_window_front()
            if not answer:
                return
            _clear_id()

        def capture_id():
            if not HAS_CV2:
                messagebox.showwarning(
                    "Camera Not Available",
                    "OpenCV is not installed, so the webcam cannot be used.\n\n"
                    "Install it with:  pip install opencv-python"
                )
                _bring_window_front()
                return

            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                messagebox.showerror(
                    "Camera Error",
                    "Could not open the webcam. Make sure no other app is using it."
                )
                _bring_window_front()
                return

            capture_win = tk.Toplevel(window)
            capture_win.title("Capture ID / Driver's License")
            capture_win.configure(bg=Colors.BG)
            capture_win.resizable(False, False)
            capture_win.transient(window)
            center_toplevel(capture_win, window, 660, 580)

            section_title(
                capture_win, "Capture ID", accent=Colors.MAGENTA, size=14,
                subtitle="Hold your ID steady in front of the camera"
            ).pack(pady=(16, 8), padx=20, anchor="w")

            video_label = tk.Label(capture_win, bg=Colors.SURFACE)
            video_label.pack(padx=20, pady=6)

            capture_win.lift()
            capture_win.focus_force()

            state = {"running": True}
            last_frame = {"img": None}

            def update_frame():
                if not state["running"]:
                    return
                ok, frame = cap.read()
                if ok:
                    frame = cv2.flip(frame, 1)
                    last_frame["img"] = frame
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(rgb)
                    img.thumbnail((600, 420), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    video_label.configure(image=photo)
                    video_label.image = photo
                capture_win.after(20, update_frame)

            def stop_camera():
                state["running"] = False
                try:
                    cap.release()
                except Exception:
                    pass

            def do_capture():
                if last_frame["img"] is None:
                    messagebox.showwarning("No Frame", "No camera frame available yet.")
                    return

                os.makedirs("captured_ids", exist_ok=True)
                filename = (
                    f"captured_ids/ID_{self.current_user['username']}_"
                    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                )
                cv2.imwrite(filename, last_frame["img"])

                stop_camera()
                capture_win.destroy()

                _set_id(filename)
                _bring_window_front()
                messagebox.showinfo(
                    "ID Captured",
                    f"Captured ID saved as:\n{os.path.basename(filename)}"
                )

            def cancel_capture():
                stop_camera()
                capture_win.destroy()
                _bring_window_front()

            btn_row = tk.Frame(capture_win, bg=Colors.BG)
            btn_row.pack(pady=14)
            NeonButton(btn_row, "◉  CAPTURE", command=do_capture,
                       accent=Colors.GREEN, width=200, height=46, filled=True,
                       bg=Colors.BG).pack(side="left", padx=8)
            NeonButton(btn_row, "✕  CANCEL", command=cancel_capture,
                       accent=Colors.RED, width=160, height=46, filled=True,
                       bg=Colors.BG).pack(side="left", padx=8)

            capture_win.protocol("WM_DELETE_WINDOW", cancel_capture)
            update_frame()

        # Build initial button row
        _rebuild_id_buttons()

        # ============================================================
        #  PROCEED TO PAYMENT
        # ============================================================

        def proceed_to_payment():
            contact = contact_entry.get().strip()
            if contact == "":
                messagebox.showwarning("Missing Information",
                                       "Please enter contact number.")
                return
            try:
                days = int(days_entry.get())
                if days <= 0:
                    raise ValueError
            except Exception:
                messagebox.showerror("Invalid", "Please enter valid rental days.")
                return

            id_path = id_path_var.get().strip()
            if id_path == "":
                messagebox.showwarning(
                    "ID Required",
                    "Please upload or capture your valid ID / driver's license."
                )
                return

            total = bike["rate"] * days
            window.withdraw()
            self.payment_window(
                parent=self.root,
                bike=bike,
                contact=contact,
                days=days,
                total=total,
                id_path=id_path,
                on_success=lambda: (window.destroy(), self.client_dashboard()),
                on_cancel=lambda: window.deiconify()
            )

        NeonButton(content, "PROCEED TO PAYMENT  →", command=proceed_to_payment,
                   accent=Colors.CYAN, width=FIELD_W, height=52, filled=True,
                   bg=Colors.BG).pack(pady=(18, 26))

    # ================= PAYMENT WINDOW =================

    def payment_window(self, parent, bike, contact, days, total, id_path,
                       on_success, on_cancel):
        pay_win = tk.Toplevel(parent)
        pay_win.title("Payment")
        pay_win.configure(bg=Colors.BG)
        pay_win.resizable(False, False)
        pay_win.transient(parent)
        pay_win.grab_set()

        screen_w = pay_win.winfo_screenwidth()
        screen_h = pay_win.winfo_screenheight()
        win_w = min(Layout.PAYMENT_WINDOW_W + 120, screen_w - 40)
        win_h = min(Layout.PAYMENT_WINDOW_H + 60, screen_h - 80)
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        pay_win.geometry(f"{win_w}x{win_h}+{x}+{y}")

        canvas = tk.Canvas(pay_win, bg=Colors.BG, highlightthickness=0, bd=0)
        canvas.pack(side="left", fill="both", expand=True)

        content = tk.Frame(canvas, bg=Colors.BG)
        canvas.create_window((0, 0), window=content, anchor="nw")

        def _update_pay_scroll(_e=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            cw = canvas.winfo_width()
            fw = content.winfo_reqwidth()
            if fw < cw:
                canvas.coords(1, (cw - fw) // 2, 0)
            else:
                canvas.coords(1, 0, 0)

        content.bind("<Configure>", _update_pay_scroll)
        canvas.bind("<Configure>", _update_pay_scroll)

        def _pay_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"

        pay_win.bind("<MouseWheel>", _pay_mousewheel)
        pay_win.bind("<Button-4>", lambda e: (canvas.yview_scroll(-1, "units"), "break")[1])
        pay_win.bind("<Button-5>", lambda e: (canvas.yview_scroll(1, "units"), "break")[1])

        section_title(
            content, "Payment", accent=Colors.GREEN, size=16,
            subtitle="Review your order and choose a payment method"
        ).pack(pady=(22, 14), padx=40, anchor="w")

        summary_outer = tk.Frame(content, bg=Colors.BORDER, padx=1, pady=1)
        summary_outer.pack(padx=40, pady=(0, 14), fill="x")

        summary = tk.Frame(summary_outer, bg=Colors.SURFACE, padx=20, pady=16)
        summary.pack(fill="both", expand=True)

        tk.Label(summary, text="ORDER SUMMARY", font=F(8, "bold"),
                 bg=Colors.SURFACE, fg=Colors.TEXT_MUTED).pack(anchor="w")

        def summary_row(label, value, value_color=Colors.TEXT, bold=False):
            row = tk.Frame(summary, bg=Colors.SURFACE)
            row.pack(fill="x", pady=(8, 0))
            tk.Label(row, text=label, font=F(10),
                     bg=Colors.SURFACE, fg=Colors.TEXT_MUTED).pack(side="left")
            tk.Label(row, text=value,
                     font=M(11, "bold") if bold else M(10),
                     bg=Colors.SURFACE, fg=value_color).pack(side="right")

        summary_row("Motorcycle", bike["name"])
        summary_row("Unit ID", bike["id"])
        summary_row("Contact", contact)
        summary_row("Rate per day", f"₱{bike['rate']}")
        summary_row("Rental days", str(days))

        tk.Frame(summary, bg=Colors.BORDER, height=1).pack(fill="x", pady=(12, 0))

        summary_row("TOTAL", f"₱{total}", value_color=Colors.CYAN, bold=True)

        tk.Label(content, text="SELECT PAYMENT METHOD", font=F(8, "bold"),
                 bg=Colors.BG, fg=Colors.TEXT_MUTED).pack(anchor="w", padx=40, pady=(16, 6))

        method_frame = tk.Frame(content, bg=Colors.BG)
        method_frame.pack(padx=40, fill="x")

        method_var = tk.StringVar(value="Cash")
        method_buttons = {}

        def select_method(name):
            method_var.set(name)
            for m, (btn, accent) in method_buttons.items():
                if m == name:
                    btn.accent = accent
                    btn._render(True)
                else:
                    btn._render(False)

        def make_method_button(parent, name, accent, subtitle):
            wrapper = tk.Frame(parent, bg=Colors.BG)
            wrapper.pack(side="left", expand=True, fill="x", padx=4)

            btn = NeonButton(
                wrapper, name.upper(), command=lambda n=name: select_method(n),
                accent=accent, width=160, height=64, font=F(11, "bold"),
                bg=Colors.BG, filled=(method_var.get() == name), radius=12
            )
            btn.pack()

            tk.Label(wrapper, text=subtitle, font=F(7),
                     bg=Colors.BG, fg=Colors.TEXT_DIM).pack(pady=(4, 0))

            method_buttons[name] = (btn, accent)

        make_method_button(method_frame, "Cash", Colors.GREEN, "Pay at the counter")
        make_method_button(method_frame, "GCash", Colors.CYAN, "Send via e-wallet")
        make_method_button(method_frame, "Card", Colors.MAGENTA, "Debit / credit card")

        dynamic_frame = tk.Frame(content, bg=Colors.BG)
        dynamic_frame.pack(padx=40, pady=(18, 0), fill="x")

        ref_entry_holder = {"widget": None}
        card_fields = {}

        def rebuild_dynamic_fields(*_):
            for child in dynamic_frame.winfo_children():
                child.destroy()
            card_fields.clear()
            ref_entry_holder["widget"] = None

            method = method_var.get()

            if method == "Cash":
                tk.Label(dynamic_frame,
                         text="Please prepare the exact amount upon pickup.",
                         font=F(10), bg=Colors.BG, fg=Colors.TEXT_MUTED).pack(anchor="w")

            elif method == "GCash":
                tk.Label(dynamic_frame, text="GCASH NUMBER", font=F(8, "bold"),
                         bg=Colors.BG, fg=Colors.TEXT_MUTED).pack(anchor="w")
                gcash_number = NeonEntry(dynamic_frame, width=500, height=46, bg=Colors.BG)
                gcash_number.pack(pady=(4, 10))
                card_fields["gcash_number"] = gcash_number

                tk.Label(dynamic_frame, text="REFERENCE NUMBER", font=F(8, "bold"),
                         bg=Colors.BG, fg=Colors.TEXT_MUTED).pack(anchor="w")
                ref_entry_holder["widget"] = NeonEntry(dynamic_frame, width=500,
                                                       height=46, bg=Colors.BG)
                ref_entry_holder["widget"].pack(pady=(4, 0))

            elif method == "Card":
                tk.Label(dynamic_frame, text="CARD NUMBER", font=F(8, "bold"),
                         bg=Colors.BG, fg=Colors.TEXT_MUTED).pack(anchor="w")
                card_number = NeonEntry(dynamic_frame, width=500, height=46, bg=Colors.BG)
                card_number.pack(pady=(4, 10))
                card_fields["card_number"] = card_number

                row = tk.Frame(dynamic_frame, bg=Colors.BG)
                row.pack(fill="x")
                left = tk.Frame(row, bg=Colors.BG)
                left.pack(side="left", fill="x", expand=True, padx=(0, 6))
                right = tk.Frame(row, bg=Colors.BG)
                right.pack(side="left", fill="x", expand=True, padx=(6, 0))

                tk.Label(left, text="EXPIRY (MM/YY)", font=F(8, "bold"),
                         bg=Colors.BG, fg=Colors.TEXT_MUTED).pack(anchor="w")
                expiry = NeonEntry(left, width=240, height=46, bg=Colors.BG)
                expiry.pack(pady=(4, 0))
                card_fields["expiry"] = expiry

                tk.Label(right, text="CVV", font=F(8, "bold"),
                         bg=Colors.BG, fg=Colors.TEXT_MUTED).pack(anchor="w")
                cvv = NeonEntry(right, width=240, height=46, bg=Colors.BG)
                cvv.pack(pady=(4, 0))
                card_fields["cvv"] = cvv

        method_var.trace_add("write", rebuild_dynamic_fields)
        rebuild_dynamic_fields()

        btn_row = tk.Frame(content, bg=Colors.BG)
        btn_row.pack(padx=40, pady=(24, 30), fill="x")

        def cancel_payment():
            pay_win.grab_release()
            pay_win.destroy()
            on_cancel()

        def confirm_payment():
            method = method_var.get()

            if method == "GCash":
                num = card_fields.get("gcash_number")
                ref_widget = ref_entry_holder["widget"]
                if num is None or num.get().strip() == "":
                    messagebox.showwarning("Missing Information",
                                           "Please enter your GCash number.")
                    return
                if ref_widget is None or ref_widget.get().strip() == "":
                    messagebox.showwarning("Missing Information",
                                           "Please enter the GCash reference number.")
                    return
                ref = ref_widget.get().strip()

            elif method == "Card":
                num = card_fields.get("card_number")
                exp = card_fields.get("expiry")
                cvv = card_fields.get("cvv")
                if num is None or num.get().strip() == "":
                    messagebox.showwarning("Missing Information",
                                           "Please enter your card number.")
                    return
                if exp is None or exp.get().strip() == "":
                    messagebox.showwarning("Missing Information",
                                           "Please enter the expiry date.")
                    return
                if cvv is None or cvv.get().strip() == "":
                    messagebox.showwarning("Missing Information",
                                           "Please enter the CVV.")
                    return
                ref = f"CARD-{num.get().strip()[-4:]}"

            else:
                ref = "CASH-ON-PICKUP"

            rental = {
                "username": self.current_user["username"],
                "customer": self.current_user["username"],
                "contact": contact,
                "motorcycle": bike["name"],
                "motorcycle_id": bike["id"],
                "days": days,
                "rate": bike["rate"],
                "total": total,
                "payment_method": method,
                "payment_ref": ref,
                "id_document": id_path,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "Rented",
            }
            self.rentals.append(rental)
            bike["status"] = "Rented"

            messagebox.showinfo(
                "Payment Successful",
                f"Payment Method: {method}\n"
                f"Reference: {ref}\n\n"
                f"Motorcycle: {bike['name']}\n"
                f"Days: {days}\n"
                f"Rate: ₱{bike['rate']}\n"
                f"Total Paid: ₱{total}\n\n"
                f"Your rental is now active. Ride safe!"
            )

            pay_win.grab_release()
            pay_win.destroy()
            on_success()

        NeonButton(btn_row, "←  CANCEL", command=cancel_payment,
                   accent=Colors.TEXT_MUTED, width=210, height=50,
                   bg=Colors.BG).pack(side="left")

        NeonButton(btn_row, "CONFIRM PAYMENT  ✓", command=confirm_payment,
                   accent=Colors.GREEN, width=340, height=50, filled=True,
                   bg=Colors.BG).pack(side="right")

    # ================= MY RENTALS =================

    def view_my_rentals(self):
        window = tk.Toplevel(self.root)
        window.title("My Rentals")
        window.configure(bg=Colors.BG)
        center_toplevel(window, self.root, 1150, 540)

        section_title(window, "My Rentals", accent=Colors.GREEN, size=15,
                      subtitle="All motorcycles you've booked"
                      ).pack(pady=(20, 12), padx=26, anchor="w")

        columns = ("Motorcycle", "Days", "Rate", "Total",
                   "Payment", "Reference", "Date", "Status")
        tree = self._make_tree(window, columns,
                               widths=[170, 60, 90, 100, 100, 140, 170, 100])
        tree.tag_configure("odd", background=Colors.SURFACE_ALT)
        tree.tag_configure("even", background=Colors.SURFACE)
        for i, rental in enumerate(self.rentals):
            if rental["username"] == self.current_user["username"]:
                tag = "odd" if i % 2 else "even"
                tree.insert("", "end", values=(
                    rental["motorcycle"], rental["days"], f"₱{rental['rate']}",
                    f"₱{rental['total']}",
                    rental.get("payment_method", "—"),
                    rental.get("payment_ref", "—"),
                    rental["date"], rental["status"]
                ), tags=(tag,))

    # ================= RETURN RENT =================

    def return_rent(self):
        active_rentals = [
            r for r in self.rentals
            if r["username"] == self.current_user["username"] and r["status"] == "Rented"
        ]
        if not active_rentals:
            messagebox.showinfo("No Rental", "You don't have an active rental.")
            return

        window = tk.Toplevel(self.root)
        window.title("Return Rent")
        window.configure(bg=Colors.BG)
        window.resizable(False, False)
        center_toplevel(window, self.root, 520, 540)

        section_title(window, "Return Rent", accent=Colors.AMBER, size=15,
                      subtitle="Submit a return request for admin approval"
                      ).pack(pady=(22, 10), padx=40, anchor="w")

        tk.Label(window, text=f"Customer: {self.current_user['username']}",
                 font=F(10, "bold"), bg=Colors.BG, fg=Colors.CYAN
                 ).pack(padx=40, anchor="w", pady=(0, 12))

        body = tk.Frame(window, bg=Colors.BG)
        body.pack(fill="x", padx=40)

        field_label(body, "SELECT YOUR MOTORCYCLE")
        selected = tk.StringVar()
        combo = ttk.Combobox(body, textvariable=selected, width=40,
                             state="readonly", style="Dark.TCombobox", font=F(10))
        combo["values"] = [r["motorcycle"] for r in active_rentals]
        combo.pack(fill="x", pady=(0, 8))

        field_label(body, "RETURN MESSAGE")
        msg_wrapper = tk.Frame(body, bg=Colors.BORDER, padx=1, pady=1)
        msg_wrapper.pack(fill="x", pady=(0, 4))
        message_entry = tk.Text(
            msg_wrapper, width=45, height=7, font=F(10), bd=0, relief="flat",
            bg=Colors.SURFACE, fg=Colors.TEXT, insertbackground=Colors.CYAN,
            padx=10, pady=8
        )
        message_entry.pack(fill="both", expand=True)

        def send_return_request():
            motorcycle = selected.get()
            message = message_entry.get("1.0", "end").strip()
            if motorcycle == "":
                messagebox.showwarning("Select Motorcycle",
                                       "Please select a motorcycle.")
                return
            if message == "":
                messagebox.showwarning("Message Required",
                                       "Please enter a return message.")
                return
            self.return_requests.append({
                "username": self.current_user["username"],
                "customer": self.current_user["username"],
                "motorcycle": motorcycle,
                "message": message,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "Pending"
            })
            messagebox.showinfo("Request Sent",
                                "Your motorcycle return request has been sent to the admin.")
            window.destroy()

        NeonButton(window, "SEND RETURN REQUEST  ✈", command=send_return_request,
                   accent=Colors.AMBER, width=440, height=48, filled=True,
                   bg=Colors.BG).pack(pady=22, padx=40)

    # ================= ADMIN DASHBOARD =================

    def admin_dashboard(self):
        for w in self.root.winfo_children():
            w.destroy()
        self.root.configure(bg=Colors.BG)

        self.build_header(
            "GV RENTAL — ADMIN",
            f"Signed in as {self.current_user['username']} — Administrator",
            [("LOGOUT", Colors.RED, self.logout)],
            c1="#0A0A18", c2="#1E1230"
        )

        button_frame = tk.Frame(self.root, bg=Colors.BG)
        button_frame.pack(pady=(20, 8), padx=30, fill="x")

        NeonButton(button_frame, "＋  ADD MOTORCYCLE", command=self.add_motorcycle,
                   accent=Colors.GREEN, width=210, height=44, filled=True,
                   bg=Colors.BG).pack(side="left", padx=(0, 8))
        NeonButton(button_frame, "VIEW RENTALS", command=self.view_all_rentals,
                   accent=Colors.CYAN, width=180, height=44, filled=True,
                   bg=Colors.BG).pack(side="left", padx=8)
        NeonButton(button_frame, "RETURN REQUESTS", command=self.view_return_requests,
                   accent=Colors.AMBER, width=200, height=44, filled=True,
                   bg=Colors.BG).pack(side="left", padx=8)
        NeonButton(button_frame, "REGISTERED USERS", command=self.view_users,
                   accent=Colors.MAGENTA, width=200, height=44, filled=True,
                   bg=Colors.BG).pack(side="left", padx=8)

        stats = tk.Frame(self.root, bg=Colors.BG)
        stats.pack(fill="x", padx=30, pady=(4, 10))

        total = len(self.motorcycles)
        available = sum(1 for b in self.motorcycles if b["status"] == "Available")
        rented = sum(1 for b in self.motorcycles if b["status"] == "Rented")
        pending = sum(1 for r in self.return_requests if r["status"] == "Pending")
        users = len(self.users)

        for label, value, accent in [
            ("Total Fleet", total, Colors.CYAN),
            ("Available", available, Colors.GREEN),
            ("Rented", rented, Colors.RED),
            ("Return Requests", pending, Colors.AMBER),
            ("Users", users, Colors.MAGENTA),
        ]:
            StatTile(stats, label, value, accent, width=210, height=78
                     ).pack(side="left", padx=6)

        section_title(self.root, "Motorcycle Records", accent=Colors.CYAN,
                      subtitle="Complete fleet inventory"
                      ).pack(pady=(10, 10), padx=30, anchor="w")

        search_row = tk.Frame(self.root, bg=Colors.BG)
        search_row.pack(fill="x", padx=30, pady=(0, 10))

        tk.Label(search_row, text="🔍", font=("Segoe UI", 13),
                 bg=Colors.BG, fg=Colors.CYAN_DIM).pack(side="left", padx=(0, 6))
        search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_row, textvariable=search_var, font=F(10), bd=0,
            relief="flat", bg=Colors.SURFACE, fg=Colors.TEXT,
            insertbackground=Colors.CYAN, highlightthickness=1,
            highlightbackground=Colors.BORDER, highlightcolor=Colors.CYAN
        )
        search_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 10))

        tree_frame = tk.Frame(self.root, bg=Colors.BG)
        tree_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        columns = ("ID", "Motorcycle", "Rate", "Status")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings",
                            style="Modern.Treeview")
        for col, w in zip(columns, [140, 400, 160, 200]):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")
        tree.pack(fill="both", expand=True)

        tree.tag_configure("available", foreground=Colors.GREEN)
        tree.tag_configure("rented", foreground=Colors.RED)
        tree.tag_configure("odd", background=Colors.SURFACE_ALT)

        def refresh(filter_text=""):
            for item in tree.get_children():
                tree.delete(item)
            ft = filter_text.lower().strip()
            i = 0
            for bike in self.motorcycles:
                if ft and ft not in bike["name"].lower() and ft not in bike["id"].lower():
                    continue
                status_tag = "available" if bike["status"] == "Available" else "rented"
                stripe = "odd" if i % 2 else ""
                tags = (status_tag, stripe) if stripe else (status_tag,)
                tree.insert("", "end", values=(
                    bike["id"], bike["name"], f"₱{bike['rate']}", bike["status"]
                ), tags=tags)
                i += 1

        refresh()
        search_var.trace_add("write", lambda *_: refresh(search_var.get()))

    # ================= ADD MOTORCYCLE =================

    def add_motorcycle(self):
        window = tk.Toplevel(self.root)
        window.title("Add Motorcycle")
        window.configure(bg=Colors.BG)
        window.resizable(False, False)
        center_toplevel(window, self.root, 440, 600)

        section_title(window, "Add Motorcycle", accent=Colors.GREEN, size=15,
                      subtitle="Register a new unit to the fleet"
                      ).pack(pady=(22, 10), padx=40, anchor="w")

        form = tk.Frame(window, bg=Colors.BG)
        form.pack(padx=40, fill="x")

        def labeled_field(label_text):
            field_label(form, label_text)
            box = NeonEntry(form, width=Layout.NARROW_FIELD_W,
                            height=Layout.NARROW_FIELD_H, bg=Colors.BG)
            box.pack()
            return box.entry

        id_entry = labeled_field("MOTORCYCLE ID")
        name_entry = labeled_field("MOTORCYCLE NAME")
        rate_entry = labeled_field("RATE PER DAY")
        image_entry = labeled_field("IMAGE FILENAME")

        def save():
            motorcycle_id = id_entry.get().strip()
            name = name_entry.get().strip()
            try:
                rate = float(rate_entry.get())
            except Exception:
                messagebox.showerror("Error", "Invalid rate.")
                return
            image = image_entry.get().strip()
            if motorcycle_id == "" or name == "":
                messagebox.showwarning("Missing", "Please complete the information.")
                return
            self.motorcycles.append({
                "id": motorcycle_id, "name": name, "rate": rate,
                "status": "Available", "image": image
            })
            messagebox.showinfo("Success", "Motorcycle added successfully!")
            window.destroy()
            self.admin_dashboard()

        NeonButton(window, "SAVE MOTORCYCLE  ✓", command=save, accent=Colors.GREEN,
                   width=Layout.NARROW_FIELD_W, height=48, filled=True,
                   bg=Colors.BG).pack(pady=28, padx=40)

    # ================= VIEW ALL RENTALS =================

    def view_all_rentals(self):
        window = tk.Toplevel(self.root)
        window.title("All Rentals")
        window.configure(bg=Colors.BG)
        center_toplevel(window, self.root, 1280, 650)

        section_title(window, "All Rental Transactions", accent=Colors.CYAN, size=15,
                      subtitle="Complete rental history across all users"
        ).pack(pady=(20, 12), padx=26, anchor="w")

        columns = ("Username", "Customer", "Contact", "Motorcycle", "Days",
                   "Total", "Payment Method", "Reference", "Date", "Status")
        tree = self._make_tree(
            window, columns,
            widths=[100, 100, 110, 160, 60, 90, 100, 130, 160, 100],
            height=14
        )
        tree.tag_configure("odd", background=Colors.SURFACE_ALT)
        tree.tag_configure("even", background=Colors.SURFACE)

        rental_rows = []
        for i, rental in enumerate(self.rentals):
            tag = "odd" if i % 2 else "even"
            item_id = tree.insert("", "end", values=(
                rental["username"], rental["customer"], rental["contact"],
                rental["motorcycle"], rental["days"], f"₱{rental['total']}",
                rental.get("payment_method", "—"),
                rental.get("payment_ref", "—"),
                rental["date"], rental["status"]
            ), tags=(tag,))
            rental_rows.append((item_id, rental))

        def get_selected_rental():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning(
                    "Select Rental",
                    "Please select a rental transaction first."
                )
                return None

            item_id = selected[0]
            for row_id, rental in rental_rows:
                if row_id == item_id:
                    return rental
            return None

        def view_id_document():
            rental = get_selected_rental()
            if rental is None:
                return

            path = rental.get("id_document", "")
            if not path:
                messagebox.showinfo(
                    "No ID Uploaded",
                    "This rental does not have an uploaded ID or driver's license."
                )
                return

            if not os.path.exists(path):
                messagebox.showerror(
                    "File Not Found",
                    "The uploaded ID file could not be found on this computer."
                )
                return

            extension = os.path.splitext(path)[1].lower()

            if extension == ".pdf":
                try:
                    os.startfile(path)
                except AttributeError:
                    import webbrowser
                    webbrowser.open(os.path.abspath(path))
                except Exception as exc:
                    messagebox.showerror(
                        "Unable to Open ID",
                        f"Could not open the PDF file.\n\n{exc}"
                    )
                return

            try:
                id_window = tk.Toplevel(window)
                id_window.title("User ID / Driver's License")
                id_window.configure(bg=Colors.BG)
                id_window.resizable(False, False)
                center_toplevel(id_window, window, 720, 620)

                section_title(
                    id_window,
                    "User ID / Driver's License",
                    accent=Colors.MAGENTA,
                    size=14,
                    subtitle=f"User: {rental['username']} • {rental['customer']}"
                ).pack(pady=(18, 10), padx=25, anchor="w")

                image = Image.open(path)
                image.thumbnail((650, 480), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)

                image_label = tk.Label(
                    id_window,
                    image=photo,
                    bg=Colors.SURFACE,
                    bd=0
                )
                image_label.image = photo
                image_label.pack(padx=25, pady=10)

                tk.Label(
                    id_window,
                    text=os.path.basename(path),
                    font=F(9),
                    bg=Colors.BG,
                    fg=Colors.TEXT_MUTED
                ).pack(pady=(0, 15))

            except Exception as exc:
                messagebox.showerror(
                    "Unable to View ID",
                    f"The ID image could not be displayed.\n\n{exc}"
                )

        button_frame = tk.Frame(window, bg=Colors.BG)
        button_frame.pack(pady=(0, 18))

        NeonButton(
            button_frame,
            "VIEW ID / DRIVER'S LICENSE",
            command=view_id_document,
            accent=Colors.MAGENTA,
            width=270,
            height=48,
            filled=True,
            bg=Colors.BG
        ).pack(side="left", padx=8)

        tk.Label(
            button_frame,
            text="Select a rental above, then click the button to view the uploaded ID.",
            font=F(9),
            bg=Colors.BG,
            fg=Colors.TEXT_MUTED
        ).pack(side="left", padx=8)

        tree.bind("<Double-1>", lambda _event: view_id_document())

    # ================= RETURN REQUESTS =================

    def view_return_requests(self):
        window = tk.Toplevel(self.root)
        window.title("Return Requests")
        window.configure(bg=Colors.BG)
        center_toplevel(window, self.root, 1080, 600)

        section_title(window, "Motorcycle Return Requests", accent=Colors.AMBER,
                      size=15, subtitle="Approve or reject pending returns"
                      ).pack(pady=(20, 12), padx=26, anchor="w")

        columns = ("Username", "Customer", "Motorcycle", "Message Alert", "Date", "Status")
        tree = self._make_tree(window, columns,
                               widths=[130, 130, 180, 260, 180, 120], height=16)
        tree.tag_configure("odd", background=Colors.SURFACE_ALT)
        tree.tag_configure("even", background=Colors.SURFACE)
        for i, request in enumerate(self.return_requests):
            tag = "odd" if i % 2 else "even"
            tree.insert("", "end", values=(
                request["username"], request["customer"], request["motorcycle"],
                request["message"], request["date"], request["status"]
            ), tags=(tag,))

        def approve():
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning("Select", "Please select a return request.")
                return
            values = tree.item(selected_item[0])["values"]
            username, motorcycle = values[0], values[2]
            for request in self.return_requests:
                if (request["username"] == username and request["motorcycle"] == motorcycle
                        and request["status"] == "Pending"):
                    request["status"] = "Approved"
                    break
            for rental in self.rentals:
                if (rental["username"] == username and rental["motorcycle"] == motorcycle
                        and rental["status"] == "Rented"):
                    rental["status"] = "Returned"
                    break
            for bike in self.motorcycles:
                if bike["name"] == motorcycle:
                    bike["status"] = "Available"
                    break
            messagebox.showinfo("Approved", "Return request approved.")
            window.destroy()
            self.view_return_requests()

        def reject():
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning("Select", "Please select a return request.")
                return
            values = tree.item(selected_item[0])["values"]
            username, motorcycle = values[0], values[2]
            for request in self.return_requests:
                if (request["username"] == username and request["motorcycle"] == motorcycle
                        and request["status"] == "Pending"):
                    request["status"] = "Rejected"
                    break
            messagebox.showinfo("Rejected", "Return request rejected.")
            window.destroy()
            self.view_return_requests()

        button_frame = tk.Frame(window, bg=Colors.BG)
        button_frame.pack(pady=18)
        NeonButton(button_frame, "✓  APPROVE RETURN", command=approve,
                   accent=Colors.GREEN, width=230, height=46, filled=True,
                   bg=Colors.BG).pack(side="left", padx=10)
        NeonButton(button_frame, "✕  REJECT RETURN", command=reject,
                   accent=Colors.RED, width=230, height=46, filled=True,
                   bg=Colors.BG).pack(side="left", padx=10)

    # ================= VIEW USERS =================

    def view_users(self):
        window = tk.Toplevel(self.root)
        window.title("Registered Users")
        window.configure(bg=Colors.BG)
        center_toplevel(window, self.root, 640, 480)

        section_title(window, "Registered Users", accent=Colors.MAGENTA, size=15,
                      subtitle="All accounts in the system"
                      ).pack(pady=(20, 12), padx=26, anchor="w")

        columns = ("Username", "Role")
        tree = self._make_tree(window, columns, widths=[300, 240])
        tree.tag_configure("odd", background=Colors.SURFACE_ALT)
        tree.tag_configure("even", background=Colors.SURFACE)
        for i, user in enumerate(self.users):
            tag = "odd" if i % 2 else "even"
            tree.insert("", "end", values=(user["username"], user["role"]), tags=(tag,))

    # ================= TREEVIEW HELPER =================

    def _make_tree(self, parent, columns, widths=None, height=14):
        frame = tk.Frame(parent, bg=Colors.BG)
        frame.pack(fill="both", expand=True, padx=22, pady=(0, 16))

        tree = ttk.Treeview(frame, columns=columns, show="headings",
                            style="Modern.Treeview", height=height)
        widths = widths or [140] * len(columns)
        for col, w in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview,
                            style="Dark.Vertical.TScrollbar")
        tree.configure(yscrollcommand=vsb.set)

        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        return tree

    # ================= LOGOUT =================

    def logout(self):
        if not messagebox.askyesno("Confirm Logout",
                                   "Are you sure you want to log out?"):
            return
        self.current_user = None
        self.login_screen()


# =====================================================================
#  SMALL LOCAL HELPER
# =====================================================================

def _lerp_color(c1, c2, t):
    from style import lerp
    return lerp(c1, c2, t)


# ================= RUN PROGRAM =================

if __name__ == "__main__":
    root = tk.Tk()
    app = MotorcycleRentalSystem(root)
    root.mainloop()