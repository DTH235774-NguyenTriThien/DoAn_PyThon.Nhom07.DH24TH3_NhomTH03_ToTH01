# app/utils.py
from datetime import datetime, date
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
