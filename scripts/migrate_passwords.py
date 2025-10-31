# scripts/migrate_passwords.py
import bcrypt
import sys
import os

# Thêm thư mục gốc vào system path để import app.db
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.db import fetch_query, execute_query, conn
except ImportError:
    print("LỖI: Không thể import 'app.db'.")
    print("Hãy đảm bảo bạn chạy script này từ thư mục gốc (Doan_Python), không phải từ 'scripts/'")
    sys.exit(1)

PASSWORD_TO_SET = '123'

def generate_hash(password):
    pw_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_pw = bcrypt.hashpw(pw_bytes, salt)
    return hashed_pw.decode('utf-8')

def seed_accounts():
    """
    Xóa sạch và tạo lại 4 tài khoản mẫu với mật khẩu '123' (bcrypt).
    """
    print(f"Bắt đầu làm sạch và tạo tài khoản (Mật khẩu: '{PASSWORD_TO_SET}')...")

    try:
        # 1. Xóa tất cả tài khoản cũ
        execute_query("DELETE FROM TaiKhoan")
        print("Đã xóa tài khoản cũ...")

        # 2. Định nghĩa tài khoản
        accounts = [
            ('admin', 'Admin', 'NV001'),
            ('nv002', 'Cashier', 'NV002'),
            ('nv004', 'Barista', 'NV004'),
            ('nv005', 'Cashier', 'NV005')
        ]

        count_success = 0
        for (user, role, manv) in accounts:
            hashed_string = generate_hash(PASSWORD_TO_SET)

            query = "INSERT INTO TaiKhoan (TenDangNhap, MatKhauHash, Role, MaNV) VALUES (?, ?, ?, ?)"
            if execute_query(query, (user, hashed_string, role, manv)):
                print(f"  [THÀNH CÔNG] Đã tạo tài khoản: {user}")
                count_success += 1
            else:
                print(f"  [THẤT BẠI] Không thể tạo: {user}")

        print(f"\nHoàn tất! Đã tạo thành công {count_success}/{len(accounts)} tài khoản.")

    except Exception as e:
        print(f"\nĐÃ XẢY RA LỖI NGHIÊM TRỌNG: {e}")
        if "FOREIGN KEY constraint" in str(e):
            print("Lỗi Khóa Ngoại: Hãy đảm bảo bạn đã chạy script SQL để tạo NhanVien (NV001-NV005) trước.")

if __name__ == "__main__":
    seed_accounts()
    if conn:
        conn.close() # Đóng kết nối sau khi chạy