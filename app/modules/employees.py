# app/modules/employees.py
import tkinter as tk
from tkinter import ttk
from app.theme import setup_styles

# Import 4 tab con
from app.utils.employee import tab_info, tab_shift, tab_attendance, tab_salary

# SỬA 1: Đổi tên hàm VÀ XÓA username, role (Hoàn tất Giai đoạn 2)
def create_employee_module(parent_frame, on_back_callback=None):
    """
    Tạo module Quản lý Nhân viên (bố cục 4 tab) bên trong parent_frame.
    """
    # SỬA 2: Xóa clear_window, center_window, root.title...
    setup_styles()

    # SỬA 3: Tạo frame chính của module bên trong parent_frame
    module_frame = tk.Frame(parent_frame, bg="#f5e6ca")
    module_frame.pack(fill="both", expand=True)

    # === HEADER (Giữ nguyên, nhưng pack vào module_frame) ===
    header = tk.Frame(module_frame, bg="#3e2723", height=70)
    header.pack(fill="x")
    tk.Label(
        header,
        text="👨‍💼 HỆ THỐNG QUẢN LÝ NHÂN VIÊN",
        bg="#3e2723",
        fg="white",
        font=("Segoe UI", 18, "bold")
    ).pack(pady=15)

    # === NOTEBOOK (Giữ nguyên, nhưng pack vào module_frame) ===
    notebook_frame = tk.Frame(module_frame, bg="#f5e6ca")
    notebook_frame.pack(fill="both", expand=True, padx=10, pady=10)

    notebook = ttk.Notebook(notebook_frame)
    notebook.pack(fill="both", expand=True)
    
    # (Hàm on_tab_changed không còn cần thiết vì mainmenu quản lý kích thước)

    # === TẠO 4 TAB (Giữ nguyên) ===
    tab1 = tk.Frame(notebook, bg="#f5e6ca")  # Thông tin nhân viên
    tab2 = tk.Frame(notebook, bg="#f5e6ca")  # Ca làm việc
    tab3 = tk.Frame(notebook, bg="#f5e6ca")  # Chấm công
    tab4 = tk.Frame(notebook, bg="#f5e6ca")  # Bảng lương

    notebook.add(tab1, text="📋 Thông tin nhân viên")
    notebook.add(tab2, text="🕐 Ca làm việc")
    notebook.add(tab3, text="📅 Chấm công")
    notebook.add(tab4, text="💰 Bảng lương")

    # SỬA 4: GỌI CÁC TAB CON và TRUYỀN on_back_callback
    tab_info.build_tab(tab1, on_back_callback)
    tab_shift.build_tab(tab2, on_back_callback)
    tab_attendance.build_tab(tab3, on_back_callback)
    tab_salary.build_tab(tab4, on_back_callback)

    notebook.select(tab1)
    
    # SỬA 5: THÊM LỆNH RETURN ĐỂ SỬA LỖI 'NoneType'
    return module_frame