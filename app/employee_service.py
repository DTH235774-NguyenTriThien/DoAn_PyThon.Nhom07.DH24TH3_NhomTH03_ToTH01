from db import cursor, conn, fetch_all

# --------------------------
#  Thêm nhân viên mới
# --------------------------
def add_employee(ma_nv, ho_ten, gioi_tinh, ngay_sinh, chuc_vu, luong, trang_thai):
    try:
        query = """
            INSERT INTO NhanVien (MaNV, HoTen, GioiTinh, NgaySinh, ChucVu, LuongCoBan, TrangThai)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (ma_nv, ho_ten, gioi_tinh, ngay_sinh, chuc_vu, luong, trang_thai))
        conn.commit()
        print(f"✅ Đã thêm nhân viên '{ho_ten}' thành công!")
    except Exception as e:
        print("❌ Lỗi khi thêm nhân viên:", e)

# --------------------------
#  Cập nhật thông tin nhân viên
# --------------------------
def update_employee(ma_nv, ho_ten=None, gioi_tinh=None, ngay_sinh=None, chuc_vu=None, luong=None, trang_thai=None):
    try:
        query = "UPDATE NhanVien SET "
        params = []

        if ho_ten:
            query += "HoTen = ?, "
            params.append(ho_ten)
        if gioi_tinh:
            query += "GioiTinh = ?, "
            params.append(gioi_tinh)
        if ngay_sinh:
            query += "NgaySinh = ?, "
            params.append(ngay_sinh)
        if chuc_vu:
            query += "ChucVu = ?, "
            params.append(chuc_vu)
        if luong:
            query += "LuongCoBan = ?, "
            params.append(luong)
        if trang_thai:
            query += "TrangThai = ?, "
            params.append(trang_thai)

        query = query.rstrip(", ") + " WHERE MaNV = ?"
        params.append(ma_nv)

        cursor.execute(query, tuple(params))
        conn.commit()
        print(f"✏️ Đã cập nhật thông tin nhân viên '{ma_nv}' thành công!")
    except Exception as e:
        print("❌ Lỗi khi cập nhật nhân viên:", e)

# --------------------------
#  Xóa nhân viên
# --------------------------
def delete_employee(ma_nv):
    try:
        cursor.execute("DELETE FROM NhanVien WHERE MaNV = ?", (ma_nv,))
        conn.commit()
        print(f"🗑️ Đã xóa nhân viên có mã '{ma_nv}'")
    except Exception as e:
        print("❌ Lỗi khi xóa nhân viên:", e)

# --------------------------
#  Xem danh sách nhân viên
# --------------------------
def list_employees():
    fetch_all("NhanVien")
