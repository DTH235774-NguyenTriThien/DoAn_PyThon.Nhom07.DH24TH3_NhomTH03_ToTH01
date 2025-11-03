# app/ui/mainmenu_frame.py
import tkinter as tk
from tkinter import ttk, messagebox
import os 
from app.utils.utils import clear_window, center_window, resource_path
from app.db import close_db_connection 
from app.utils.report_helpers import get_dashboard_kpis

try:
    from PIL import Image, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    print("WARNING: Thư viện 'Pillow' chưa được cài đặt (pip install Pillow).")
    print("Sẽ sử dụng icon text dự phòng.")

def show_main_menu(root, username_display, role, on_exit_callback=None, employee_id=None):
    """
    Hiển thị giao diện menu chính (Sidebar) của ứng dụng.
    Đây là trung tâm điều hướng, quản lý việc tải và hiển thị các module con.
    """
    clear_window(root)
    root.title(f"Hệ thống Quản lý Quán Cà Phê - Chào {username_display} ({role})")
    root.configure(bg="#f5e6ca") 

    window_width = 1500
    window_height = 720
    center_window(root, window_width, window_height, offset_y=-50)
    root.minsize(1200, 600)
    
    style = ttk.Style()

    # Style cho thẻ (card) trắng
    style.configure("KPI.TFrame", background="#f9fafb", relief="solid", borderwidth=1)
    
    # Style cho Tiêu đề thẻ (chữ nhỏ, màu nâu)
    style.configure("KPI.Title.TLabel", 
                    background="#f9fafb", 
                    foreground="#4b2e05", 
                    font=("Segoe UI", 14, "bold"))
    
    # Style cho 3 màu giá trị (KPI)
    style.configure("Blue.KPI.Value.TLabel", 
                    background="#f9fafb", 
                    foreground="#1976d2", 
                    font=("Segoe UI", 28, "bold"))
    style.configure("Green.KPI.Value.TLabel", 
                    background="#f9fafb", 
                    foreground="#4caf50", 
                    font=("Segoe UI", 28, "bold"))
    style.configure("Red.KPI.Value.TLabel", 
                    background="#f9fafb", 
                    foreground="#d32f2f", 
                    font=("Segoe UI", 28, "bold"))
    
    style.configure("TLabelFrame", background="#f5e6ca", bordercolor="#4b2e05")
    style.configure("TLabelFrame.Label", 
                    background="#f5e6ca", 
                    foreground="#4b2e05",
                    font=("Segoe UI", 11, "bold"))


    # --- Khung chính (Main Frame) chia Sidebar và Content ---
    main_frame = tk.Frame(root, bg="#f5e6ca")
    main_frame.pack(fill="both", expand=True)
    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_columnconfigure(1, weight=1) # Cột content co giãn

    # --- Sidebar Frame (Khung bên trái) ---
    sidebar_frame = tk.Frame(main_frame, bg="#4b2e05", width=220)
    sidebar_frame.grid(row=0, column=0, sticky="nswe")
    sidebar_frame.grid_propagate(False) 

    # --- Logo và Tên quán ---
    logo_label = tk.Label(sidebar_frame, bg="#4b2e05")
    logo_image_tk = None 
    if PILLOW_AVAILABLE:
        # Dùng resource_path để tìm ảnh (quan trọng khi đóng gói)
        logo_path = resource_path(os.path.join('app', 'assets', 'coffee_icon.png'))
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
    logo_label.image = logo_image_tk # Giữ tham chiếu
    tk.Label(sidebar_frame, text="CAFE MANAGER", font=("Segoe UI", 16, "bold"), bg="#4b2e05", fg="white").pack(pady=(0, 20))
    
    # --- Các nút điều hướng (Menu Items) ---
    menu_buttons_frame = tk.Frame(sidebar_frame, bg="#4b2e05")
    menu_buttons_frame.pack(fill="x", expand=True, pady=10)

    # Danh sách (List) để lưu các nút (quan trọng cho điều hướng phím)
    sidebar_buttons = [] # Cấu trúc: { "name": "...", "button": ... }
    current_module_frame = None
    current_selection_index = 0 # 0 = Dashboard
    
    def clear_content_frame():
        """Xóa tất cả widget con trong content_frame."""
        for widget in content_frame.winfo_children():
            widget.destroy()

    def set_active_button(module_name_to_activate):
        """Highlight nút được chọn và cập nhật index."""
        nonlocal current_selection_index
        for i, btn_info in enumerate(sidebar_buttons):
            if btn_info["name"] == module_name_to_activate:
                btn_info["button"].configure(style="Sidebar.Active.TButton")
                current_selection_index = i # Cập nhật index
            else:
                btn_info["button"].configure(style="Sidebar.TButton")
                
    def load_module(module_name):
        """Tải module con vào content_frame, xử lý phân quyền."""
        
        # --- Kiểm tra Phân quyền ---
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
        
        # --- Highlight nút ---
        set_active_button(module_name)

        # --- Dọn dẹp và Tải ---
        nonlocal current_module_frame
        clear_content_frame() 

        def on_back_to_dashboard_callback():
            """Hàm callback được gọi khi module con nhấn 'Quay lại'."""
            nonlocal current_module_frame
            if current_module_frame:
                current_module_frame.destroy()
                current_module_frame = None
            
            show_dashboard_content() 
            set_active_button("Dashboard") # Kích hoạt lại nút Dashboard

        module_container = tk.Frame(content_frame, bg="#f5e6ca") 
        module_container.pack(fill="both", expand=True)
        current_module_frame = module_container 

        # --- Logic Tải Module (Routing) ---
        if module_name == "Dashboard":
            show_dashboard_content()
        elif module_name == "POS":
            from app.modules.pos import create_pos_module
            module_frame_instance = create_pos_module(module_container, employee_id, on_back_to_dashboard_callback)
            module_frame_instance.pack(fill="both", expand=True)
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
                module_container, employee_id, on_back_to_dashboard_callback)
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

    # --- Helper tạo nút Sidebar ---
    def add_sidebar_button(name, text):
        """Hàm helper để tạo và lưu nút vào danh sách"""
        btn = ttk.Button(menu_buttons_frame, text=text, style="Sidebar.TButton", 
                         command=lambda n=name: load_module(n))
        btn.pack(fill="x", pady=2, padx=10)
        sidebar_buttons.append({"name": name, "button": btn})

    # (Tạo 10 nút module)
    add_sidebar_button("Dashboard", "Dashboard")
    add_sidebar_button("POS", "Bán hàng (POS)")
    add_sidebar_button("Employees", "Quản lý Nhân viên")
    add_sidebar_button("Products", "Quản lý Sản phẩm")
    add_sidebar_button("Recipes", "Quản lý Công thức")
    add_sidebar_button("Ingredients", "Quản lý Kho")
    add_sidebar_button("Invoices", "Quản lý Hóa đơn")
    add_sidebar_button("Customers", "Quản lý Khách hàng")
    add_sidebar_button("Reports", "Báo cáo & Thống kê")
    add_sidebar_button("Settings", "Cấu hình hệ thống")

    # --- Điều hướng Phím tắt ---
    def navigate_up(event=None):
        """Di chuyển lựa chọn lên trên"""
        nonlocal current_selection_index
        current_selection_index = (current_selection_index - 1) % len(sidebar_buttons)
        module_name = sidebar_buttons[current_selection_index]["name"]
        set_active_button(module_name)
        return "break" 
    def navigate_down(event=None):
        """Di chuyển lựa chọn xuống dưới"""
        nonlocal current_selection_index
        current_selection_index = (current_selection_index + 1) % len(sidebar_buttons)
        module_name = sidebar_buttons[current_selection_index]["name"]
        set_active_button(module_name)
        return "break"
    def activate_selection(event=None):
        """Tải module đang được highlight"""
        module_name = sidebar_buttons[current_selection_index]["name"]
        load_module(module_name)
        return "break"
        
    root.bind_all("<Up>", navigate_up)
    root.bind_all("<Down>", navigate_down)
    root.bind_all("<Return>", activate_selection) 

    # --- Thông tin người dùng & Đăng xuất ---
    bottom_sidebar_frame = tk.Frame(sidebar_frame, bg="#4b2e05")
    bottom_sidebar_frame.pack(side="bottom", fill="x", pady=(10, 20))
    tk.Label(bottom_sidebar_frame, text=f"Xin chào, {username_display}", font=("Segoe UI", 10), bg="#4b2e05", fg="#d7ccc8").pack(pady=(0, 5))
    
    def go_back_to_login():
        """Đăng xuất, dọn dẹp phím tắt và quay về màn hình Login."""
        if messagebox.askyesno("Đăng xuất", "Bạn có chắc chắn muốn đăng xuất?", parent=root):
            
            # Hủy gán phím tắt
            root.unbind_all("<Up>")
            root.unbind_all("<Down>")
            root.unbind_all("<Return>")
            
            from app.ui.login_frame import show_login
            show_login(root, on_exit_callback=on_exit_callback) 
            
    ttk.Button(bottom_sidebar_frame, text="⬅ Đăng xuất", style="Logout.TButton",
               command=go_back_to_login).pack(pady=5, padx=10, fill="x")

    # --- Content Frame (Khung bên phải) ---
    content_frame = tk.Frame(main_frame, bg="#f5e6ca", relief="flat", bd=1)
    content_frame.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)
    
    
    def create_card(parent, title, value, style_color_prefix, icon_image):
        """
        Hàm helper tạo thẻ KPI (card) trắng với icon (trái) và text (phải)
        """
        card = ttk.Frame(parent, style="KPI.TFrame", padding=20)
        card.grid(sticky="nsew", padx=10, pady=10)
        card.grid_rowconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=0) # Cột Icon (cố định)
        card.grid_columnconfigure(1, weight=1) # Cột Text (co giãn)

        icon_label = ttk.Label(card, image=icon_image, background="#f9fafb")
        icon_label.grid(row=0, column=0, rowspan=2, sticky="ns", padx=(0, 20))

        title_label = ttk.Label(card, text=title, style="KPI.Title.TLabel", anchor="w")
        title_label.grid(row=0, column=1, sticky="sw")
        
        value_style = f"{style_color_prefix}.KPI.Value.TLabel"
        value_label = ttk.Label(card, text=value, style=value_style, anchor="w")
        value_label.grid(row=1, column=1, sticky="nw", pady=(5, 0))
        
        return card 

    
    def show_dashboard_content():
        """Hàm hiển thị Dashboard (3 khu vực)"""
        
        for widget in content_frame.winfo_children():
            widget.destroy()
        
        content_frame.configure(bg="#f5e6ca") # Màu be
        
        # --- Cấu hình Grid chính của Dashboard ---
        content_frame.grid_rowconfigure(0, weight=0) # Hàng 0: Tiêu đề
        content_frame.grid_rowconfigure(1, weight=0) # Hàng 1: KPIs
        content_frame.grid_rowconfigure(2, weight=0) # Hàng 2: Lối tắt
        content_frame.grid_rowconfigure(3, weight=1) # Hàng 3: Cảnh báo
        content_frame.grid_columnconfigure(0, weight=1)

        # --- Khu vực 1: Tiêu đề Chào mừng ---
        tk.Label(content_frame, text="CHÀO MỪNG ĐẾN VỚI HỆ THỐNG QUẢN LÝ QUÁN CÀ PHÊ",
                 font=("Segoe UI", 18, "bold"), bg="#f5e6ca", fg="#4b2e05", 
                 wraplength=800, justify="center").grid(row=0, column=0, pady=(60, 30), sticky="ew")
        
        # --- Khu vực 2: Các thẻ KPI ---
        kpi_frame = tk.Frame(content_frame, bg="#f5e6ca")
        kpi_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        kpi_frame.grid_columnconfigure(0, weight=1)
        kpi_frame.grid_columnconfigure(1, weight=1)
        kpi_frame.grid_columnconfigure(2, weight=1)

        # (Lưu trữ tham chiếu ảnh)
        kpi_frame.image_references = []
        try:
            img_rev = Image.open(resource_path('app/assets/icon_revenue.png')).resize((48, 48), Image.Resampling.LANCZOS)
            photo_rev = ImageTk.PhotoImage(img_rev)
            kpi_frame.image_references.append(photo_rev)
            img_ord = Image.open(resource_path('app/assets/icon_orders.png')).resize((48, 48), Image.Resampling.LANCZOS)
            photo_ord = ImageTk.PhotoImage(img_ord)
            kpi_frame.image_references.append(photo_ord)
            img_alert = Image.open(resource_path('app/assets/icon_stock_alert.png')).resize((48, 48), Image.Resampling.LANCZOS)
            photo_alert = ImageTk.PhotoImage(img_alert)
            kpi_frame.image_references.append(photo_alert)
        except Exception as e:
            print(f"Lỗi tải icon Dashboard: {e}.")
            photo_rev = photo_ord = photo_alert = None

        try:
            kpi_data = get_dashboard_kpis()
        except Exception as e:
            messagebox.showerror("Lỗi Dashboard", f"Không thể tải KPI: {e}")
            kpi_data = {"DoanhThuHomNay": 0, "DonHangHomNay": 0, "SPHetHang": 0}

        doanh_thu_text = f"{int(kpi_data.get('DoanhThuHomNay') or 0):,} đ"
        don_hang_text = f"{int(kpi_data.get('DonHangHomNay') or 0)}"
        het_hang_text = f"{int(kpi_data.get('SPHetHang') or 0)}"

        card1 = create_card(kpi_frame, "Tổng Doanh Thu Hôm Nay", doanh_thu_text, "Blue", photo_rev) 
        card1.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        card2 = create_card(kpi_frame, "Đơn Hàng (Đã trả tiền)", don_hang_text, "Green", photo_ord)
        card2.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        card3 = create_card(kpi_frame, "Sản Phẩm Hết Hàng", het_hang_text, "Red", photo_alert)
        card3.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
        
        # --- Khu vực 3: Lối tắt Nhanh ---
        shortcut_frame = ttk.LabelFrame(content_frame, text=" Lối tắt nhanh ", 
                                        padding=(10, 10))
        shortcut_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=15)
        shortcut_frame.grid_columnconfigure(0, weight=1)
        shortcut_frame.grid_columnconfigure(1, weight=1)
        
        btn_pos_shortcut = ttk.Button(shortcut_frame, text="🛒 BÁN HÀNG (POS)", 
                             style="Add.TButton", 
                             command=lambda: load_module("POS"))
        btn_pos_shortcut.grid(row=0, column=0, sticky="nsew", padx=10, pady=5, ipady=10)
        
        btn_reports_shortcut = ttk.Button(shortcut_frame, text="📊 XEM BÁO CÁO", 
                                 style="Edit.TButton", 
                                 command=lambda: load_module("Reports"))
        btn_reports_shortcut.grid(row=0, column=1, sticky="nsew", padx=10, pady=5, ipady=10)

        # --- Khu vực 4: Cảnh báo Tồn kho ---
        alert_frame = ttk.LabelFrame(content_frame, text=" ⚠️ Cảnh báo Tồn kho (Ngưỡng <= 10) ", 
                                     padding=(10, 10))
        alert_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 20))
        alert_frame.grid_rowconfigure(0, weight=1)
        alert_frame.grid_columnconfigure(0, weight=1)
        
        cols = ("TenNL", "SoLuongTon", "DonVi")
        tree_alerts = ttk.Treeview(alert_frame, columns=cols, show="headings", height=5)
        tree_alerts.heading("TenNL", text="Nguyên Liệu"); tree_alerts.column("TenNL", anchor="w", width=300)
        tree_alerts.heading("SoLuongTon", text="Tồn Kho"); tree_alerts.column("SoLuongTon", anchor="e", width=100)
        tree_alerts.heading("DonVi", text="Đơn Vị"); tree_alerts.column("DonVi", anchor="center", width=100)
        tree_alerts.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(alert_frame, orient="vertical", command=tree_alerts.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        tree_alerts.configure(yscrollcommand=scrollbar.set)
        
        try:
            from app.utils.report_helpers import get_low_stock_alerts
            low_stock_items = get_low_stock_alerts(threshold=10) 
            if not low_stock_items:
                tree_alerts.insert("", "end", values=("(Không có cảnh báo nào)", "", ""))
            else:
                for item in low_stock_items:
                    tree_alerts.insert("", "end", values=(
                        item['TenNL'],
                        f"{item['SoLuongTon']:.2f}",
                        item['DonVi']
                    ))
        except Exception as e:
            tree_alerts.insert("", "end", values=(f"Lỗi tải cảnh báo: {e}", "", ""))

    # Hiển thị Dashboard mặc định khi vào main menu
    load_module("Dashboard")