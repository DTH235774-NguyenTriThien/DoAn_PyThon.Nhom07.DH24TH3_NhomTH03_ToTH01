# app/ui/mainmenu_frame.py
import tkinter as tk
from tkinter import ttk
from app.utils import clear_window


def show_main_menu(root, username, role):
    clear_window(root)

    # ====== CẤU HÌNH FORM CHÍNH ======
    root.title("☕ Hệ thống quản lý cà phê - Main Menu")
    root.configure(bg="#f5e6ca")

    window_width = 800
    window_height = 600
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width / 2) - (window_width / 2))
    y = int((screen_height / 2) - (window_height / 2))
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    root.minsize(750, 550)

    # ====== HEADER ======
    header = tk.Frame(root, bg="#4b2e05", height=80)
    header.pack(fill="x")
    tk.Label(
        header,
        text=f"☕ Xin chào {username} ({role}) ☕",
        bg="#4b2e05",
        fg="white",
        font=("Segoe UI", 16, "bold"),
    ).pack(pady=20)

    # ====== KHUNG CHÍNH ======
    main = tk.Frame(root, bg="#f5e6ca")
    main.pack(expand=True, pady=40)

    # ====== STYLE ======
    style = ttk.Style()
    style.theme_use("clam")

    style.configure(
        "Coffee.TButton",
        font=("Segoe UI", 13, "bold"),
        padding=15,
        relief="flat",
        background="#a47148",  # Nâu caramel
        foreground="white",
        borderwidth=0,
    )
    style.map(
        "Coffee.TButton",
        background=[("active", "#8b5e34"), ("pressed", "#6f4518")],
        foreground=[("active", "white")],
    )

    style.configure(
        "Logout.TButton",
        font=("Segoe UI", 13, "bold"),
        padding=15,
        relief="flat",
        background="#c75c5c",
        foreground="white",
        borderwidth=0,
    )
    style.map("Logout.TButton", background=[("active", "#a94442")])

    # ====== KHUNG NÚT ======
    btn_frame = tk.Frame(main, bg="#f5e6ca")
    btn_frame.pack()

    ttk.Button(
        btn_frame,
        text="👥 Quản lý nhân viên",
        style="Coffee.TButton",
        width=25,
        command=lambda: open_employee_module(root),
    ).grid(row=0, column=0, padx=25, pady=20)

    ttk.Button(
        btn_frame,
        text="🥤 Quản lý đồ uống",
        style="Coffee.TButton",
        width=25,
        command=lambda: print("Đồ uống module"),
    ).grid(row=0, column=1, padx=25, pady=20)

    ttk.Button(
        btn_frame,
        text="🧾 Hóa đơn",
        style="Coffee.TButton",
        width=25,
        command=lambda: print("Hóa đơn module"),
    ).grid(row=1, column=0, padx=25, pady=20)

    ttk.Button(
        btn_frame,
        text="📊 Thống kê",
        style="Coffee.TButton",
        width=25,
        command=lambda: print("Thống kê module"),
    ).grid(row=1, column=1, padx=25, pady=20)

    ttk.Button(
        main,
        text="🚪 Đăng xuất",
        style="Logout.TButton",
        width=30,
        command=lambda: go_back_to_login(root),
    ).pack(pady=30)


def open_employee_module(root):
    from app.modules.employees import show_employee_module
    show_employee_module(root)


def go_back_to_login(root):
    from app.ui.login_frame import show_login
    show_login(root)
