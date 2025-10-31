# app/ui/mainmenu_frame.py
import tkinter as tk
from tkinter import ttk
from app.utils.utils import clear_window, center_window 

# =========================================================
# PHIÊN BẢN ĐỒNG BỘ (V3)
# (Đã sửa lỗi 'list index out of range' VÀ lỗi 'treo terminal')
# =========================================================
def show_main_menu(root, display_name, role, on_exit_callback=None):
    clear_window(root)

    # ====== WINDOW CONFIG ======
    root.title("☕ Hệ thống quản lý cà phê - Main Menu")
    root.configure(bg="#f5e6ca")
    center_window(root, 900, 600) 
    root.minsize(850, 550)

    # ====== HEADER ======
    header = tk.Frame(root, bg="#4b2e05", height=80)
    header.pack(fill="x")
    tk.Label(
        header,
        text=f"☕ Xin chào {display_name} ({role}) ☕", # Dùng display_name
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

    # ====== BỐ CỤC NÚT (Layout 3-3-1) ======
    btn_container = tk.Frame(main, bg="#f5e6ca")
    btn_container.pack(expand=True)
    top_row_frame = tk.Frame(btn_container, bg="#f5e6ca")
    top_row_frame.pack(pady=15)
    bottom_row_frame = tk.Frame(btn_container, bg="#f5e6ca")
    bottom_row_frame.pack(pady=15)

    # SỬA 1: Đảm bảo có 6 nút (thêm "Quản lý Kho")
    buttons = [
        ("👥 Quản lý nhân viên", lambda: open_employee_module(root, on_exit_callback)),
        ("🥤 Quản lý đồ uống", lambda: from_app_open_drinks(root, on_exit_callback)),
        ("🧾 Quản lý hóa đơn", lambda: from_app_open_invoices(root, on_exit_callback)),
        ("💳 Khách hàng", lambda: from_app_open_customers(root, on_exit_callback)),
        ("📦 Quản lý Kho", lambda: from_app_open_ingredients(root, on_exit_callback)), # <-- NÚT MỚI
        ("📊 Thống kê", lambda: from_app_open_reports(root, on_exit_callback)),
    ]

    # Thêm 3 nút đầu tiên vào Hàng 1
    for i in range(3):
        text, cmd = buttons[i]
        ttk.Button(
            top_row_frame,
            text=text,
            style="Coffee.TButton",
            width=25,
            command=cmd
        ).pack(side="left", padx=15)
        
    # SỬA 2: Lặp đến 6 (thay vì 5)
    for i in range(3, 6): 
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
        command=lambda: go_back_to_login(root, on_exit_callback), # SỬA 3: Truyền callback
    ).pack(pady=25) 

# =========================================================
# KẾT THÚC THAY THẾ
# =========================================================

# ----------- HELPER FUNCTIONS (CẬP NHẬT ĐỂ TRUYỀN CALLBACK) --------------

def open_employee_module(root, on_exit_callback=None):
    from app.modules.employees import show_employee_module
    # (Lưu ý: show_employee_module chưa được refactor để nhận on_exit_callback)
    show_employee_module(root) 

def go_back_to_login(root, on_exit_callback=None):
    from app.ui.login_frame import show_login
    show_login(root, on_exit_callback=on_exit_callback)

def from_app_open_drinks(root, on_exit_callback=None):
    from app.modules.drinks import show_drinks_module
    show_drinks_module(root)

def from_app_open_invoices(root, on_exit_callback=None):
    from app.modules.invoices import show_invoices_module
    show_invoices_module(root)

def from_app_open_customers(root, on_exit_callback=None):
    from app.modules.customers import show_customers_module
    show_customers_module(root)

def from_app_open_reports(root, on_exit_callback=None):
    from app.modules.reports import show_reports_module
    show_reports_module(root, on_exit_callback=on_exit_callback)

def from_app_open_ingredients(root, on_exit_callback=None):
    from app.modules.ingredients import show_ingredients_module
    show_ingredients_module(root)