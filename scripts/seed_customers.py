# scripts/seed_customers.py
import sys
import os
import tkinter as tk
from tkinter import messagebox
from decimal import Decimal

# --- Cấu hình Path (Giống script trước) ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

try:
    from app import db
    from app.db import execute_query
    from app.utils.id_helpers import generate_next_makh
except ImportError:
    print("Lỗi: Không thể import app.db.")
    sys.exit(1)

# =========================================================
# DỮ LIỆU SEEDING KHÁCH HÀNG
# (SỬA LỖI: Đã xóa cột 'TrangThai')
# =========================================================
SEED_CUSTOMERS = [
    # MaKH sẽ được sinh tự động
    {"TenKH": "Trần Văn An", "SDT": "0901112221", "DiemTichLuy": 50},
    {"TenKH": "Nguyễn Thị Bình", "SDT": "0901112222", "DiemTichLuy": 120},
    {"TenKH": "Lê Minh Cường", "SDT": "0901112223", "DiemTichLuy": 0},
    {"TenKH": "Phạm Hoàng Dũng", "SDT": "0901112224", "DiemTichLuy": 250},
    {"TenKH": "Võ Thu Hà", "SDT": "0901112225", "DiemTichLuy": 15},
    {"TenKH": "Đặng Gia Huy", "SDT": "0901112226", "DiemTichLuy": 0},
    {"TenKH": "Hoàng Yến Linh", "SDT": "0901112227", "DiemTichLuy": 85},
    {"TenKH": "Ngô Bảo Long", "SDT": "0901112228", "DiemTichLuy": 30},
    {"TenKH": "Trịnh Mai Phương", "SDT": "0901112229", "DiemTichLuy": 500},
    {"TenKH": "Lý Hùng", "SDT": "0901112230", "DiemTichLuy": 10},
]

def run_seeding():
    """
    Thêm khách hàng mẫu vào CSDL.
    Không xóa dữ liệu cũ.
    """
    
    root = tk.Tk()
    root.withdraw() 
    
    if not messagebox.askyesno("Xác nhận",
        "Script này sẽ THÊM MỚI khoảng 10 khách hàng mẫu vào CSDL.\n"
        "(Nó sẽ KHÔNG xóa khách hàng hiện có của bạn).\n\n"
        "Bạn có muốn tiếp tục?"):
        print("Đã hủy bỏ seeding.")
        root.destroy()
        return

    customers_added = 0
    warnings = []

    try:
        print("Bắt đầu thêm khách hàng mẫu...")

        for cust in SEED_CUSTOMERS:
            # 1. Sinh MaKH tự động
            makh = generate_next_makh(db.cursor)
            
            # 2. Lấy thông tin
            ten = cust["TenKH"]
            sdt = cust["SDT"]
            diem = cust["DiemTichLuy"]
            # (Đã xóa 'trangthai')
            
            # 3. Chèn vào CSDL
            # SỬA LỖI: Xóa cột TrangThai khỏi query
            query = """
                INSERT INTO KhachHang (MaKH, TenKH, SDT, DiemTichLuy)
                VALUES (?, ?, ?, ?)
            """
            params = (makh, ten, sdt, diem)
            
            if execute_query(query, params):
                customers_added += 1
            else:
                warnings.append(f"Lỗi khi thêm khách hàng: {ten}")

        # Hoàn tất
        if not warnings:
            messagebox.showinfo("✅ Thành công",
                                f"Seeding khách hàng thành công!\n\n"
                                f"Đã thêm: {customers_added} khách hàng mới.")
            print("Seeding hoàn tất.")
        else:
            messagebox.showwarning("Hoàn tất (Có cảnh báo)",
                                   f"Đã thêm {customers_added} khách hàng.\n"
                                   f"Lỗi: {warnings[0]}")
            print(f"Cảnh báo: {warnings[0]}")

    except Exception as e:
        db.conn.rollback() 
        messagebox.showerror("Lỗi nghiêm trọng", f"Đã xảy ra lỗi:\n{e}")
    finally:
        db.close_db_connection()
        root.destroy()
        print("Đã đóng kết nối CSDL.")

# --- HÀM CHẠY CHÍNH ---
if __name__ == "__main__":
    if db.conn:
        run_seeding()
    else:
        print("Không thể kết nối CSDL.")