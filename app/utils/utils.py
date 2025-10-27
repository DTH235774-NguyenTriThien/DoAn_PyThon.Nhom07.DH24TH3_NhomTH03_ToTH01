# app/utils.py
from datetime import datetime, date, time
from tkinter import messagebox
from tkinter import ttk
from app import db
import tkinter as tk
"""
Hàm tiện ích dùng chung trong app.
"""

def clear_window(root):
    """Xóa mọi widget con của root (dọn màn hình để hiển thị frame mới)."""
    for widget in root.winfo_children():
        widget.destroy()

# Định dạng datetime để lưu vào db
def _time_to_minutes(t):
    """Chuyển datetime.time -> phút từ 00:00"""
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
    

def validate_shift_time(start_time_str, end_time_str, exclude_maca=None, parent=None, allow_partial_overlap=False):
    """
    Kiểm tra giờ ca:
     - start_time_str, end_time_str: chuỗi hoặc dạng parseable bởi parse_time()
     - exclude_maca: nếu sửa ca, bỏ qua MaCa này khi kiểm tra
     - allow_partial_overlap: nếu True -> cho phép ghi chồng (partial) nhưng vẫn có thể chặn hoàn toàn trùng exact
       (mặc định False = KHÔNG cho phép bất kỳ overlap nào)
    Trả về True nếu hợp lệ (không conflict theo chính sách).
    """
    from app.utils.utils import parse_time  # bảo đảm dùng parse_time cùng file
    try:
        t_start = parse_time(start_time_str)
        t_end = parse_time(end_time_str)
    except Exception:
        t_start = None
        t_end = None

    if not t_start or not t_end:
        # thông báo lỗi format
        from tkinter import messagebox
        messagebox.showwarning("Sai định dạng giờ", "⚠️ Giờ phải có dạng HH:MM (ví dụ 07:30).", parent=parent)
        return False

    if t_end <= t_start:
        from tkinter import messagebox
        messagebox.showwarning("Giờ không hợp lệ", "⚠️ Giờ kết thúc phải lớn hơn giờ bắt đầu.", parent=parent)
        return False

    # chuyển sang phút để so sánh tiện
    s_min = _time_to_minutes(t_start)
    e_min = _time_to_minutes(t_end)

    # lấy tất cả ca hiện có
    try:
        db.cursor.execute("SELECT MaCa, TenCa, GioBatDau, GioKetThuc FROM CaLam ORDER BY MaCa")
        rows = db.cursor.fetchall()
    except Exception as ex:
        from tkinter import messagebox
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
        from tkinter import messagebox
        messagebox.showwarning("Trùng giờ", f"⚠️ Giờ ca bị trùng với các ca: {conflict_list}", parent=parent)
        return False

    return True
# HELPER GENERATE primary key

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

def generate_next_macc(cursor):
    """
    Sinh mã chấm công (MaCham) mới — tự động tìm khoảng trống nhỏ nhất.
    Nếu bảng rỗng, bắt đầu từ 1.
    Ví dụ: [1,2,4] -> trả về 3.
    """
    try:
        cursor.execute("SELECT MaCham FROM ChamCong ORDER BY MaCham ASC")
        rows = cursor.fetchall()
        if not rows:
            return 1

        # Lấy tất cả mã hiện có (chuyển sang int)
        existing = [r.MaCham for r in rows if r.MaCham is not None]

        # Tìm khoảng trống nhỏ nhất
        expected = 1
        for val in existing:
            if val != expected:
                break
            expected += 1
        return expected
    except Exception as e:
        print("[generate_next_macc] Lỗi:", e)
        return 1

def generate_next_maca(cursor):
    """
    Sinh mã ca (MaCa) mới:
    - Bắt đầu từ 1.
    - Tự động tìm khoảng trống nhỏ nhất chưa dùng.
    - Hoạt động tốt dù đã xóa 1 vài ca giữa chừng.
    """
    try:
        cursor.execute("SELECT MaCa FROM CaLam ORDER BY MaCa ASC")
        rows = cursor.fetchall()

        if not rows:
            return 1  # nếu bảng rỗng → bắt đầu từ 1

        existing_ids = [r.MaCa for r in rows if r.MaCa is not None]
        expected = 1
        for value in existing_ids:
            if value != expected:
                # nếu phát hiện khoảng trống
                return expected
            expected += 1

        # nếu không có khoảng trống thì tăng tiếp
        return expected
    except Exception as e:
        print(f"[generate_next_maca] Lỗi: {e}")
        return 1


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

def create_form_window(title, size="430x500", bg="#f8f9fa"):
    """
    Tạo cửa sổ form chuẩn (popup) dùng cho các module Add/Edit.
    Trả về tuple (win, form, entries)
    """
    win = tk.Toplevel()
    win.title(title)
    win.geometry(size)
    win.resizable(False, False)
    win.configure(bg=bg)

    form = tk.Frame(win, bg=bg)
    form.pack(padx=20, pady=15, fill="both", expand=True)

    return win, form

def go_back(root, username=None, role=None):
    """
    Quay lại menu chính — dùng chung cho mọi module.
    """
    from app.ui.mainmenu_frame import show_main_menu
    show_main_menu(root, username, role)

def center_window(win, width, height, offset_y=-30):
    """Canh giữa màn hình cho một cửa sổ Tkinter"""
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2) + offset_y)
    win.geometry(f"{width}x{height}+{x}+{y}")