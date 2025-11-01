# app/ui/mainmenu_frame.py
import tkinter as tk
from tkinter import ttk, messagebox
import os 
from app.utils.utils import clear_window, center_window 
from app.db import close_db_connection 

try:
    from PIL import Image, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    print("WARNING: Thư viện 'Pillow' chưa được cài đặt (pip install Pillow).")
    print("Sẽ sử dụng icon text dự phòng.")

def show_main_menu(root, username_display, role, on_exit_callback=None):
    clear_window(root)
    root.title(f"Hệ thống Quản lý Quán Cà Phê - Chào {username_display} ({role})")
    root.configure(bg="#f5e6ca") 

    window_width = 1500
    window_height = 720
    center_window(root, window_width, window_height, offset_y=-50)
    root.minsize(1200, 600)
    
    # =========================================================
    # SỬA: XÓA CÁC DÒNG CẤU HÌNH STYLE TẠM THỜI
    # (Vì chúng đã được chuyển vào theme.py)
    # style = ttk.Style()
    # style.configure("Sidebar.Active.TButton", ...)
    # style.map("Sidebar.Active.TButton", ...)
    # =========================================================

    # --- Khung chính (Main Frame) chia Sidebar và Content ---
    main_frame = tk.Frame(root, bg="#f5e6ca")
    main_frame.pack(fill="both", expand=True)
    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_columnconfigure(1, weight=1) 

    # --- Sidebar Frame (Khung bên trái) ---
    sidebar_frame = tk.Frame(main_frame, bg="#4b2e05", width=220)
    sidebar_frame.grid(row=0, column=0, sticky="nswe")
    sidebar_frame.grid_propagate(False) 

    # --- Logo và Tên quán (Dùng Pillow) ---
    logo_label = tk.Label(sidebar_frame, bg="#4b2e05")
    logo_image_tk = None 

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
    logo_label.image = logo_image_tk 
    tk.Label(sidebar_frame, text="CAFE MANAGER", font=("Segoe UI", 16, "bold"), bg="#4b2e05", fg="white").pack(pady=(0, 20))

    # --- Các nút điều hướng (Menu Items) ---
    menu_buttons_frame = tk.Frame(sidebar_frame, bg="#4b2e05")
    menu_buttons_frame.pack(fill="x", expand=True, pady=10)

    # (Dictionary lưu trữ các nút - Giữ nguyên)
    sidebar_buttons = {}
    
    current_module_frame = None
    
    def clear_content_frame():
        for widget in content_frame.winfo_children():
            widget.destroy()

    def load_module(module_name):
        
        # --- KIỂM TRA PHÂN QUYỀN (Giữ nguyên) ---
        is_admin = (role == 'Admin') 
        restricted_modules = {
            "Employees": "Quản lý Nhân viên",
            "Reports": "Báo cáo & Thống kê",
            "Settings": "Cấu hình hệ thống"
        }
        if module_name in restricted_modules and not is_admin:
            module_display_name = restricted_modules[module_name]
            messagebox.showwarning("Không có quyền", 
                                   f"Bạn không có quyền truy cập module:\n{module_display_name}",
                                   parent=root)
            return 
        
        # --- LOGIC QUẢN LÝ NÚT ACTIVE (Giữ nguyên) ---
        # 1. Reset TẤT CẢ các nút về style mặc định
        for btn in sidebar_buttons.values():
            btn.configure(style="Sidebar.TButton")
            
        # 2. Kích hoạt nút vừa được nhấp
        if module_name in sidebar_buttons:
            # (Giờ đây 'Sidebar.Active.TButton' đã được định nghĩa trong theme)
            sidebar_buttons[module_name].configure(style="Sidebar.Active.TButton")

        nonlocal current_module_frame
        clear_content_frame() 

        def on_back_to_dashboard_callback():
            nonlocal current_module_frame
            if current_module_frame:
                current_module_frame.destroy()
                current_module_frame = None
            show_dashboard_content()
            
            # Khi quay lại, kích hoạt lại nút Dashboard
            for btn in sidebar_buttons.values():
                btn.configure(style="Sidebar.TButton")
            if "Dashboard" in sidebar_buttons:
                sidebar_buttons["Dashboard"].configure(style="Sidebar.Active.TButton")

        module_container = tk.Frame(content_frame, bg="#f9fafb")
        module_container.pack(fill="both", expand=True)
        current_module_frame = module_container 

        # (Logic tải module bên dưới giữ nguyên)
        if module_name == "Dashboard":
            show_dashboard_content()
        
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
            module_frame_instance = create_invoices_module(
                module_container, 
                username_display, 
                on_back_to_dashboard_callback
            )
            module_frame_instance.pack(fill="both", expand=True)

        elif module_name == "Customers":
            from app.modules.customers import create_customers_module
            module_frame_instance = create_customers_module(module_container, on_back_to_dashboard_callback)
            module_frame_instance.pack(fill="both", expand=True)
            
        elif module_name == "Reports":
            from app.modules.reports import create_reports_module
            module_frame_instance = create_reports_module(module_container, on_back_to_dashboard_callback)
            module_frame_instance.pack(fill="both", expand=True)
        elif module_name == "Settings":
            from app.modules.settings import create_settings_module
            module_frame_instance = create_settings_module(module_container, on_back_to_dashboard_callback)
            module_frame_instance.pack(fill="both",expand=True)

    # (Logic lưu các nút vào dictionary - Giữ nguyên)
    btn_dashboard = ttk.Button(menu_buttons_frame, text="Dashboard", style="Sidebar.TButton", 
                               command=lambda: load_module("Dashboard"))
    btn_dashboard.pack(fill="x", pady=2, padx=10)
    sidebar_buttons["Dashboard"] = btn_dashboard
    
    btn_employees = ttk.Button(menu_buttons_frame, text="Quản lý Nhân viên", style="Sidebar.TButton", 
                               command=lambda: load_module("Employees"))
    btn_employees.pack(fill="x", pady=2, padx=10)
    sidebar_buttons["Employees"] = btn_employees
    
    btn_products = ttk.Button(menu_buttons_frame, text="Quản lý Sản phẩm", style="Sidebar.TButton", 
                              command=lambda: load_module("Products"))
    btn_products.pack(fill="x", pady=2, padx=10)
    sidebar_buttons["Products"] = btn_products
    
    btn_recipes = ttk.Button(menu_buttons_frame, text="Quản lý Công thức", style="Sidebar.TButton", 
                             command=lambda: load_module("Recipes"))
    btn_recipes.pack(fill="x", pady=2, padx=10)
    sidebar_buttons["Recipes"] = btn_recipes
    
    btn_ingredients = ttk.Button(menu_buttons_frame, text="Quản lý Kho", style="Sidebar.TButton", 
                                 command=lambda: load_module("Ingredients"))
    btn_ingredients.pack(fill="x", pady=2, padx=10)
    sidebar_buttons["Ingredients"] = btn_ingredients
    
    btn_invoices = ttk.Button(menu_buttons_frame, text="Quản lý Hóa đơn", style="Sidebar.TButton", 
                              command=lambda: load_module("Invoices"))
    btn_invoices.pack(fill="x", pady=2, padx=10)
    sidebar_buttons["Invoices"] = btn_invoices
    
    btn_customers = ttk.Button(menu_buttons_frame, text="Quản lý Khách hàng", style="Sidebar.TButton", 
                               command=lambda: load_module("Customers"))
    btn_customers.pack(fill="x", pady=2, padx=10)
    sidebar_buttons["Customers"] = btn_customers
    
    btn_reports = ttk.Button(menu_buttons_frame, text="Báo cáo & Thống kê", style="Sidebar.TButton", 
                             command=lambda: load_module("Reports"))
    btn_reports.pack(fill="x", pady=2, padx=10)
    sidebar_buttons["Reports"] = btn_reports
    
    btn_settings = ttk.Button(menu_buttons_frame, text="Cấu hình hệ thống", style="Sidebar.TButton", 
                              command=lambda: load_module("Settings"))
    btn_settings.pack(fill="x", pady=2, padx=10)
    sidebar_buttons["Settings"] = btn_settings


    # --- Thông tin người dùng & Đăng xuất (ở cuối Sidebar) ---
    bottom_sidebar_frame = tk.Frame(sidebar_frame, bg="#4b2e05")
    bottom_sidebar_frame.pack(side="bottom", fill="x", pady=(10, 20))

    tk.Label(bottom_sidebar_frame, text=f"Xin chào, {username_display}", font=("Segoe UI", 10), bg="#4b2e05", fg="#d7ccc8").pack(pady=(0, 5))
    
    def go_back_to_login():
        if messagebox.askyesno("Đăng xuất", "Bạn có chắc chắn muốn đăng xuất?", parent=root):
            from app.ui.login_frame import show_login
            show_login(root, on_exit_callback=on_exit_callback) 

    ttk.Button(bottom_sidebar_frame, text="⬅ Đăng xuất", style="Logout.TButton",
               command=go_back_to_login).pack(pady=5, padx=10, fill="x")

    # --- Content Frame (Khung bên phải) ---
    content_frame = tk.Frame(main_frame, bg="#f9fafb", relief="flat", bd=1)
    content_frame.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)
    
    def show_dashboard_content():
        clear_content_frame()
        tk.Label(content_frame, text="CHÀO MỪNG ĐẾN VỚI HỆ THỐNG QUẢN LÝ QUÁN CÀ PHÊ",
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