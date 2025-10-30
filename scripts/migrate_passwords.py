# scripts/migrate_passwords.py
import bcrypt
import sys
import os

# Thêm thư mục gốc vào system path để import app.db
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.db import fetch_query, execute_query
except ImportError:
    print("LỖI: Không thể import 'app.db'.")
    print("Hãy đảm bảo bạn chạy script này từ thư mục gốc (Doan_Python), không phải từ 'scripts/'")
    sys.exit(1)

def migrate():
    """
    Nâng cấp tất cả mật khẩu trong bảng TaiKhoan sang Bcrypt.
    Mật khẩu mặc định cho tất cả sẽ là '123'.
    """

    PASSWORD_TO_SET = '123'
    print(f"Bắt đầu nâng cấp mật khẩu sang Bcrypt (Mật khẩu mới: '{PASSWORD_TO_SET}')...")

    try:
        # 1. Lấy tất cả user
        users = fetch_query("SELECT TenDangNhap FROM TaiKhoan")
        if not users:
            print("Không tìm thấy tài khoản nào trong CSDL.")
            return

        print(f"Tìm thấy {len(users)} tài khoản. Đang xử lý...")

        # 2. Chuyển đổi mật khẩu
        pw_bytes = PASSWORD_TO_SET.encode('utf-8')

        count_success = 0
        for user in users:
            username = user["TenDangNhap"]

            # 3. Tạo hash Bcrypt mới (đã bao gồm salt)
            salt = bcrypt.gensalt()
            hashed_pw = bcrypt.hashpw(pw_bytes, salt)
            hashed_string = hashed_pw.decode('utf-8')

            # 4. Cập nhật vào CSDL
            query = "UPDATE TaiKhoan SET MatKhauHash = ? WHERE TenDangNhap = ?"
            if execute_query(query, (hashed_string, username)):
                print(f"  [THÀNH CÔNG] Đã nâng cấp tài khoản: {username}")
                count_success += 1
            else:
                print(f"  [THẤT BẠI] Không thể nâng cấp: {username}")

        print(f"\nHoàn tất! Đã nâng cấp thành công {count_success}/{len(users)} tài khoản.")
        print("Bạn có thể đăng nhập bằng mật khẩu '123' ngay bây giờ.")

    except Exception as e:
        print(f"\nĐÃ XẢY RA LỖI NGHIÊM TRỌNG: {e}")
        print("Quá trình nâng cấp có thể đã thất bại. Vui lòng kiểm tra CSDL.")

if __name__ == "__main__":
    migrate()