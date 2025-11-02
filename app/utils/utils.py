# app/utils/utils.py
import tkinter as tk
from tkinter import ttk

"""
Hàm tiện ích UI dùng chung trong app.
"""

def clear_window(root):
    """Xóa mọi widget con của root (dọn màn hình để hiển thị frame mới)."""
    for widget in root.winfo_children():
        widget.destroy()

# =========================================================
# SỬA LỖI: CĂN GIỮA CỬA SỔ POP-UP
# =========================================================
def create_form_window(title, size="430x500", bg="#f8f9fa"):
    """
    Tạo cửa sổ form chuẩn (popup) dùng cho các module Add/Edit.
    (SỬA: Đã thêm logic tự động căn giữa)
    """
    win = tk.Toplevel()
    win.title(title)
    win.configure(bg=bg)
    win.resizable(False, False)

    try:
        # Tách chuỗi size (ví dụ: "430x500")
        width_str, height_str = size.split('x')
        width = int(width_str)
        height = int(height_str)
        
        # Gọi hàm helper center_window (hàm đã có ở dưới)
        # (Chúng ta truyền parent=win.master để nó căn giữa so với cửa sổ chính)
        center_window_relative(win, win.master, width, height) 
        
    except ValueError:
        # Nếu size không đúng định dạng, dùng cách cũ
        win.geometry(size)
        print(f"Cảnh báo: Chuỗi size '{size}' không hợp lệ, không thể căn giữa.")

    form = tk.Frame(win, bg=bg)
    form.pack(padx=20, pady=15, fill="both", expand=True)

    return win, form

def go_back(root, username=None, role=None, on_exit_callback=None):
    """
    (Hàm này đã cũ - các module mới dùng on_back_callback)
    Quay lại menu chính — dùng chung cho mọi module.
    """
    from app.ui.mainmenu_frame import show_main_menu
    # Truyền tất cả 4 đối số
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
# HÀM MỚI: CĂN GIỮA POP-UP (SO VỚI CỬA SỔ CHA)
# =========================================================
def center_window_relative(popup_window, parent_window, width, height):
    """
    Canh giữa một cửa sổ Toplevel (popup) so với cửa sổ cha (parent).
    """
    popup_window.update_idletasks()
    
    # Lấy kích thước và vị trí của cửa sổ cha
    parent_x = parent_window.winfo_x()
    parent_y = parent_window.winfo_y()
    parent_width = parent_window.winfo_width()
    parent_height = parent_window.winfo_height()

    # Tính toán vị trí x, y mới cho popup
    x = parent_x + int((parent_width / 2) - (width / 2))
    y = parent_y + int((parent_height / 2) - (height / 2))

    popup_window.geometry(f"{width}x{height}+{x}+{y}")
    
    # Đảm bảo popup ở trên cùng và khóa cửa sổ cha
    popup_window.transient(parent_window)
    popup_window.grab_set()