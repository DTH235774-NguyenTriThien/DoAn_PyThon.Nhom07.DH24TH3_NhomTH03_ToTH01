import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import bcrypt
from app import db

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Đăng nhập - Quản lý Quán Cà Phê")
        self.geometry("450x300")
        self.resizable(False, False)
        self.configure(bg="#ECEFF1")  # màu nền dịu mắt

        # ===== Header với logo =====
        header_frame = tk.Frame(self, bg="#ECEFF1")
        header_frame.pack(pady=10)
        
        # Load icon/logo (thay đường dẫn bằng icon thực tế của bạn)
        try:
            logo = Image.open("assets/logo.png").resize((60, 60))
            self.logo_img = ImageTk.PhotoImage(logo)
            tk.Label(header_frame, image=self.logo_img, bg="#ECEFF1").pack(side="left", padx=10)
        except:
            tk.Label(header_frame, text="☕", font=("Segoe UI", 32), bg="#ECEFF1").pack(side="left", padx=10)

        tk.Label(header_frame, text="Quản lý Quán Cà Phê", font=("Segoe UI", 20, "bold"), bg="#ECEFF1").pack(side="left")

        # ===== Frame chính =====
        frm = tk.Frame(self, bg="#ffffff", padx=30, pady=10, bd=1, relief="solid")
        frm.pack(pady=20)

        tk.Label(frm, text="Đăng nhập", font=("Segoe UI", 16, "bold"), bg="#ffffff").grid(row=0, column=0, columnspan=3, pady=(0,15))

        # Cấu hình cột để canh đều label và ô nhập
        frm.grid_columnconfigure(0, minsize=120)
        frm.grid_columnconfigure(1, weight=1)

        # ===== Username =====
        tk.Label(frm, text="Tên đăng nhập:", bg="#ffffff", anchor='e', width=15).grid(row=1, column=0, sticky='e', pady=5, padx=(0,10))
        self.username = tk.StringVar()
        user_entry = ttk.Entry(frm, textvariable=self.username, width=30, font=("Segoe UI", 10))
        user_entry.grid(row=1, column=1, columnspan=2, sticky='w', pady=5)

        # ===== Password =====
        tk.Label(frm, text="Mật khẩu:", bg="#ffffff", anchor='e', width=15).grid(row=2, column=0, sticky='e', pady=5, padx=(0,10))
        self.password = tk.StringVar()
        self.pwd_entry = ttk.Entry(frm, textvariable=self.password, show="•", width=30, font=("Segoe UI", 10))
        self.pwd_entry.grid(row=2, column=1, sticky='w', pady=5)
        
        # Nút hiển thị/ẩn mật khẩu
        self.show_pwd = False
        show_btn = tk.Button(frm, text="👁", command=self.toggle_password, relief="flat", bg="#ffffff")
        show_btn.grid(row=2, column=2, padx=(5,0))

        # ===== Buttons =====
        btn_frame = tk.Frame(frm, bg="#ffffff")
        btn_frame.grid(row=3, column=0, columnspan=3, pady=10)

        login_btn = tk.Button(btn_frame, text="Đăng nhập", width=15, bg="#1976D2", fg="white", font=("Segoe UI", 10, "bold"), command=self.login)
        login_btn.pack(side="left", padx=10)

        exit_btn = tk.Button(btn_frame, text="Thoát", width=15, bg="#E53935", fg="white", font=("Segoe UI", 10, "bold"), command=self.destroy)
        exit_btn.pack(side="left", padx=10)

        # Enter key login
        self.bind('<Return>', lambda e: self.login())

        # Focus vào ô nhập username
        user_entry.focus()

    def toggle_password(self):
        self.show_pwd = not self.show_pwd
        self.pwd_entry.config(show="" if self.show_pwd else "•")

    def login(self):
        user = self.username.get().strip()
        pwd = self.password.get().strip()

        if not user or not pwd:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập tên đăng nhập và mật khẩu.")
            return

        row = db.fetch_one("SELECT MatKhauHash, Role, MaNV FROM TaiKhoan WHERE TenDangNhap = ?", (user,))
        if not row:
            messagebox.showerror("Lỗi", "Tài khoản không tồn tại.")
            return

        stored = row.get('MatKhauHash')
        if stored is None:
            messagebox.showerror("Lỗi", "Tài khoản chưa cấu hình mật khẩu.")
            return

        try:
            ok = bcrypt.checkpw(pwd.encode('utf-8'), stored.encode('utf-8'))
        except Exception:
            ok = False

        if ok:
            messagebox.showinfo("Thành công", f"Đăng nhập thành công. Vai trò: {row.get('Role')}")
            self.destroy()
            from app.ui.mainmenu import MainMenu
            MainMenu(username=user, role=row.get('Role'), ma_nv=row.get('MaNV')).mainloop()
        else:
            messagebox.showerror("Lỗi", "Mật khẩu không đúng.")

if __name__ == "__main__":
    window = LoginWindow()
    window.mainloop()