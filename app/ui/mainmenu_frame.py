# app/ui/mainmenu_frame.py
import tkinter as tk
from tkinter import ttk, messagebox
import os 
from app.utils.utils import clear_window, center_window 
from app.db import close_db_connection # Fix lỗi treo terminal

# Import Pillow (PIL)
try:
    from PIL import Image, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    print("WARNING: Thư viện 'Pillow' chưa được cài đặt (pip install Pillow).")
    print("Sẽ sử dụng icon text dự phòng.")

# =========================================================
# PHIÊN BẢN CHUẨN (GIAI ĐOẠN 1)
# (Bố cục Sidebar + Pillow + Fix lỗi Thoát)
# =========================================================
def show_main_menu(root, username_display, role, on_exit_callback=None):
    clear_window(root)
    root.title(f"Hệ thống Quản lý Quán Cà Phê - Chào {username_display} ({role})")
    root.configure(bg="#f5e6ca") # Màu nền tổng thể

    # Thiết lập kích thước cửa sổ và căn giữa
    window_width = 1500
    window_height = 720
    center_window(root, window_width, window_height, offset_y=-50)
    root.minsize(1200, 600)
    
    # (Style đã được chuyển sang theme.py, không cần định nghĩa ở đây)

    # --- Khung chính (Main Frame) chia Sidebar và Content ---
    main_frame = tk.Frame(root, bg="#f5e6ca")
    main_frame.pack(fill="both", expand=True)
    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_columnconfigure(1, weight=1) # Cột content chiếm hết chiều rộng còn lại

    # --- Sidebar Frame (Khung bên trái) ---
    sidebar_frame = tk.Frame(main_frame, bg="#4b2e05", width=220)
    sidebar_frame.grid(row=0, column=0, sticky="nswe")
    sidebar_frame.grid_propagate(False) # Ngăn không cho khung tự co giãn

    # --- Logo và Tên quán (Dùng Pillow) ---
    logo_label = tk.Label(sidebar_frame, bg="#4b2e05")
    logo_image_tk = None # Biến để lưu trữ tham chiếu (rất quan trọng)

    if PILLOW_AVAILABLE:
        logo_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'coffee_icon.png')
        try:
            img = Image.open(logo_path)
            img_resized = img.resize((40, 40), Image.Resampling.LANCZOS)
            logo_image_tk = ImageTk.PhotoImage(img_resized)
            logo_label.config(image=logo_image_tk)
        except Exception as e:
            print(f"Lỗi tải logo: {e}. Sử dụng icon text.")
            logo_label.config(text="☕", font=("Segoe UI Emoji", 30), fg="#d7ccc8")
    else:
        logo_label.config(text="☕", font=("Segoe UI Emoji", 30), fg="#d7ccc8")

    logo_label.pack(pady=(20, 0))
    logo_label.image = logo_image_tk # "Neo" ảnh vào widget
    tk.Label(sidebar_frame, text="CAFE MANAGER", font=("Segoe UI", 16, "bold"), bg="#4b2e05", fg="white").pack(pady=(0, 20))

    # --- Các nút điều hướng (Menu Items) ---
    menu_buttons_frame = tk.Frame(sidebar_frame, bg="#4b2e05")
    menu_buttons_frame.pack(fill="x", expand=True, pady=10)

    current_module_frame = None
    
    def clear_content_frame():
        """Xóa tất cả widget trong content_frame."""
        for widget in content_frame.winfo_children():
            widget.destroy()

    def load_module(module_name):
        nonlocal current_module_frame
        clear_content_frame() 

        def on_back_to_dashboard_callback():
            nonlocal current_module_frame
            if current_module_frame:
                current_module_frame.destroy()
                current_module_frame = None
            show_dashboard_content()

        # Tạo một frame mới cho module con trong content_frame
        module_container = tk.Frame(content_frame, bg="#f9fafb")
        module_container.pack(fill="both", expand=True)
        current_module_frame = module_container # Lưu lại tham chiếu

        if module_name == "Dashboard":
            show_dashboard_content()
        
        # =========================================================
        # GIAI ĐOẠN 3 SẼ ĐƯỢC THỰC HIỆN TẠI ĐÂY
        # (Nơi chúng ta import và gọi các hàm create_..._module)
        # =========================================================
        elif module_name == "Employees":
            from app.modules.employees import create_employee_module
            module_frame_instance = create_employee_module(module_container, on_back_to_dashboard_callback)
            module_frame_instance.pack(fill="both", expand=True)
        elif module_name == "Products":
            from app.modules.drinks import create_drinks_module
            module_frame_instance = create_drinks_module(module_container, on_back_to_dashboard_callback)
            module_frame_instance.pack(fill="both", expand=True)
        elif module_name == "Recipes":
            from app.modules.recipes import create_recipes_module
            module_frame_instance = create_recipes_module(module_container, on_back_to_dashboard_callback)
            module_frame_instance.pack(fill="both", expand=True)
        elif module_name == "Ingredients":
            from app.modules.ingredients import create_ingredients_module
            module_frame_instance = create_ingredients_module(module_container, on_back_to_dashboard_callback)
            module_frame_instance.pack(fill="both", expand=True)
            
        elif module_name == "Invoices":
            from app.modules.invoices import create_invoices_module
            # (Đã sửa ở lần trước)
            module_frame_instance = create_invoices_module(
                module_container, 
                username_display, 
                on_back_to_dashboard_callback
            )
            module_frame_instance.pack(fill="both", expand=True)

        # SỬA 1: THÊM LỆNH GỌI MODULE CUSTOMERS
        elif module_name == "Customers":
            from app.modules.customers import create_customers_module
            module_frame_instance = create_customers_module(module_container, on_back_to_dashboard_callback)
            module_frame_instance.pack(fill="both", expand=True)
            
        elif module_name == "Reports":
            from app.modules.reports import create_reports_module
            module_frame_instance = create_reports_module(module_container, on_back_to_dashboard_callback)
            module_frame_instance.pack(fill="both", expand=True)
        elif module_name == "Settings":
            tk.Label(module_container, text="Đang tải Module: Cấu hình...", font=("Segoe UI", 14, "bold"), bg="#f9fafb").pack(pady=50)

    # Tạo các nút điều hướng
    ttk.Button(menu_buttons_frame, text="   Dashboard", style="Sidebar.TButton", command=lambda: load_module("Dashboard")).pack(fill="x", pady=2, padx=10)
    ttk.Button(menu_buttons_frame, text="   Quản lý Nhân viên", style="Sidebar.TButton", command=lambda: load_module("Employees")).pack(fill="x", pady=2, padx=10)
    ttk.Button(menu_buttons_frame, text="   Quản lý Sản phẩm", style="Sidebar.TButton", command=lambda: load_module("Products")).pack(fill="x", pady=2, padx=10)
    ttk.Button(menu_buttons_frame, text="   Quản lý Công thức", style="Sidebar.TButton", command=lambda: load_module("Recipes")).pack(fill="x", pady=2, padx=10)
    ttk.Button(menu_buttons_frame, text="   Quản lý Kho", style="Sidebar.TButton", command=lambda: load_module("Ingredients")).pack(fill="x", pady=2, padx=10)
    ttk.Button(menu_buttons_frame, text="   Quản lý Hóa đơn", style="Sidebar.TButton", command=lambda: load_module("Invoices")).pack(fill="x", pady=2, padx=10)
    
    # SỬA 2: THÊM NÚT QUẢN LÝ KHÁCH HÀNG
    ttk.Button(menu_buttons_frame, text="   Quản lý Khách hàng", style="Sidebar.TButton", command=lambda: load_module("Customers")).pack(fill="x", pady=2, padx=10)
    
    ttk.Button(menu_buttons_frame, text="   Báo cáo & Thống kê", style="Sidebar.TButton", command=lambda: load_module("Reports")).pack(fill="x", pady=2, padx=10)
    ttk.Button(menu_buttons_frame, text="   Cấu hình hệ thống", style="Sidebar.TButton", command=lambda: load_module("Settings")).pack(fill="x", pady=2, padx=10)


    # --- Thông tin người dùng & Đăng xuất (ở cuối Sidebar) ---
    bottom_sidebar_frame = tk.Frame(sidebar_frame, bg="#4b2e05")
    bottom_sidebar_frame.pack(side="bottom", fill="x", pady=(10, 20))

    tk.Label(bottom_sidebar_frame, text=f"Xin chào, {username_display}", font=("Segoe UI", 10), bg="#4b2e05", fg="#d7ccc8").pack(pady=(0, 5))
    
    def go_back_to_login():
        if messagebox.askyesno("Đăng xuất", "Bạn có chắc chắn muốn đăng xuất?", parent=root):
            close_db_connection() # Đóng CSDL
            if on_exit_callback:
                from app.ui.login_frame import show_login
                show_login(root, on_exit_callback=on_exit_callback)
            else:
                root.destroy() # Fallback

    ttk.Button(bottom_sidebar_frame, text="⬅ Đăng xuất", style="Logout.TButton",
               command=go_back_to_login).pack(pady=5, padx=10, fill="x")

    # --- Content Frame (Khung bên phải) ---
    content_frame = tk.Frame(main_frame, bg="#f9fafb", relief="flat", bd=1)
    content_frame.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)
    
    def show_dashboard_content():
        clear_content_frame()
        tk.Label(content_frame, text="CHÀO MỪNG ĐẾN VỚI HỆ THỐNG QUẢN LÝ QUÁN CÀ PHÊ ANHKH",
                 font=("Segoe UI", 18, "bold"), bg="#f9fafb", fg="#4b2e05", wraplength=800, justify="center").pack(pady=80, padx=20)
        
        card_frame = tk.Frame(content_frame, bg="#f9fafb")
        card_frame.pack(pady=20)

        def create_card(parent, title, value, color):
            card = tk.Frame(parent, bg=color, bd=1, relief="solid", width=250, height=120)
            card.pack_propagate(False) 
            card.pack(side="left", padx=15, pady=10)
            tk.Label(card, text=title, font=("Segoe UI", 12, "bold"), bg=color, fg="white", wraplength=200).pack(pady=(15, 5))
            tk.Label(card, text=value, font=("Segoe UI", 18, "bold"), bg=color, fg="white").pack()
        
        # (Đây là dữ liệu giả, sẽ được cập nhật sau)
        create_card(card_frame, "Tổng Doanh Thu Hôm Nay", "$ 5,500,000", "#1976d2") 
        create_card(card_frame, "Đơn Hàng Mới", "15", "#4caf50")
        create_card(card_frame, "Sản Phẩm Hết Hàng", "3", "#d32f2f")

    # Hiển thị Dashboard mặc định khi vào main menu
    load_module("Dashboard")