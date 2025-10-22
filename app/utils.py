# app/utils.py
"""
Hàm tiện ích dùng chung trong app.
"""

def clear_window(root):
    """Xóa mọi widget con của root (dọn màn hình để hiển thị frame mới)."""
    for widget in root.winfo_children():
        widget.destroy()

from datetime import datetime, date

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