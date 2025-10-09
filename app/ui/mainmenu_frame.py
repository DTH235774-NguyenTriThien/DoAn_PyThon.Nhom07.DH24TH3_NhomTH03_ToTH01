# app/ui/mainmenu_frame.py
import tkinter as tk
from tkinter import ttk
from app.utils import clear_window

def show_main_menu(root, username, role):
    clear_window(root)
    root.configure(bg="#f5f0e1")

    header = tk.Frame(root, bg="#3e2723", height=80)
    header.pack(fill="x")
    tk.Label(header, text=f"☕ Xin chào {username} ({role}) ☕",
             bg="#3e2723", fg="white", font=("Arial", 16, "bold")).pack(pady=20)

    main = tk.Frame(root, bg="#f5f0e1")
    main.pack(expand=True)

    # 👉 Gọi module employees thật khi click
    ttk.Button(
        main,
        text="👥 Quản lý nhân viên",
        width=25,
        command=lambda: open_employee_module(root)
    ).grid(row=0, column=0, padx=30, pady=15)

    ttk.Button(main, text="🥤 Quản lý đồ uống", width=25,
               command=lambda: print("Đồ uống module")).grid(row=0, column=1, padx=30, pady=15)
    ttk.Button(main, text="🧾 Hóa đơn", width=25,
               command=lambda: print("Hóa đơn module")).grid(row=1, column=0, padx=30, pady=15)
    ttk.Button(main, text="📊 Thống kê", width=25,
               command=lambda: print("Thống kê module")).grid(row=1, column=1, padx=30, pady=15)

    ttk.Button(main, text="🚪 Đăng xuất", width=25,
               command=lambda: go_back_to_login(root)).grid(row=2, column=0, columnspan=2, pady=40)


def open_employee_module(root):
    """Mở giao diện quản lý nhân viên"""
    from app.modules.employees import show_employee_module
    show_employee_module(root)


def go_back_to_login(root):
    from app.ui.login_frame import show_login
    show_login(root)
