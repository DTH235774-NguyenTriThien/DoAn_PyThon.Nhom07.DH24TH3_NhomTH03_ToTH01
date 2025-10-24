# app/ui/mainmenu_frame.py
import tkinter as tk
from tkinter import ttk
from app.utils import clear_window

def show_main_menu(root, username, role):
    clear_window(root)

    # ====== WINDOW CONFIG ======
    root.title("☕ Hệ thống quản lý cà phê - Main Menu")
    root.configure(bg="#f5e6ca")

    window_width, window_height = 900, 600
    screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
    x = int((screen_width / 2) - (window_width / 2))
    y = int((screen_height / 2) - (window_height / 2))
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    root.minsize(850, 550)

    # ====== HEADER ======
    header = tk.Frame(root, bg="#4b2e05", height=80)
    header.pack(fill="x")
    tk.Label(
        header,
        text=f"☕ Xin chào {username} ({role}) ☕",
        bg="#4b2e05",
        fg="white",
        font=("Segoe UI", 16, "bold")
    ).pack(pady=20)

    # ====== MAIN CONTENT ======
    main = tk.Frame(root, bg="#f5e6ca")
    main.pack(expand=True, pady=30)

    # ====== STYLE ======
    style = ttk.Style()
    style.theme_use("clam")

    style.configure(
        "Coffee.TButton",
        font=("Segoe UI", 13, "bold"),
        padding=15,
        relief="flat",
        background="#a47148",
        foreground="white",
        borderwidth=0,
    )
    style.map(
        "Coffee.TButton",
        background=[("active", "#8b5e34"), ("pressed", "#6f4518")],
        foreground=[("active", "white")],
    )

    style.configure(
        "Logout.TButton",
        font=("Segoe UI", 13, "bold"),
        padding=15,
        relief="flat",
        background="#c75c5c",
        foreground="white",
        borderwidth=0,
    )
    style.map("Logout.TButton", background=[("active", "#a94442")])

    # ====== GRID BUTTON FRAME ======
    btn_frame = tk.Frame(main, bg="#f5e6ca")
    btn_frame.pack(expand=True)

    buttons = [
        ("👥 Quản lý nhân viên", lambda: open_employee_module(root)),
        ("🥤 Quản lý đồ uống", lambda: from_app_open_drinks(root)),
        ("🧾 Quản lý hóa đơn", lambda: from_app_open_invoices(root)),
        ("💳 Khách hàng", lambda: from_app_open_customers(root)),
        ("📊 Thống kê", lambda: print("Thống kê module")),
    ]

    # Bố trí nút dạng 2 hàng, 3 cột
    for i, (text, cmd) in enumerate(buttons):
        row, col = divmod(i, 3)
        ttk.Button(
            btn_frame,
            text=text,
            style="Coffee.TButton",
            width=25,
            command=cmd
        ).grid(row=row, column=col, padx=30, pady=25)

    # Căn giữa lưới nút
    for i in range(3):
        btn_frame.grid_columnconfigure(i, weight=1)

    # ====== LOGOUT BUTTON ======
    ttk.Button(
        main,
        text="🚪 Đăng xuất",
        style="Logout.TButton",
        width=25,
        command=lambda: go_back_to_login(root),
    ).pack(pady=25)

# ----------- HELPER FUNCTIONS --------------

def open_employee_module(root):
    from app.modules.employees import show_employee_module
    show_employee_module(root)

def go_back_to_login(root):
    from app.ui.login_frame import show_login
    show_login(root)

def from_app_open_drinks(root):
    from app.modules.drinks import show_drinks_module
    show_drinks_module(root)

def from_app_open_invoices(root):
    from app.modules.invoices import show_invoices_module
    show_invoices_module(root)

def from_app_open_customers(root):
    from app.modules.customers import show_customers_module
    show_customers_module(root)
