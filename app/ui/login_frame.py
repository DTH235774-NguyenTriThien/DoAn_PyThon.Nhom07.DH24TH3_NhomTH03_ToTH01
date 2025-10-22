# app/ui/login_frame.py
import tkinter as tk
from tkinter import messagebox
import pyodbc, configparser, os
from app.utils import clear_window

def show_login(root):
    """Hiển thị giao diện đăng nhập (icon mật khẩu nằm ngoài textbox, không che)"""
    clear_window(root)
    root.title("Đăng nhập hệ thống quản lý quán cà phê")
    root.geometry("500x400")
    root.configure(bg="#d7ccc8")  # nền nâu nhẹ

    # Card chính
    frame = tk.Frame(root, bg="#fff8e1", bd=2, relief="groove", highlightbackground="#a1887f", highlightthickness=1)
    frame.place(relx=0.5, rely=0.5, anchor="center", width=420, height=360)

    tk.Label(frame, text="☕ ĐĂNG NHẬP HỆ THỐNG ☕",
             font=("Segoe UI", 16, "bold"), bg="#fff8e1", fg="#4e342e").pack(pady=18)

    # form (sử dụng grid, cột 1 là entry mở rộng)
    form = tk.Frame(frame, bg="#fff8e1")
    form.pack(padx=30, pady=5, fill="x")

    # đảm bảo cột 1 (entry) mở rộng
    form.grid_columnconfigure(1, weight=1)

  # --- Tên đăng nhập ---
    tk.Label(form, text="Tên đăng nhập", font=("Segoe UI", 11), bg="#fff8e1", fg="#4e342e")\
        .grid(row=0, column=0, sticky="w", pady=8)
    entry_user = tk.Entry(form, width=28, font=("Segoe UI", 11), bd=1, relief="solid")
    entry_user.grid(row=0, column=1, padx=10, pady=8)

    # --- Mật khẩu ---
    tk.Label(form, text="Mật khẩu", font=("Segoe UI", 11), bg="#fff8e1", fg="#4e342e")\
        .grid(row=1, column=0, sticky="w", pady=8)

    pw_frame = tk.Frame(form, bg="#fff8e1")
    pw_frame.grid(row=1, column=1, padx=10, pady=8)

    entry_pass = tk.Entry(pw_frame, width=24, show="*", font=("Segoe UI", 11), bd=1, relief="solid")
    entry_pass.pack(side="left", fill="x", expand=True)


    # nút icon nằm ngoài textbox (cột 2)
    def toggle_pw():
        if entry_pass.cget("show") == "":
            entry_pass.config(show="*")
            btn_toggle.config(text="👁")
        else:
            entry_pass.config(show="")
            btn_toggle.config(text="🙈")

    btn_toggle = tk.Button(form, text="👁", bg="#fff8e1", bd=0, relief="flat",
                           cursor="hand2", font=("Segoe UI", 10), command=toggle_pw)
    btn_toggle.grid(row=1, column=2, padx=(6,0), pady=(6,6))

    # Ghi nhớ đăng nhập (dưới form)
    remembered_user = ""
    if os.path.exists("remember.ini"):
        rcfg = configparser.ConfigParser()
        rcfg.read("remember.ini", encoding="utf-8")
        remembered_user = rcfg.get("remember", "username", fallback="")

    entry_user.delete(0, tk.END)
    if remembered_user:
        entry_user.insert(0, remembered_user)

    remember_var = tk.BooleanVar(value=bool(remembered_user))
    chk = tk.Checkbutton(frame, text="Ghi nhớ đăng nhập", bg="#fff8e1", variable=remember_var, font=("Segoe UI", 10))
    chk.pack(anchor="w", padx=36, pady=(6, 8))

    # Nút chức năng: hai nút ngang hàng, đều nhau
    btn_frame = tk.Frame(frame, bg="#fff8e1")
    btn_frame.pack(pady=12)
    def check_login():
        user = entry_user.get().strip()
        pw = entry_pass.get().strip()
        if not user or not pw:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập tên đăng nhập và mật khẩu!")
            return
        try:
            cfg = configparser.ConfigParser()
            cfg.read('config.ini', encoding='utf-8')
            server = cfg['database']['server']
            database = cfg['database']['database']
            driver = cfg['database']['driver']
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
                # Lưu nhớ
                if remember_var.get():
                    rc = configparser.ConfigParser()
                    rc["remember"] = {"username": user}
                    with open("remember.ini", "w", encoding="utf-8") as f:
                        rc.write(f)
                else:
                    if os.path.exists("remember.ini"):
                        os.remove("remember.ini")
                messagebox.showinfo("Đăng nhập", f"Xin chào {hoten or username}!\nVai trò: {role}")
                from app.ui.mainmenu_frame import show_main_menu
                show_main_menu(root, username, role)
            else:
                # hiệu ứng: chọn textbox password và highlight nhỏ (tuỳ ý)
                entry_pass.focus_set()
                messagebox.showerror("Sai thông tin", "Tên đăng nhập hoặc mật khẩu không đúng!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể kết nối SQL Server:\n{e}")

    # hai nút bằng nhau
    btn_login = tk.Button(btn_frame, text="Đăng nhập", bg="#6d4c41", fg="white",
                          font=("Segoe UI", 11, "bold"), width=14, command=check_login, cursor="hand2")
    btn_login.grid(row=0, column=0, padx=8)
    btn_exit = tk.Button(btn_frame, text="Thoát", bg="#8d6e63", fg="white",
                         font=("Segoe UI", 11), width=14, command=root.destroy, cursor="hand2")
    btn_exit.grid(row=0, column=1, padx=8)

    # Enter bindings
    entry_user.bind("<Return>", lambda e: entry_pass.focus_set())
    entry_pass.bind("<Return>", lambda e: check_login())