# app/utils/business_helpers.py
from tkinter import messagebox
from datetime import time
from app import db # Cần để truy cập db.cursor

# Import các hàm time helper mà chúng ta vừa tách ra
from app.utils.time_helpers import parse_time, _time_to_minutes


def validate_shift_time(start_time_str, end_time_str, exclude_maca=None, parent=None, allow_partial_overlap=False):
    """
    Kiểm tra giờ ca:
     - start_time_str, end_time_str: chuỗi hoặc dạng parseable bởi parse_time()
     - exclude_maca: nếu sửa ca, bỏ qua MaCa này khi kiểm tra
     - allow_partial_overlap: nếu True -> cho phép ghi chồng (partial) nhưng vẫn có thể chặn hoàn toàn trùng exact
       (mặc định False = KHÔNG cho phép bất kỳ overlap nào)
    Trả về True nếu hợp lệ (không conflict theo chính sách).
    """
    try:
        t_start = parse_time(start_time_str)
        t_end = parse_time(end_time_str)
    except Exception:
        t_start = None
        t_end = None

    if not t_start or not t_end:
        # thông báo lỗi format
        messagebox.showwarning("Sai định dạng giờ", "⚠️ Giờ phải có dạng HH:MM (ví dụ 07:30).", parent=parent)
        return False

    if t_end <= t_start:
        messagebox.showwarning("Giờ không hợp lệ", "⚠️ Giờ kết thúc phải lớn hơn giờ bắt đầu.", parent=parent)
        return False

    # chuyển sang phút để so sánh tiện
    s_min = _time_to_minutes(t_start)
    e_min = _time_to_minutes(t_end)

    # lấy tất cả ca hiện có
    try:
        # Sử dụng db.cursor toàn cục
        db.cursor.execute("SELECT MaCa, TenCa, GioBatDau, GioKetThuc FROM CaLam ORDER BY MaCa")
        rows = db.cursor.fetchall()
    except Exception as ex:
        messagebox.showerror("Lỗi kiểm tra giờ", f"Không thể truy vấn CaLam: {ex}", parent=parent)
        return False

    conflicts = []
    for r in rows:
        # bỏ qua ca đang sửa
        if exclude_maca and str(r.MaCa) == str(exclude_maca):
            continue

        # lấy giờ của ca hiện có, parse
        if getattr(r, "GioBatDau", None) is None or getattr(r, "GioKetThuc", None) is None:
            continue
        # nếu DB trả về datetime.time hoặc datetime, xử lý tương ứng
        try:
            # r.GioBatDau có thể là time hoặc str hoặc datetime
            if isinstance(r.GioBatDau, time):
                s2 = r.GioBatDau
            else:
                s2 = parse_time(str(r.GioBatDau))
            if isinstance(r.GioKetThuc, time):
                e2 = r.GioKetThuc
            else:
                e2 = parse_time(str(r.GioKetThuc))
        except Exception:
            continue

        if not s2 or not e2:
            continue

        s2_min = _time_to_minutes(s2)
        e2_min = _time_to_minutes(e2)

        # Kiểm tra overlap chuẩn:
        # two intervals [s,e) và [s2,e2) overlap nếu s < e2 and s2 < e
        overlap = (s_min < e2_min) and (s2_min < e_min)

        if overlap:
            if allow_partial_overlap:
                # nếu cho phép partial overlap, có thể vẫn chặn exact duplicates (tùy policy)
                # ở đây ta sẽ cho phép partial overlap, nhưng chặn nếu **exact same interval**
                if not (s_min == s2_min and e_min == e2_min):
                    # cho phép partial, skip adding to conflicts
                    continue
                else:
                    conflicts.append(r)
            else:
                conflicts.append(r)

    if conflicts:
        # build message
        conflict_list = ", ".join(
            f"{c.TenCa} ({(c.GioBatDau.strftime('%H:%M') if getattr(c,'GioBatDau',None) else '')}–{(c.GioKetThuc.strftime('%H:%M') if getattr(c,'GioKetThuc',None) else '')})"
            for c in conflicts
        )
        messagebox.showwarning("Trùng giờ", f"⚠️ Giờ ca bị trùng với các ca: {conflict_list}", parent=parent)
        return False

    return True


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