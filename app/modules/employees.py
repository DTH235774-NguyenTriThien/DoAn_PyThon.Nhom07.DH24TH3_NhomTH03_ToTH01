# app/modules/employees.py
import tkinter as tk
from tkinter import ttk
from app.theme import setup_styles

# Import 4 tab con
from app.utils.employee import tab_info, tab_shift, tab_attendance, tab_salary

def create_employee_module(parent_frame, on_back_callback=None):
    """
    Tạo module Quản lý Nhân viên (bố cục 4 tab) bên trong parent_frame.
    """
    setup_styles()

    # Frame chính của module, được nhúng vào parent_frame
    module_frame = tk.Frame(parent_frame, bg="#f5e6ca")
    module_frame.pack(fill="both", expand=True)

    # --- Header ---
    header = tk.Frame(module_frame, bg="#3e2723", height=70)
    header.pack(fill="x")
    tk.Label(
        header,
        text="👨‍💼 HỆ THỐNG QUẢN LÝ NHÂN VIÊN",
        bg="#3e2723",
        fg="white",
        font=("Segoe UI", 18, "bold")
    ).pack(pady=15)

    # --- Notebook (Tabs) ---
    notebook_frame = tk.Frame(module_frame, bg="#f5e6ca")
    notebook_frame.pack(fill="both", expand=True, padx=10, pady=10)

    notebook = ttk.Notebook(notebook_frame)
    notebook.pack(fill="both", expand=True)
    
    # --- Tạo 4 tab con ---
    tab1 = tk.Frame(notebook, bg="#f5e6ca")  # Thông tin nhân viên
    tab2 = tk.Frame(notebook, bg="#f5e6ca")  # Ca làm việc
    tab3 = tk.Frame(notebook, bg="#f5e6ca")  # Chấm công
    tab4 = tk.Frame(notebook, bg="#f5e6ca")  # Bảng lương

    notebook.add(tab1, text="📋 Thông tin nhân viên")
    notebook.add(tab2, text="🕐 Ca làm việc")
    notebook.add(tab3, text="📅 Chấm công")
    notebook.add(tab4, text="💰 Bảng lương")

    # --- Gọi hàm build() cho từng tab con ---
    # (Truyền 'on_back_callback' vào từng tab)
    tab_info.build_tab(tab1, on_back_callback)
    tab_shift.build_tab(tab2, on_back_callback)
    tab_attendance.build_tab(tab3, on_back_callback)
    tab_salary.build_tab(tab4, on_back_callback)

    notebook.select(tab1) # Mở tab Thông tin đầu tiên
    
    # Trả về frame chính của module
    return module_frame