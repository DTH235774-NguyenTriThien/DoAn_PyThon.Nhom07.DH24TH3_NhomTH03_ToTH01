# app/utils/time_helpers.py
from datetime import datetime, date, time

def _time_to_minutes(t):
    """Chuyển datetime.time -> số phút tính từ 00:00"""
    if t is None:
        return None
    return t.hour * 60 + t.minute

def parse_time(s):
    """
    Nhận chuỗi giờ (HH:MM hoặc HH:MM:SS) và trả về datetime.time hoặc None.
    """
    if not s:
        return None
    s = s.strip()
    fmts = ("%H:%M", "%H:%M:%S")
    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt).time()
        except ValueError:
            continue
    return None

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
    # Fallback: thử parse ISO
    try:
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
    """Định dạng date object để prefill input (YYYY-MM-DD)"""
    if not d:
        return ""
    if isinstance(d, str):
        d = parse_date(d)
        if not d:
            return ""
    return d.strftime("%Y-%m-%d")

def normalize_date_input(val):
    """
    Chuẩn hóa nhiều loại input (str, datetime, date) về datetime.date.
    """
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
        # Thử các định dạng phổ biến
        fmts = ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y.%m.%d")
        for fmt in fmts:
            try:
                return datetime.strptime(s, fmt).date()
            except Exception:
                continue
        # Fallback: nếu chuỗi có time (iso)
        try:
            return datetime.fromisoformat(s).date()
        except Exception:
            pass

        raise ValueError(f"Không nhận diện được định dạng ngày: '{val}'")

    raise ValueError(f"Kiểu dữ liệu ngày không hợp lệ: {type(val)}")

def format_time_for_display(dt):
    """Hiển thị giờ phút (HH:MM) cho Treeview."""
    if not dt:
        return ""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except Exception:
            return ""
    return dt.strftime("%H:%M")

def combine_date_time(date_obj, time_input):
    """
    Kết hợp date + time thành datetime.
    - time_input có thể là chuỗi ('HH:MM', 'HhMM', 'HH.MM') hoặc datetime.time.
    """
    if not date_obj or not time_input:
        return None
    try:
        # Nếu là datetime.time, gộp trực tiếp
        if isinstance(time_input, time):
            return datetime.combine(date_obj, time_input)

        # Nếu là chuỗi, parse thủ công
        s = str(time_input).strip().lower().replace("h", ":").replace(".", ":")
        parts = s.split(":")
        if len(parts) >= 2:
            h, m = map(int, parts[:2])
        elif len(parts) == 1:
            h, m = int(parts[0]), 0
        else:
            return None
        return datetime.combine(date_obj, time(h, m))
    except Exception:
        return None