# app/ui/mainmenu.py
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk  # pip install pillow

# =============================
#  GIAO DIỆN MENU CHÍNH
# =============================
def open_mainmenu(username, role):
    root = tk.Tk()
    root.title("Phần mềm quản lý quán cà phê")
    root.geometry("900x600")
    root.configure(bg="#f5f0e1")

    # ======= TIÊU ĐỀ CHÀO MỪNG =======
    header_frame = tk.Frame(root, bg="#3e2723", height=80)
    header_frame.pack(fill="x")
    tk.Label(
        header_frame,
        text=f"☕ CHÀO MỪNG {username.upper()} - VAI TRÒ: {role.upper()} ☕",
        bg="#3e2723", fg="white",
        font=("Arial", 16, "bold")
    ).pack(pady=20)

    # ======= KHUNG NÚT CHỨC NĂNG =======
    main_frame = tk.Frame(root, bg="#f5f0e1")
    main_frame.pack(pady=40)

    # Cấu hình nút: (Tên, icon, hàm mở module)
    buttons = [
        ("Quản lý nhân viên", "👥", open_employee),
        ("Quản lý đồ uống", "🥤", open_menu),
        ("Quản lý hóa đơn", "🧾", open_invoice),
        ("Thống kê - Báo cáo", "📊", open_report),
        ("Đăng xuất", "🚪", lambda: logout(root))
    ]

    # Tạo lưới nút (2 cột)
    for i, (text, icon, command) in enumerate(buttons):
        btn = ttk.Button(
            main_frame,
            text=f"{icon}\n{text}",
            command=command,
            width=25
        )
        btn.grid(row=i//2, column=i%2, padx=40, pady=20, ipadx=10, ipady=20)

    # ======= NHÃN CHÂN TRANG =======
    footer = tk.Label(
        root,
        text="© 2025 - Phần mềm quản lý quán cà phê | Được phát triển bởi Nguyễn Trí Thiện - Trần Lê Hửu Lý",
        bg="#3e2723", fg="white", font=("Arial", 10)
    )
    footer.pack(side="bottom", fill="x", pady=5)

    root.mainloop()


# =============================
#  CÁC HÀM XỬ LÝ MODULE
# =============================

def open_employee():
    try:
        from app.modules import employees
        employees.open_window(tk._default_root)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể mở module nhân viên: {e}")

def open_menu():
    messagebox.showinfo("Đang phát triển", "Chức năng Quản lý đồ uống sẽ được cập nhật ở Sprint 4 ☕")

def open_invoice():
    messagebox.showinfo("Đang phát triển", "Chức năng Quản lý hóa đơn sẽ có ở Sprint 5 🧾")

def open_report():
    messagebox.showinfo("Đang phát triển", "Chức năng Báo cáo thống kê sẽ có ở Sprint 6 📊")

def logout(window):
    if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn đăng xuất?"):
        window.destroy()
        from app.ui import login
        login.open_login()
