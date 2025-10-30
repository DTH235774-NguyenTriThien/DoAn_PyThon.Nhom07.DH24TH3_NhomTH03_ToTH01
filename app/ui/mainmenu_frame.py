# app/ui/mainmenu_frame.py
import tkinter as tk
from tkinter import ttk
# SỬA 1: Import thêm center_window
from app.utils.utils import clear_window, center_window 

# =========================================================
# THAY THẾ TOÀN BỘ HÀM NÀY
# =========================================================
def show_main_menu(root, display_name, role):
    clear_window(root)

    # ====== WINDOW CONFIG ======
    root.title("☕ Hệ thống quản lý cà phê - Main Menu")
    root.configure(bg="#f5e6ca")

    # SỬA 2: Sử dụng helper center_window
    window_width, window_height = 900, 600
    center_window(root, window_width, window_height)
    
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

    # ====== STYLE ======
    # (Giữ nguyên style của bạn)
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

    # =========================================================
    # SỬA 3: BỐ CỤC NÚT (Layout 3-2-1)
    # =========================================================
    
    # Frame chính chứa các nút, dùng pack để căn giữa
    btn_container = tk.Frame(main, bg="#f5e6ca")
    btn_container.pack(expand=True)

    # --- Hàng 1 (3 nút) ---
    top_row_frame = tk.Frame(btn_container, bg="#f5e6ca")
    top_row_frame.pack(pady=15)
    
    # --- Hàng 2 (2 nút) ---
    bottom_row_frame = tk.Frame(btn_container, bg="#f5e6ca")
    bottom_row_frame.pack(pady=15)

    buttons = [
        ("👥 Quản lý nhân viên", lambda: open_employee_module(root)),
        ("🥤 Quản lý đồ uống", lambda: from_app_open_drinks(root)),
        ("🧾 Quản lý hóa đơn", lambda: from_app_open_invoices(root)),
        ("💳 Khách hàng", lambda: from_app_open_customers(root)),
        ("📊 Thống kê", lambda: from_app_open_reports(root)),
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
        
    # Thêm 2 nút cuối vào Hàng 2
    for i in range(3, 5):
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
        btn_container, # Đưa vào chung container
        text="🚪 Đăng xuất",
        style="Logout.TButton",
        width=25,
        command=lambda: go_back_to_login(root),
    ).pack(pady=25) # pack ở cuối sẽ tự động căn giữa

# =========================================================
# KẾT THÚC THAY THẾ
# =========================================================

# ----------- HELPER FUNCTIONS (Giữ nguyên) --------------

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

def from_app_open_reports(root):
    from app.modules.reports import show_statistics_module
    show_statistics_module(root)