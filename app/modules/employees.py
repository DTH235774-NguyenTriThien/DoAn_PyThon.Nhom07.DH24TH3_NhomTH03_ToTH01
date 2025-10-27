import tkinter as tk
from tkinter import ttk
from app.utils.utils import clear_window, go_back,center_window
from app.theme import setup_styles

# Import 4 tab con (mỗi tab là 1 file riêng)
from app.utils.employee import tab_info, tab_shift, tab_attendance, tab_salary


def show_employee_module(root, username=None, role=None):
    """Giao diện quản lý nhân viên (phiên bản mở rộng với 4 tab)"""
    # === Cấu hình chung ===
    clear_window(root)
    setup_styles()

    root.title("📋 Quản lý nhân viên - Phiên bản mở rộng")
    root.configure(bg="#f5e6ca")
    center_window(root, 1200, 600, offset_y=-60)
    root.minsize(1000, 550)

    # === HEADER ===
    header = tk.Frame(root, bg="#3e2723", height=70)
    header.pack(fill="x")
    tk.Label(
        header,
        text="👨‍💼 HỆ THỐNG QUẢN LÝ NHÂN VIÊN",
        bg="#3e2723",
        fg="white",
        font=("Segoe UI", 18, "bold")
    ).pack(pady=15)

    # === NOTEBOOK (4 TAB) ===
    notebook_frame = tk.Frame(root, bg="#f5e6ca")
    notebook_frame.pack(fill="both", expand=True, padx=10, pady=10)

    notebook = ttk.Notebook(notebook_frame)
    notebook.pack(fill="both", expand=True)

    # === TẠO 4 TAB ===
    tab1 = tk.Frame(notebook, bg="#f5e6ca")  # Thông tin nhân viên
    tab2 = tk.Frame(notebook, bg="#f5e6ca")  # Ca làm việc
    tab3 = tk.Frame(notebook, bg="#f5e6ca")  # Chấm công
    tab4 = tk.Frame(notebook, bg="#f5e6ca")  # Bảng lương

    notebook.add(tab1, text="📋 Thông tin nhân viên")
    notebook.add(tab2, text="🕐 Ca làm việc")
    notebook.add(tab3, text="📅 Chấm công")
    notebook.add(tab4, text="💰 Bảng lương")

    # === GỌI CÁC TAB CON ===
    tab_info.build_tab(tab1, root, username, role)
    tab_shift.build_tab(tab2, root, username, role)
    tab_attendance.build_tab(tab3, root, username, role)
    tab_salary.build_tab(tab4,root, username, role)

    # === MẸO: Đặt tab đầu tiên làm mặc định ===
    notebook.select(tab1)

    # === Thông báo debug nhẹ (tùy chọn) ===


# Chỉ dùng khi chạy độc lập để test UI (không cần mainmenu)
if __name__ == "__main__":
    from app.db import conn
    root = tk.Tk()
    show_employee_module(root, username="admin", role="Admin")
    root.mainloop()
