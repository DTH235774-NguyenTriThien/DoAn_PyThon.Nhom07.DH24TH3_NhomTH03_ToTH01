import tkinter.ttk as ttk

def setup_styles():
    style = ttk.Style()

    #dùng theme "clam" để đảm bảo style hiển thị đầy đủ
    style.theme_use('clam')

    base_font = ("Segoe UI", 10, "bold")
    base_padding = (5, 8)

    # 🌿 Style gốc
    style.configure("CoffeeBase.TButton",
                    font=base_font,
                    padding=base_padding,
                    anchor="center")

    # ➕ Thêm
    style.configure("Add.TButton",
                    font=base_font,
                    padding=base_padding,
                    anchor="center",
                    foreground="#2e7d32")
    style.map("Add.TButton",
              background=[("active", "#e8f5e9")])

    # ✏️ Sửa
    style.configure("Edit.TButton",
                    font=base_font,
                    padding=base_padding,
                    anchor="center",
                    foreground="#1565c0")
    style.map("Edit.TButton",
              background=[("active", "#e3f2fd")])

    # 🗑 Xóa
    style.configure("Delete.TButton",
                    font=base_font,
                    padding=base_padding,
                    anchor="center",
                    foreground="#b71c1c")
    style.map("Delete.TButton",
              background=[("active", "#ffebee")])

    # ✖️ Đóng
    style.configure("Close.TButton",
                    font=base_font,
                    padding=base_padding,
                    anchor="center",
                    foreground="#3e2723")
    style.map("Close.TButton",
              background=[("active", "#efebe9")])

    style.map("Close.TButton",
              background=[("active", "#efebe9")])
              
    # =========================================================
    # THÊM CÁC STYLE MỚI CHO BỐ CỤC DASHBOARD (Sidebar)
    # =========================================================
    
    # --- Màu sắc chủ đề (Theme Colors) ---
    COLOR_PRIMARY_DARK = "#4b2e05"     # Nâu đậm (Header, Sidebar)
    COLOR_TEXT_LIGHT = "white"
    COLOR_DANGER = "#c75c5c"           # Đỏ (Nút Xóa / Đăng xuất)
    COLOR_DANGER_HOVER = "#a94442"

    # --- Style cho Sidebar (Bố cục Dashboard MỚI) ---
    
    # Nút Sidebar (Sidebar.TButton)
    style.configure("Sidebar.TButton", 
                    font=("Segoe UI", 12), 
                    foreground=COLOR_TEXT_LIGHT, 
                    background=COLOR_PRIMARY_DARK, # Nền trùng màu sidebar
                    borderwidth=0, 
                    focusthickness=0, 
                    focuscolor="none",
                    relief="flat",
                    anchor="center", # Căn trái chữ
                    padding=[20, 10, 20, 10]) # Padding (left, top, right, bottom)
    
    style.map("Sidebar.TButton", 
              background=[('active', '#6d4c41')], # Màu khi rê chuột
              foreground=[('active', COLOR_TEXT_LIGHT)])

    # Nút Đăng xuất (Logout.TButton)
    style.configure("Logout.TButton",
                    font=("Segoe UI", 11, "bold"),
                    foreground=COLOR_TEXT_LIGHT,
                    background=COLOR_DANGER, 
                    borderwidth=0,
                    relief="flat",
                    padding=[10, 5])
    style.map("Logout.TButton", 
              background=[('active', COLOR_DANGER_HOVER)],
              foreground=[('active', COLOR_TEXT_LIGHT)])
    


    # --- Style cho Báo cáo (KPI Cards) ---
    style.configure("KPI.TFrame", background="#f9fafb", relief="solid", borderwidth=1)
    style.configure("KPI.Title.TLabel", background="#f9fafb", foreground=COLOR_PRIMARY_DARK, font=("Segoe UI", 14, "bold"))
    style.configure("KPI.Value.TLabel", background="#f9fafb", foreground="#a47148", font=("Segoe UI", 28, "bold"))

    # THÊM STYLE CHO NÚT ACTIVE
    # =========================================================
    style.configure("Sidebar.Active.TButton",
                    font=("Segoe UI", 11, "bold"),
                    anchor="center",
                    padding=(10, 12),
                    borderwidth=0,
                    background="#ffebee",  # Nền sáng (màu content_frame)
                    foreground="#4b2e05") # Chữ tối (màu sidebar)
    
    style.map("Sidebar.Active.TButton",
              background=[("active", "#ffebee")], # Giữ nguyên màu khi hover/active
              foreground=[("active", "#4b2e05")])
    # =========================================================