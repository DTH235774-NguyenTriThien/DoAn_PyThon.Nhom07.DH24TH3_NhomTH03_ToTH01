# app/utils/business_helpers.py
from tkinter import messagebox
from datetime import time
from app import db 
from app.db import execute_query, fetch_query
from decimal import Decimal

# Import các hàm time helper
from app.utils.time_helpers import parse_time, _time_to_minutes


def validate_shift_time(start_time_str, end_time_str, exclude_maca=None, parent=None, allow_partial_overlap=False):
    """
    Kiểm tra xem giờ ca mới có bị trùng (overlap) với các ca đã tồn tại không.
    Trả về True nếu hợp lệ.
    """
    try:
        t_start = parse_time(start_time_str)
        t_end = parse_time(end_time_str)
    except Exception:
        t_start, t_end = None, None

    if not t_start or not t_end:
        messagebox.showwarning("Sai định dạng giờ", "⚠️ Giờ phải có dạng HH:MM (ví dụ 07:30).", parent=parent)
        return False

    if t_end <= t_start:
        messagebox.showwarning("Giờ không hợp lệ", "⚠️ Giờ kết thúc phải lớn hơn giờ bắt đầu.", parent=parent)
        return False

    s_min = _time_to_minutes(t_start)
    e_min = _time_to_minutes(t_end)

    try:
        db.cursor.execute("SELECT MaCa, TenCa, GioBatDau, GioKetThuc FROM CaLam ORDER BY MaCa")
        rows = db.cursor.fetchall()
    except Exception as ex:
        messagebox.showerror("Lỗi kiểm tra giờ", f"Không thể truy vấn CaLam: {ex}", parent=parent)
        return False

    conflicts = []
    for r in rows:
        if exclude_maca and str(r.MaCa) == str(exclude_maca):
            continue

        if getattr(r, "GioBatDau", None) is None or getattr(r, "GioKetThuc", None) is None:
            continue
            
        try:
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

        overlap = (s_min < e2_min) and (s2_min < e_min)

        if overlap:
            if allow_partial_overlap:
                if not (s_min == s2_min and e_min == e2_min):
                    continue
                else:
                    conflicts.append(r)
            else:
                conflicts.append(r)

    if conflicts:
        conflict_list = ", ".join(
            f"{c.TenCa} ({(c.GioBatDau.strftime('%H:%M') if getattr(c,'GioBatDau',None) else '')}–{(c.GioKetThuc.strftime('%H:%M') if getattr(c,'GioKetThuc',None) else '')})"
            for c in conflicts
        )
        messagebox.showwarning("Trùng giờ", f"⚠️ Giờ ca bị trùng với các ca: {conflict_list}", parent=parent)
        return False

    return True


def safe_delete(table_name, key_column, key_value, cursor, conn, refresh_func=None, item_label="mục"):
    """
    Hàm xóa dữ liệu an toàn, có xử lý lỗi khóa ngoại (FOREIGN KEY).
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
    Trả về giá trị tổng (float).
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

def deduct_inventory_from_recipe(mahd):
    """
    Tự động trừ kho nguyên liệu dựa trên công thức của các món đã bán
    trong một hóa đơn.
    """
    try:
        items_sold = fetch_query(
            "SELECT MaSP, SoLuong FROM ChiTietHoaDon WHERE MaHD = ?",
            (mahd,)
        )
        
        if not items_sold:
            return True 

        total_deductions = {}

        for item in items_sold:
            masp = item['MaSP']
            quantity_sold = int(item['SoLuong'])
            
            recipe = fetch_query(
                "SELECT MaNL, SoLuong FROM CongThuc WHERE MaSP = ?",
                (masp,)
            )
            
            if not recipe:
                continue 

            for ingredient in recipe:
                manl = ingredient['MaNL']
                try:
                    qty_needed_per_item = Decimal(ingredient['SoLuong'])
                    total_to_deduct = qty_needed_per_item * quantity_sold
                except Exception:
                    continue 

                if manl in total_deductions:
                    total_deductions[manl] += total_to_deduct
                else:
                    total_deductions[manl] = total_to_deduct

        if not total_deductions:
             return True
             
        for manl, total_to_deduct in total_deductions.items():
            query_update = """
                UPDATE NguyenLieu 
                SET SoLuongTon = SoLuongTon - ? 
                WHERE MaNL = ?
            """
            if not execute_query(query_update, (float(total_to_deduct), manl)):
                # Ghi lại lỗi một cách thầm lặng nếu 1 NL bị lỗi,
                # nhưng vẫn tiếp tục trừ các NL khác.
                pass
        
        return True

    except Exception as e:
        messagebox.showerror("Lỗi Trừ Kho Nghiêm trọng", 
                             f"Đã xảy ra lỗi khi tự động trừ kho cho HD {mahd}:\n{e}")
        return False