# app/ui/mainmenu_frame.py
import tkinter as tk
from tkinter import ttk
from app.utils.utils import clear_window, center_window 

def show_main_menu(root, display_name, role, on_exit_callback=None):
    clear_window(root)

    # ====== WINDOW CONFIG ======
    root.title("☕ Hệ thống quản lý cà phê - Main Menu")
    root.configure(bg="#f5e6ca")
    # SỬA 1: Mở rộng cửa sổ chính để chứa 4 nút
    center_window(root, 1100, 600) 
    root.minsize(1000, 550)

    # ====== HEADER ======
    header = tk.Frame(root, bg="#4b2e05", height=80)
    header.pack(fill="x")
    tk.Label(
        header,
        text=f"☕ Xin chào {display_name} ({role}) ☕", 
        bg="#4b2e05",
        fg="white",
        font=("Segoe UI", 16, "bold")
    ).pack(pady=20)

    # ====== MAIN CONTENT ======
    main = tk.Frame(root, bg="#f5e6ca")
    main.pack(expand=True, pady=30, fill="both")

    # ====== STYLE (Giữ nguyên) ======
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Coffee.TButton", font=("Segoe UI", 13, "bold"), padding=15, relief="flat", background="#a47148", foreground="white", borderwidth=0)
    style.map("Coffee.TButton", background=[("active", "#8b5e34"), ("pressed", "#6f4518")], foreground=[("active", "white")])
    style.configure("Logout.TButton", font=("Segoe UI", 13, "bold"), padding=15, relief="flat", background="#c75c5c", foreground="white", borderwidth=0)
    style.map("Logout.TButton", background=[("active", "#a94442")])

    # ====== BỐ CỤC NÚT (SỬA 2: Layout 4-3-1) ======
    btn_container = tk.Frame(main, bg="#f5e6ca")
    btn_container.pack(expand=True)
    top_row_frame = tk.Frame(btn_container, bg="#f5e6ca")
    top_row_frame.pack(pady=15)
    bottom_row_frame = tk.Frame(btn_container, bg="#f5e6ca")
    bottom_row_frame.pack(pady=15)

    # SỬA 3: Thêm nút "Quản lý Công thức" (Tổng 7 nút)
    buttons = [
        ("👥 Quản lý nhân viên", lambda: open_employee_module(root, on_exit_callback)),
        ("🥤 Quản lý đồ uống", lambda: from_app_open_drinks(root, on_exit_callback)),
        ("📦 Quản lý Kho", lambda: from_app_open_ingredients(root, on_exit_callback)),
        ("📜 Quản lý Công thức", lambda: from_app_open_recipes(root, on_exit_callback)), # <-- NÚT MỚI
        ("🧾 Quản lý hóa đơn", lambda: from_app_open_invoices(root, on_exit_callback)),
        ("💳 Khách hàng", lambda: from_app_open_customers(root, on_exit_callback)),
        ("📊 Thống kê", lambda: from_app_open_reports(root, on_exit_callback)),
    ]

    # Thêm 4 nút đầu tiên vào Hàng 1
    for i in range(4): # <-- SỬA 4: Đổi (3) thành (4)
        text, cmd = buttons[i]
        ttk.Button(
            top_row_frame,
            text=text,
            style="Coffee.TButton",
            width=25,
            command=cmd
        ).pack(side="left", padx=15)

    # Thêm 3 nút cuối vào Hàng 2
    for i in range(4, 7): # <-- SỬA 5: Đổi (3, 6) thành (4, 7)
        text, cmd = buttons[i]
        ttk.Button(
            bottom_row_frame,
            text=text,
            style="Coffee.TButton",
            width=25,
            command=cmd
        ).pack(side="left", padx=15)

    # ====== LOGOUT BUTTON (Hàng 3, 1 nút) ======
    ttk.Button(
        btn_container, 
        text="🚪 Đăng xuất",
        style="Logout.TButton",
        width=25,
        command=lambda: go_back_to_login(root, on_exit_callback),
    ).pack(pady=25) 

# ----------- HELPER FUNCTIONS (CẬP NHẬT ĐỂ TRUYỀN CALLBACK) --------------

def open_employee_module(root, on_exit_callback=None):
    from app.modules.employees import show_employee_module
    show_employee_module(root) # (TODO: Cần refactor)

def go_back_to_login(root, on_exit_callback=None):
    from app.ui.login_frame import show_login
    show_login(root, on_exit_callback=on_exit_callback)

def from_app_open_drinks(root, on_exit_callback=None):
    from app.modules.drinks import show_drinks_module
    show_drinks_module(root) # (TODO: Cần refactor)

def from_app_open_invoices(root, on_exit_callback=None):
    from app.modules.invoices import show_invoices_module
    show_invoices_module(root, on_exit_callback=on_exit_callback)

def from_app_open_customers(root, on_exit_callback=None):
    from app.modules.customers import show_customers_module
    show_customers_module(root) # (TODO: Cần refactor)

def from_app_open_reports(root, on_exit_callback=None):
    from app.modules.reports import show_reports_module
    show_reports_module(root, on_exit_callback=on_exit_callback)

def from_app_open_ingredients(root, on_exit_callback=None):
    from app.modules.ingredients import show_ingredients_module
    show_ingredients_module(root) # (TODO: Cần refactor)

# SỬA 6: Thêm helper cho module mới
def from_app_open_recipes(root, on_exit_callback=None):
    from app.modules.recipes import show_recipes_module
    show_recipes_module(root) # (TODO: Cần refactor)