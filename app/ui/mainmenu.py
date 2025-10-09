import tkinter as tk
from tkinter import ttk, messagebox

class MainMenu(tk.Tk):
    def __init__(self, username, role, ma_nv=None):
        super().__init__()
        self.title("Quản lý Quán Cà Phê - Menu chính")
        self.geometry("800x480")
        self.username = username
        self.role = role

        header = ttk.Frame(self, padding=10)
        header.pack(fill='x')
        ttk.Label(header, text=f"Người dùng: {username} | Vai trò: {role}").pack(side='left')
        ttk.Button(header, text="Đăng xuất", command=self.logout).pack(side='right')

        body = ttk.Frame(self, padding=20)
        body.pack(fill='both', expand=True)

        ttk.Button(body, text="Quản lý nhân viên", command=self.open_employee).grid(row=0, column=0, padx=10, pady=10, sticky='ew')

        # role-based: nếu không phải admin/manager thì ẩn/khóa một số nút
        if role.lower() not in ('admin','manager'):
            # ví dụ: disable delete-heavy features later
            pass

    def logout(self):
        self.destroy()
        from app.ui.login import root as login_root  # or re-open login
        from app.ui.login import LoginWindow
        LoginWindow().mainloop()

    def open_employee(self):
        from app.modules.employees import open_window
        open_window(self)
