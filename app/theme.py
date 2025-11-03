# app/theme.py
import tkinter.ttk as ttk

def setup_styles():
    """Định nghĩa và cấu hình tất cả các style ttk cho ứng dụng."""
    
    style = ttk.Style()

    # Dùng theme "clam" để đảm bảo style hiển thị đầy đủ trên mọi HĐH
    style.theme_use('clam')

    base_font = ("Segoe UI", 10, "bold")
    base_padding = (5, 8)

    # --- Style Nút CRUD Tiêu chuẩn ---

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

    # ✖️ Đóng / Tải lại
    style.configure("Close.TButton",
                    font=base_font,
                    padding=base_padding,
                    anchor="center",
                    foreground="#3e2723")
    style.map("Close.TButton",
              background=[("active", "#efebe9")])

    # --- Màu sắc chủ đề (Theme Colors) ---
    COLOR_PRIMARY_DARK = "#4b2e05"   # Nâu đậm (Header, Sidebar)
    COLOR_TEXT_LIGHT = "white"
    COLOR_DANGER = "#c75c5c"         # Đỏ (Nút Xóa / Đăng xuất)
    COLOR_DANGER_HOVER = "#a94442"
    COLOR_CONTENT_BG = "#f9fafb"     # Nền trắng của nội dung
    COLOR_ACCENT = "#a47148"         # Nâu nhạt (Accent)

    # --- Style cho Bố cục Dashboard (Sidebar) ---
    
    # Nút Sidebar (Mặc định)
    style.configure("Sidebar.TButton", 
                    font=("Segoe UI", 12), 
                    foreground=COLOR_TEXT_LIGHT, 
                    background=COLOR_PRIMARY_DARK,
                    borderwidth=0, 
                    focusthickness=0, 
                    focuscolor="none",
                    relief="flat",
                    anchor="center", # Căn giữa chữ
                    padding=[20, 10, 20, 10])
    
    style.map("Sidebar.TButton", 
              background=[('active', '#6d4c41')], # Màu khi rê chuột
              foreground=[('active', COLOR_TEXT_LIGHT)])

    # Nút Sidebar (Khi đang được chọn)
    style.configure("Sidebar.Active.TButton",
                    font=("Segoe UI", 11, "bold"),
                    anchor="center",
                    padding=(10, 12),
                    borderwidth=0,
                    background=COLOR_CONTENT_BG,    # Nền sáng
                    foreground=COLOR_PRIMARY_DARK) # Chữ tối
    
    style.map("Sidebar.Active.TButton",
              background=[("active", COLOR_CONTENT_BG)], # Giữ nguyên màu
              foreground=[("active", COLOR_PRIMARY_DARK)])

    # Nút Đăng xuất
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
    style.configure("KPI.TFrame", background=COLOR_CONTENT_BG, relief="solid", borderwidth=1)
    style.configure("KPI.Title.TLabel", background=COLOR_CONTENT_BG, foreground=COLOR_PRIMARY_DARK, font=("Segoe UI", 14, "bold"))
    
    # (Style giá trị KPI màu xanh/lục/đỏ nằm trong mainmenu_frame.py vì chúng đặc thù)

    # Style cho Nút Sản phẩm (POS)
    style.configure("Product.TButton",
                    font=("Segoe UI", 10),
                    padding=(5, 5),
                    anchor="center",
                    compound="top")