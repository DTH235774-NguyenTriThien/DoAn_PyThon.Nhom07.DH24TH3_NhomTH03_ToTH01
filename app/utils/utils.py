# app/utils/utils.py
import tkinter as tk
from tkinter import ttk
# SỬA 1: Thêm 2 import cần thiết cho resource_path
import os
import sys

"""
Hàm tiện ích UI dùng chung trong app.
"""

# =========================================================
# SỬA 2: THÊM HÀM `resource_path` (DÙNG CHO ĐÓNG GÓI .EXE)
# (Đây là hàm bị thiếu)
# =========================================================
def resource_path(relative_path):
    """ 
    Lấy đường dẫn tuyệt đối đến tài nguyên, hoạt động cho cả .py (dev) 
    và .exe (đã đóng gói).
    """
    try:
        # PyInstaller tạo một thư mục temp và lưu đường dẫn trong _MEIPASS
        # os.path.join(sys._MEIPASS, relative_path)
        # Sửa lại cho đúng cấu trúc: file .exe sẽ ở cùng cấp với app/
        base_path = sys._MEIPASS
    except Exception:
        # Nếu chạy bằng .py, base_path là thư mục gốc của dự án (Doan_Python)
        # (Giả định utils.py nằm trong app/utils/)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    return os.path.join(base_path, relative_path)


def clear_window(root):
    """Xóa mọi widget con của root (dọn màn hình để hiển thị frame mới)."""
    for widget in root.winfo_children():
        widget.destroy()

# =========================================================
# HÀM TẠO CỬA SỔ POP-UP (Đã sửa để căn giữa)
# =========================================================
def create_form_window(title, size="430x500", bg="#f8f9fa"):
    """
    Tạo cửa sổ form chuẩn (popup) dùng cho các module Add/Edit.
    (Đã thêm logic tự động căn giữa)
    """
    win = tk.Toplevel()
    win.title(title)
    win.configure(bg=bg)
    win.resizable(False, False)

    try:
        width_str, height_str = size.split('x')
        width = int(width_str)
        height = int(height_str)
        
        # Gọi hàm helper center_window_relative
        center_window_relative(win, win.master, width, height) 
        
    except ValueError:
        win.geometry(size)
        print(f"Cảnh báo: Chuỗi size '{size}' không hợp lệ, không thể căn giữa.")

    form = tk.Frame(win, bg=bg)
    form.pack(padx=20, pady=15, fill="both", expand=True)

    return win, form

def go_back(root, username=None, role=None, on_exit_callback=None):
    """ (Hàm này đã cũ) """
    from app.ui.mainmenu_frame import show_main_menu
    show_main_menu(root, username, role, on_exit_callback)

def center_window(win, width, height, offset_y=-30):
    """Canh giữa màn hình cho một cửa sổ Tkinter (dùng cho cửa sổ CHÍNH)"""
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2) + offset_y)
    win.geometry(f"{width}x{height}+{x}+{y}")

# =========================================================
# HÀM CĂN GIỮA POP-UP (Đã thêm ở bước trước)
# =========================================================
def center_window_relative(popup_window, parent_window, width, height):
    """
    Canh giữa một cửa sổ Toplevel (popup) so với cửa sổ cha (parent).
    """
    popup_window.update_idletasks()
    
    parent_x = parent_window.winfo_x()
    parent_y = parent_window.winfo_y()
    parent_width = parent_window.winfo_width()
    parent_height = parent_window.winfo_height()

    x = parent_x + int((parent_width / 2) - (width / 2))
    y = parent_y + int((parent_height / 2) - (height / 2))

    popup_window.geometry(f"{width}x{height}+{x}+{y}")
    
    popup_window.transient(parent_window)
    popup_window.grab_set()