# scripts/seed_inventory.py
import sys
import os
import tkinter as tk
from tkinter import messagebox

# Thêm thư mục gốc của dự án (Doan_Python) vào system path
# Điều này là BẮT BUỘC để script có thể 'import app.db'
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

try:
    from app import db
except ImportError:
    print("Lỗi: Không thể import app.db. Hãy đảm bảo bạn chạy script này từ thư mục gốc,")
    print("hoặc cấu trúc thư mục của bạn đúng.")
    sys.exit(1)

def fill_inventory():
    """
    Cập nhật số lượng tồn kho của TẤT CẢ nguyên liệu về một giá trị mặc định.
    """
    # Bạn có thể thay đổi số lượng này tùy theo đơn vị (ví dụ: 5000 cho 'g'/'ml', 100 cho 'kg'/'l')
    # Nhưng để đơn giản, chúng ta dùng một số chung.
    DEFAULT_QUANTITY = 500.0 
    
    query = "UPDATE NguyenLieu SET SoLuongTon = ?"
    
    # Ẩn cửa sổ root của tkinter
    root = tk.Tk()
    root.withdraw() 
    
    print(f"Đang thực hiện cập nhật kho... Đặt tất cả SoLuongTon = {DEFAULT_QUANTITY}")

    try:
        if db.execute_query(query, (DEFAULT_QUANTITY,)):
            # Lấy số dòng bị ảnh hưởng (nếu cursor hỗ trợ)
            # count = db.cursor.rowcount 
            # (Lưu ý: rowcount có thể không đáng tin cậy với mọi driver pyodbc)
            
            messagebox.showinfo("✅ Thành công", 
                                f"Đã lấp đầy kho!\n\nTất cả nguyên liệu đã được đặt lại số lượng tồn kho = {DEFAULT_QUANTITY}.")
            print("Cập nhật kho thành công.")
        else:
            # Lỗi này đã được xử lý bởi db.execute_query
            print("Cập nhật kho thất bại (Xem thông báo lỗi).")
            
    except Exception as e:
        messagebox.showerror("Lỗi nghiêm trọng", f"Không thể thực thi script:\n{e}")
    finally:
        # Đảm bảo đóng kết nối CSDL
        db.close_db_connection()
        root.destroy()

if __name__ == "__main__":
    fill_inventory()