# app/utils.py
from datetime import datetime, date
from tkinter import messagebox
"""
Hàm tiện ích dùng chung trong app.
"""

def clear_window(root):
    """Xóa mọi widget con của root (dọn màn hình để hiển thị frame mới)."""
    for widget in root.winfo_children():
        widget.destroy()

# Định dạng datetime để lưu vào db

def parse_date(s):
    """
    Chấp nhận nhiều định dạng ngày đầu vào và trả datetime.date hoặc None.
    Các định dạng hỗ trợ: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, YYYY/MM/DD
    """
    if not s:
        return None
    s = s.strip()
    formats = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d")
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            continue
    # nếu không parse được, cố thử chỉ lấy phần ngày nếu chứa space/time
    try:
        # fallback: try parse ISO
        return datetime.fromisoformat(s).date()
    except Exception:
        return None

def format_for_display(d):
    """Định dạng date object để hiển thị trong Treeview: DD/MM/YYYY"""
    if not d:
        return ""
    if isinstance(d, str):
        d = parse_date(d)
        if not d:
            return ""
    return d.strftime("%d/%m/%Y")

def format_for_input(d):
    """Định dạng date object để prefill input (YYYY-MM-DD) — dễ sửa bằng keyboard"""
    if not d:
        return ""
    if isinstance(d, str):
        d = parse_date(d)
        if not d:
            return ""
    return d.strftime("%Y-%m-%d")
def normalize_date_input(val):

    if val is None:
        return None

    # Nếu đã là date (không phải datetime)
    if isinstance(val, date) and not isinstance(val, datetime):
        return val

    # Nếu là datetime
    if isinstance(val, datetime):
        return val.date()

    # Nếu là chuỗi
    if isinstance(val, str):
        s = val.strip()
        if s == "":
            return None
        # thử các định dạng phổ biến
        fmts = ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y.%m.%d")
        for fmt in fmts:
            try:
                return datetime.strptime(s, fmt).date()
            except Exception:
                continue
        # fallback: nếu chuỗi có time phần (iso), thử fromisoformat
        try:
            return datetime.fromisoformat(s).date()
        except Exception:
            pass

        raise ValueError(f"Không nhận diện được định dạng ngày: '{val}'")

    # nếu loại không được hỗ trợ
    raise ValueError(f"Kiểu dữ liệu ngày không hợp lệ: {type(val)}")

def generate_next_manv(cursor):
    """
    Tạo mã nhân viên tiếp theo (NV00x) dựa trên dữ liệu hiện có trong DB.
    Trả về mã nhỏ nhất chưa được dùng.
    """
    cursor.execute("SELECT MaNV FROM NhanVien")
    rows = [r.MaNV.strip().upper() for r in cursor.fetchall() if r.MaNV]

    # Lọc các mã hợp lệ NVxxx
    numbers = []
    for code in rows:
        if code.startswith("NV"):
            try:
                num = int(code[2:])
                numbers.append(num)
            except ValueError:
                pass

    next_num = 1
    while next_num in numbers:
        next_num += 1

    return f"NV{next_num:03d}"


def generate_next_masp(cursor):
    """
    Sinh mã MaSP dạng SP001, SP002... dựa trên MaSP hiện có trong bảng SANPHAM.
    """
    cursor.execute("SELECT MaSP FROM SANPHAM")
    rows = [r.MaSP.strip().upper() for r in cursor.fetchall() if r.MaSP]
    nums = []
    for code in rows:
        if code.startswith("SP"):
            try:
                nums.append(int(code[2:]))
            except Exception:
                pass
    next_num = 1
    while next_num in nums:
        next_num += 1
    return f"SP{next_num:03d}"

def generate_next_mahd(cursor):
    """
    Sinh mã MaHD dạng HD0001, HD0002... dựa trên MaHD hiện có trong bảng HoaDon.
    """
    cursor.execute("SELECT MaHD FROM HoaDon")
    rows = [r.MaHD.strip().upper() for r in cursor.fetchall() if r.MaHD]
    nums = []
    for code in rows:
        if code.startswith("HD"):
            try:
                nums.append(int(code[2:]))
            except Exception:
                pass
    next_num = 1
    while next_num in nums:
        next_num += 1
    return f"HD{next_num:04d}"

def generate_next_makh(cursor):
    """
    Sinh mã MaKH dạng KH001, KH002...
    """
    cursor.execute("SELECT MaKH FROM KhachHang")
    rows = [r.MaKH.strip().upper() for r in cursor.fetchall() if r.MaKH]
    nums = []
    for code in rows:
        if code.startswith("KH"):
            try:
                nums.append(int(code[2:]))
            except Exception:
                pass
    next_num = 1
    while next_num in nums:
        next_num += 1
    return f"KH{next_num:03d}"



def safe_delete(table_name, key_column, key_value, cursor, conn, refresh_func=None, item_label="mục"):
    """
    Hàm xóa dữ liệu an toàn, có xử lý lỗi khóa ngoại.
    - table_name: tên bảng trong DB (VD: 'NhanVien', 'SanPham')
    - key_column: tên cột khóa chính (VD: 'MaNV', 'MaSP')
    - key_value: giá trị cần xóa (VD: 'NV001')
    - cursor, conn: kết nối DB
    - refresh_func: hàm làm mới TreeView (nếu có)
    - item_label: mô tả ngắn gọn (VD: 'nhân viên', 'sản phẩm')
    """

    if not key_value:
        messagebox.showwarning("⚠️ Thiếu thông tin", "Không xác định được đối tượng cần xóa!")
        return

    if not messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc muốn xóa {item_label} {key_value}?"):
        return

    try:
        cursor.execute(f"DELETE FROM {table_name} WHERE {key_column}=?", (key_value,))
        conn.commit()

        if refresh_func:
            refresh_func()

        messagebox.showinfo("✅ Thành công", f"Đã xóa {item_label} {key_value} khỏi {table_name}.")

    except Exception as e:
        conn.rollback()
        err = str(e).lower()

        if "foreign key constraint" in err or "reference constraint" in err or "fk_" in err:
            messagebox.showwarning(
                "Không thể xóa",
                f"⚠️ {item_label.capitalize()} {key_value} đang được sử dụng trong bảng khác.\n"
                f"Vui lòng xóa các dữ liệu liên quan trước khi thực hiện xóa."
            )
        else:
            messagebox.showerror("Lỗi", f"Không thể xóa {item_label}: {e}")

def recalc_invoice_total(cursor, conn, mahd):
    """
    Tính lại TongTien cho HoaDon.MaHD = mahd dựa trên ChiTietHoaDon.
    Trả về giá trị tổng (Decimal/float).
    """
    cursor.execute("""
        SELECT ISNULL(SUM(SoLuong * DonGia), 0) AS Tong
        FROM ChiTietHoaDon
        WHERE MaHD = ?
    """, (mahd,))
    row = cursor.fetchone()
    total = float(row.Tong) if row and getattr(row, 'Tong', None) is not None else 0.0
    cursor.execute("UPDATE HoaDon SET TongTien = ? WHERE MaHD = ?", (total, mahd))
    conn.commit()
    return total