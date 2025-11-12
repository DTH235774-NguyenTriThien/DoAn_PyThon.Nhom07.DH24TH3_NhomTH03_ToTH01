# app/ui/login_frame.py
import tkinter as tk
from tkinter import messagebox
import configparser
import os
import bcrypt 

# Import các helper chuẩn
from app.utils.utils import clear_window, center_window 
from app.db import fetch_query 

def show_login(root, on_exit_callback=None):
    """Hiển thị giao diện đăng nhập (đã nâng cấp lên Bcrypt)"""
    clear_window(root)
    root.title("Đăng nhập hệ thống quản lý quán cà phê")
    root.configure(bg="#d7ccc8") 

    window_width = 550
    window_height = 450
    center_window(root, window_width, window_height) 
    root.minsize(150, 200)

    frame = tk.Frame(root, bg="#fff8e1", bd=2, relief="groove", highlightbackground="#a1887f", highlightthickness=1)
    frame.place(relx=0.5, rely=0.5, anchor="center", width=420, height=360)
    
    tk.Label(frame, text="☕ ĐĂNG NHẬP HỆ THỐNG ☕", font=("Segoe UI", 16, "bold"), bg="#fff8e1", fg="#4e342e").pack(pady=18)
    
    form = tk.Frame(frame, bg="#fff8e1")
    form.pack(padx=30, pady=5, fill="x")
    form.grid_columnconfigure(1, weight=1)
    
    tk.Label(form, text="Tên đăng nhập", font=("Segoe UI", 11), bg="#fff8e1", fg="#4e342e").grid(row=0, column=0, sticky="w", pady=8)
    entry_user = tk.Entry(form, width=28, font=("Segoe UI", 11), bd=1, relief="solid")
    entry_user.grid(row=0, column=1, padx=10, pady=8)
    
    tk.Label(form, text="Mật khẩu", font=("Segoe UI", 11), bg="#fff8e1", fg="#4e342e").grid(row=1, column=0, sticky="w", pady=8)
    
    pw_frame = tk.Frame(form, bg="#fff8e1")
    pw_frame.grid(row=1, column=1, padx=10, pady=8)
    
    entry_pass = tk.Entry(pw_frame, width=24, show="*", font=("Segoe UI", 11), bd=1, relief="solid")
    entry_pass.pack(side="left", fill="x", expand=True)
    
    def toggle_pw():
        if entry_pass.cget("show") == "":
            entry_pass.config(show="*"); btn_toggle.config(text="👁")
        else:
            entry_pass.config(show=""); btn_toggle.config(text="🙈")
            
    btn_toggle = tk.Button(form, text="👁", bg="#fff8e1", bd=0, relief="flat", cursor="hand2", font=("Segoe UI", 10), command=toggle_pw)
    btn_toggle.grid(row=1, column=2, padx=(6, 0), pady=(6, 6))
    
    # Đọc file ghi nhớ
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
    
    btn_frame = tk.Frame(frame, bg="#fff8e1")
    btn_frame.pack(pady=12)

    def check_login():
        user = entry_user.get().strip()
        pw_plain = entry_pass.get().strip()
        
        if not user or not pw_plain:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập tên đăng nhập và mật khẩu!")
            return
        
        query = """
            SELECT tk.TenDangNhap, tk.MatKhauHash, nv.HoTen, tk.Role, tk.MaNV
            FROM TaiKhoan tk
            LEFT JOIN NhanVien nv ON tk.MaNV = nv.MaNV
            WHERE tk.TenDangNhap = ? AND (nv.MaNV IS NULL OR nv.TrangThai != N'Đã nghỉ')
        """
        results = fetch_query(query, (user,))

        if results:
            user_data = results[0]
            hash_from_db_str = user_data.get("MatKhauHash")

            # === SỬA LỖI: Định nghĩa biến Ở ĐÂY (bên ngoài try) ===
            username_login = user_data.get("TenDangNhap", user) 
            hoten = user_data.get("HoTen")
            role = user_data.get("Role", "Unknown")
            employee_id = user_data.get("MaNV") 
            display_name = hoten or username_login
            # ====================================================

            if not hash_from_db_str:
                 messagebox.showerror("Lỗi Hash", f"Tài khoản [{username_login}] không có mật khẩu (hash bị NULL).")
                 return

            try:
                pw_plain_bytes = pw_plain.encode('utf-8')
                hash_from_db_bytes = hash_from_db_str.encode('utf-8')

                if bcrypt.checkpw(pw_plain_bytes, hash_from_db_bytes):
                    
                    # Xử lý Ghi nhớ
                    if remember_var.get():
                        rc = configparser.ConfigParser()
                        rc["remember"] = {"username": user}
                        with open("remember.ini", "w", encoding="utf-8") as f:
                            rc.write(f)
                    else:
                        if os.path.exists("remember.ini"):
                            os.remove("remember.ini")
                    
                    messagebox.showinfo("Đăng nhập", f"Xin chào {display_name}!\nVai trò: {role}")
                    
                    # Chuyển sang Main Menu
                    from app.ui.mainmenu_frame import show_main_menu
                    show_main_menu(root, display_name, role, on_exit_callback, employee_id=employee_id)
                else:
                    entry_pass.focus_set()
                    messagebox.showerror("Sai thông tin", "Tên đăng nhập hoặc mật khẩu không đúng!")
            
            except Exception as e:
                # Bây giờ `username_login` đã tồn tại và có thể hiển thị lỗi
                messagebox.showerror("Lỗi Hash", f"Lỗi định dạng mật khẩu cho [{username_login}]. Vui lòng chạy script đồng bộ.\n{e}")
        else:
            messagebox.showerror("Sai thông tin", "Tên đăng nhập hoặc mật khẩu không đúng!")
            
    def exit_app():
        """Gọi hàm callback 'on_closing' từ main.py để thoát an toàn."""
        if on_exit_callback:
            on_exit_callback() 
        else:
            root.destroy() # Fallback

    btn_login = tk.Button(btn_frame, text="Đăng nhập", bg="#6d4c41", fg="white",
                          font=("Segoe UI", 11, "bold"), width=14, command=check_login, cursor="hand2")
    btn_login.grid(row=0, column=0, padx=8)
    
    btn_exit = tk.Button(btn_frame, text="Thoát", bg="#8d6e63", fg="white",
                         font=("Segoe UI", 11), width=14, command=exit_app, cursor="hand2")
    btn_exit.grid(row=0, column=1, padx=8)

    # Gán phím tắt
    entry_user.bind("<Return>", lambda e: entry_pass.focus_set())
    entry_pass.bind("<Return>", lambda e: check_login())