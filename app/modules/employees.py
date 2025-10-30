# app/modules/employees.py
import tkinter as tk
from tkinter import ttk

# Import center_window
from app.utils.utils import clear_window, go_back, center_window 
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

    # =========================================================
    # LOGIC TỰ ĐỘNG THAY ĐỔI KÍCH THƯỚC
    # =========================================================
    
    # Kích thước chuẩn (cho Tab 1, 2)
    DEFAULT_WIDTH = 1200
    DEFAULT_MIN_WIDTH = 1000
    
    # Kích thước rộng (cho Tab 3: Chấm công, Tab 4: Bảng lương)
    WIDE_WIDTH = 1400 
    WIDE_MIN_WIDTH = 1200
    
    HEIGHT = 600

    # Đặt kích thước mặc định ban đầu (cho Tab 1)
    center_window(root, DEFAULT_WIDTH, HEIGHT, offset_y=-60)
    root.minsize(DEFAULT_MIN_WIDTH, 550)

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
    
    # === HÀM XỬ LÝ SỰ KIỆN CHUYỂN TAB ===
    def on_tab_changed(event):
        """Hàm này được gọi mỗi khi người dùng nhấp vào tab mới"""
        try:
            selected_tab_index = notebook.index(notebook.select())
            
            # Tab 2 (Chấm công) hoặc Tab 3 (Bảng lương)
            if selected_tab_index == 2 or selected_tab_index == 3:
                # Cần cửa sổ rộng
                if root.winfo_width() != WIDE_WIDTH:
                    # Gọi hàm center_window để đặt kích thước MỚI
                    center_window(root, WIDE_WIDTH, HEIGHT, offset_y=-60)
                    root.minsize(WIDE_MIN_WIDTH, 550)
            else:
                # Tab 0 (Thông tin) hoặc Tab 1 (Ca làm)
                # Cần cửa sổ chuẩn
                if root.winfo_width() != DEFAULT_WIDTH:
                    # Gọi hàm center_window để đặt kích thước MỚI
                    center_window(root, DEFAULT_WIDTH, HEIGHT, offset_y=-60)
                    root.minsize(DEFAULT_MIN_WIDTH, 550)
        except Exception as e:
            # Xử lý nếu cửa sổ đã bị đóng
            print(f"Lỗi khi đổi tab: {e}")

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
    
    # =========================================================
    #           GẮN SỰ KIỆN VÀO NOTEBOOK
    # =========================================================
    # Dòng này sẽ kích hoạt hàm 'on_tab_changed' mỗi khi bạn đổi tab
    notebook.bind("<<NotebookTabChanged>>", on_tab_changed)


# Chỉ dùng khi chạy độc lập để test UI (không cần mainmenu)
if __name__ == "__main__":
    from app.db import conn
    root = tk.Tk()
    show_employee_module(root, username="admin", role="Admin")
    root.mainloop()