# app/utils/utils.py
import tkinter as tk
from tkinter import ttk

"""
Hàm tiện ích UI dùng chung trong app.
Các hàm nghiệp vụ đã được chuyển sang:
- time_helpers.py
- id_helpers.py
- business_helpers.py
"""

def clear_window(root):
    """Xóa mọi widget con của root (dọn màn hình để hiển thị frame mới)."""
    for widget in root.winfo_children():
        widget.destroy()

def create_form_window(title, size="430x500", bg="#f8f9fa"):
    """
    Tạo cửa sổ form chuẩn (popup) dùng cho các module Add/Edit.
    Trả về tuple (win, form, entries)
    """
    win = tk.Toplevel()
    win.title(title)
    win.geometry(size)
    win.resizable(False, False)
    win.configure(bg=bg)

    form = tk.Frame(win, bg=bg)
    form.pack(padx=20, pady=15, fill="both", expand=True)

    return win, form

def go_back(root, username=None, role=None):
    """
    Quay lại menu chính — dùng chung cho mọi module.
    """
    # Import cục bộ để tránh lỗi circular import
    from app.ui.mainmenu_frame import show_main_menu
    show_main_menu(root, username, role)

def center_window(win, width, height, offset_y=-30):
    """Canh giữa màn hình cho một cửa sổ Tkinter"""
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2) + offset_y)
    win.geometry(f"{width}x{height}+{x}+{y}")