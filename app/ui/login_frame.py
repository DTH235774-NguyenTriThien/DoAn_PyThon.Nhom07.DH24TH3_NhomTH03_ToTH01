# app/ui/login_frame.py
import tkinter as tk
from tkinter import messagebox
import configparser
import os

# Thay đổi: Import các hàm chuẩn hóa từ db.py và utils.py
from app.utils.utils import clear_window
from app.db import fetch_query  # Import hàm fetch_query đã chuẩn hóa

def show_login(root):
    """Hiển thị giao diện đăng nhập (icon mật khẩu nằm ngoài textbox, không che)"""
    clear_window(root)
    root.title("Đăng nhập hệ thống quản lý quán cà phê")
    root.geometry("500x400")
    root.configure(bg="#d7ccc8")  # nền nâu nhẹ

    window_width = 550
    window_height = 450
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width / 2) - (window_width / 2))
    y = int((screen_height / 2) - (window_height / 2))
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    root.minsize(150, 200)

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
    btn_toggle.grid(row=1, column=2, padx=(6, 0), pady=(6, 6))

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

    # ==============================================================
    # REFACTOR: Hàm check_login được viết lại
    # ==============================================================
    def check_login():
        user = entry_user.get().strip()
        pw = entry_pass.get().strip()
        
        if not user or not pw:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập tên đăng nhập và mật khẩu!")
            return
        
        # Câu query không đổi
        query = """
            SELECT tk.TenDangNhap, nv.HoTen, tk.Role
            FROM TaiKhoan tk
            LEFT JOIN NhanVien nv ON tk.MaNV = nv.MaNV
            WHERE tk.TenDangNhap = ?
            AND tk.MatKhauHash = CONVERT(NVARCHAR(256), HASHBYTES('SHA2_256', ?), 2)
        """
        
        # Thay vì tự kết nối, chúng ta dùng hàm fetch_query đã chuẩn hóa
        # fetch_query trả về một list[dict]
        results = fetch_query(query, (user, pw))

        if results:
            # Lấy kết quả đầu tiên (và duy nhất)
            user_data = results[0] 
            
            # Truy cập bằng tên cột (dict key)
            username = user_data["TenDangNhap"]
            hoten = user_data["HoTen"]
            role = user_data["Role"]

            # Lưu nhớ (logic này giữ nguyên)
            if remember_var.get():
                rc = configparser.ConfigParser()
                rc["remember"] = {"username": user}
                with open("remember.ini", "w", encoding="utf-8") as f:
                    rc.write(f)
            else:
                if os.path.exists("remember.ini"):
                    os.remove("remember.ini")
            
            messagebox.showinfo("Đăng nhập", f"Xin chào {hoten or username}!\nVai trò: {role}")
            
            # Chuyển sang main menu (giữ nguyên)
            from app.ui.mainmenu_frame import show_main_menu
            show_main_menu(root, username, role)
        else:
            # Sai thông tin
            entry_pass.focus_set()
            messagebox.showerror("Sai thông tin", "Tên đăng nhập hoặc mật khẩu không đúng!")
        
        # Lưu ý: Không cần khối try...except Exception as e:
        # vì hàm fetch_query() trong db.py đã tự xử lý việc này!

    # ==============================================================
    # KẾT THÚC REFACTOR
    # ==============================================================

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