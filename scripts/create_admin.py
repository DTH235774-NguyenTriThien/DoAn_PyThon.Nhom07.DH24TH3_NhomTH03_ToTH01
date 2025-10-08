# scripts/create_admin.py
import getpass
import bcrypt
from app import db

def create_admin(username, password, ma_nv=None, role='admin'):
    pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    # INSERT, nếu TenDangNhap đã tồn tại thì UPDATE
    existing = db.fetch_one("SELECT TenDangNhap FROM TaiKhoan WHERE TenDangNhap = ?", (username,))
    if existing:
        print("Tài khoản đã tồn tại. Cập nhật mật khẩu.")
        db.execute("UPDATE TaiKhoan SET MatKhauHash = ? , Role = ?, MaNV = ? WHERE TenDangNhap = ?", (pw_hash, role, ma_nv, username))
    else:
        db.execute("INSERT INTO TaiKhoan (TenDangNhap, MatKhauHash, Role, MaNV) VALUES (?, ?, ?, ?)", (username, pw_hash, role, ma_nv))
    print("Ok. Tạo/Cập nhật tài khoản thành công.")

if __name__ == "__main__":
    user = input("Tên đăng nhập (ví dụ admin): ").strip()
    pwd = getpass.getpass("Mật khẩu: ")
    ma_nv = input("Mã nhân viên (optional): ").strip() or None
    create_admin(user, pwd, ma_nv)