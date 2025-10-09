# app/ui/login_frame.py
import tkinter as tk
from tkinter import messagebox
import pyodbc, configparser
from app.utils import clear_window   # <-- thay đổi ở đây

def show_login(root):
    """Hiển thị giao diện đăng nhập"""

    clear_window(root)
    frame = tk.Frame(root, bg="#f8f9fa")
    frame.pack(expand=True)

    tk.Label(frame, text="☕ ĐĂNG NHẬP HỆ THỐNG ☕",
             font=("Arial", 18, "bold"), bg="#f8f9fa", fg="#2b2b2b").pack(pady=20)

    frm_inputs = tk.Frame(frame, bg="#f8f9fa")
    frm_inputs.pack()

    tk.Label(frm_inputs, text="Tên đăng nhập:", font=("Arial", 12), bg="#f8f9fa").grid(row=0, column=0, sticky="w", pady=8)
    entry_user = tk.Entry(frm_inputs, width=25, font=("Arial", 12))
    entry_user.grid(row=0, column=1, pady=8)

    tk.Label(frm_inputs, text="Mật khẩu:", font=("Arial", 12), bg="#f8f9fa").grid(row=1, column=0, sticky="w", pady=8)
    entry_pass = tk.Entry(frm_inputs, show="*", width=25, font=("Arial", 12))
    entry_pass.grid(row=1, column=1, pady=8)

    def check_login():
        user = entry_user.get().strip()
        pw = entry_pass.get().strip()
        if not user or not pw:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập tên đăng nhập và mật khẩu!")
            return

        try:
            config = configparser.ConfigParser()
            config.read('config.ini', encoding='utf-8')
            server = config['database']['server']
            database = config['database']['database']
            driver = config['database']['driver']
            conn = pyodbc.connect(f"DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes;")
            cursor = conn.cursor()

            query = """
                SELECT tk.TenDangNhap, nv.HoTen, tk.Role
                FROM TaiKhoan tk
                LEFT JOIN NhanVien nv ON tk.MaNV = nv.MaNV
                WHERE tk.TenDangNhap = ?
                AND tk.MatKhauHash = CONVERT(NVARCHAR(256), HASHBYTES('SHA2_256', ?), 2)
            """
            cursor.execute(query, (user, pw))
            result = cursor.fetchone()
            if result:
                username, hoten, role = result
                messagebox.showinfo("Đăng nhập", f"Xin chào {hoten or 'người dùng'}!\nVai trò: {role}")
                # import cục bộ tránh circular import
                from app.ui.mainmenu_frame import show_main_menu
                show_main_menu(root, username, role)
            else:
                messagebox.showerror("Sai thông tin", "Tên đăng nhập hoặc mật khẩu không đúng!")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể kết nối SQL Server: {e}")

    tk.Button(frame, text="Đăng nhập", width=18, bg="#007bff", fg="white",
              font=("Arial", 11, "bold"), command=check_login).pack(pady=15)

    tk.Button(frame, text="Thoát", width=18, bg="#dc3545", fg="white",
              font=("Arial", 11), command=root.destroy).pack(pady=5)
