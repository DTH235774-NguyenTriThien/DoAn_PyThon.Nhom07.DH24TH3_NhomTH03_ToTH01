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
