# app/main.py
import tkinter as tk
from app.ui.login_frame import show_login

from app import db
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    plt = None
    MATPLOTLIB_AVAILABLE = False

def main():
    root = tk.Tk()
    from app.theme import setup_styles
    setup_styles()
    root.title("Phần mềm quản lý quán cà phê")
    root.geometry("900x600")
    root.configure(bg="#f5f0e1")

    def on_closing():
        """
        Hàm này được gọi khi người dùng nhấn nút "X" của cửa sổ.
        Nó sẽ dọn dẹp CSDL và Matplotlib trước khi thoát.
        """
        try:
            # 1. Đóng kết nối CSDL
            if db and db.conn:
                db.close_db_connection() 
                
            # 2. Đóng tất cả biểu đồ matplotlib
            if MATPLOTLIB_AVAILABLE:
                plt.close('all')
                
        except Exception as e:
            pass # Bỏ qua bất kỳ lỗi nào xảy ra trong quá trình đóng
        finally:
            # 3. Phá hủy cửa sổ root (thoát ứng dụng)
            root.destroy()

    # Ghi đè hành vi mặc định của nút "X" (WM_DELETE_WINDOW)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Truyền hàm 'on_closing' vào login_frame
    show_login(root, on_exit_callback=on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()