import tkinter as tk
from tkinter import messagebox
import pyodbc
import configparser

# =====================================================
#  Hàm khởi tạo giao diện đăng nhập
# =====================================================
def open_login():
    """Hiển thị giao diện đăng nhập hệ thống"""
    # ------------------------
    # Đọc cấu hình kết nối
    # ------------------------
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')

    server = config['database']['server']
    database = config['database']['database']
    driver = config['database']['driver']
    trusted = config['database'].get('trusted_connection', 'yes')

    # ------------------------
    # Kết nối SQL Server
    # ------------------------
    try:
        if trusted.lower() == 'yes':
            conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes;"
        else:
            username = config['database']['username']
            password = config['database']['password']
            conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};"

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        print("✅ Kết nối SQL Server thành công!")

    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể kết nối SQL Server: {e}")
        return

    # =====================================================
    #  Hàm xử lý đăng nhập
    # =====================================================
    def check_login():
        username = entry_username.get().strip()
        password = entry_password.get().strip()

        if username == "" or password == "":
            messagebox.showwarning("Thiếu thông tin", "⚠️ Vui lòng nhập đầy đủ Tên đăng nhập và Mật khẩu!")
            return

        try:
            query = """
                SELECT tk.TenDangNhap, nv.HoTen, tk.Role
                FROM TaiKhoan tk
                LEFT JOIN NhanVien nv ON tk.MaNV = nv.MaNV
                WHERE tk.TenDangNhap = ?
                AND tk.MatKhauHash = CONVERT(NVARCHAR(256), HASHBYTES('SHA2_256', ?), 2)
            """
            cursor.execute(query, (username, password))
            result = cursor.fetchone()

            if result:
                ten_dang_nhap, ten_nv, role = result
                ten_nv = ten_nv if ten_nv else "Không xác định"
                messagebox.showinfo("Thành công", f"🎉 Đăng nhập thành công!\nNgười dùng: {ten_nv}\nVai trò: {role}")
                root.destroy()  # Đóng giao diện đăng nhập
                from app.ui.mainmenu import open_mainmenu
                open_mainmenu(username, role)

            else:
                messagebox.showerror("Thất bại", "❌ Tên đăng nhập hoặc mật khẩu không đúng!")

        except Exception as e:
            messagebox.showerror("Lỗi truy vấn", f"Không thể kiểm tra tài khoản: {e}")

    # =====================================================
    #  Giao diện Tkinter
    # =====================================================
    root = tk.Tk()
    root.title("Đăng nhập hệ thống quản lý quán cà phê")
    root.geometry("420x280")
    root.configure(bg="#f8f9fa")

    title_label = tk.Label(
        root,
        text="☕ ĐĂNG NHẬP HỆ THỐNG ☕",
        font=("Arial", 16, "bold"),
        bg="#f8f9fa",
        fg="#2b2b2b"
    )
    title_label.pack(pady=15)

    frame = tk.Frame(root, bg="#f8f9fa")
    frame.pack(pady=10)

    # --- Nhập tên đăng nhập ---
    tk.Label(frame, text="Tên đăng nhập:", bg="#f8f9fa", font=("Arial", 12)).grid(
        row=0, column=0, sticky="w", padx=10, pady=8)
    entry_username = tk.Entry(frame, width=25, font=("Arial", 12))
    entry_username.grid(row=0, column=1, padx=10, pady=8)

    # --- Nhập mật khẩu ---
    tk.Label(frame, text="Mật khẩu:", bg="#f8f9fa", font=("Arial", 12)).grid(
        row=1, column=0, sticky="w", padx=10, pady=8)
    entry_password = tk.Entry(frame, width=25, show="*", font=("Arial", 12))
    entry_password.grid(row=1, column=1, padx=10, pady=8)

    # --- Nút đăng nhập ---
    btn_login = tk.Button(
        root,
        text="Đăng nhập",
        bg="#007bff",
        fg="white",
        width=18,
        font=("Arial", 11, "bold"),
        command=check_login
    )
    btn_login.pack(pady=10)

    # --- Nút thoát ---
    btn_exit = tk.Button(
        root,
        text="Thoát",
        bg="#dc3545",
        fg="white",
        width=18,
        font=("Arial", 11),
        command=root.destroy
    )
    btn_exit.pack()

    root.mainloop()


# =====================================================
#  Khởi động trực tiếp file
# =====================================================
if __name__ == "__main__":
    open_login()
