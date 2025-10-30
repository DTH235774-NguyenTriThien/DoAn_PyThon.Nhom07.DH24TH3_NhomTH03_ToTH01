import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime, date
from app import db
from app.db import execute_query
from app.utils.utils import go_back
from app.utils.time_helpers import (
    format_for_display, parse_date, parse_time, 
    combine_date_time, normalize_date_input
)
from app.utils.id_helpers import generate_next_macc
from app.utils.business_helpers import safe_delete
from app.theme import setup_styles


def build_tab(parent, root=None, username=None, role=None):
    """Tab Chấm công — hiển thị, tìm kiếm và CRUD cơ bản"""
    setup_styles()
    parent.configure(bg="#f5e6ca")

    # ===== THANH CÔNG CỤ =====
    top_frame = tk.Frame(parent, bg="#f9fafb")
    top_frame.pack(fill="x", pady=10)

    search_var = tk.StringVar()
    tk.Label(top_frame, text="🔎 Tìm chấm công:", font=("Arial", 11),
             bg="#f9fafb").pack(side="left", padx=5)
    entry_search = ttk.Entry(top_frame, textvariable=search_var, width=40)
    entry_search.pack(side="left", padx=5)

    # ===== TREEVIEW =====
    columns = ["MaCham", "MaNV", "HoTen", "TenCa", "NgayLam", "ClockIn", "ClockOut", "GhiChu"]
    headers = {
        "MaCham": "Mã CC",
        "MaNV": "Mã NV",
        "HoTen": "Họ tên",
        "TenCa": "Ca làm",
        "NgayLam": "Ngày làm",
        "ClockIn": "Giờ vào",
        "ClockOut": "Giờ ra",
        "GhiChu": "Ghi chú"
    }

    tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)
    for col in columns:
        tree.heading(col, text=headers[col])
        tree.column(col, anchor="center", width=120 if col != "GhiChu" else 200)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    # ===== LOAD DATA =====
    def load_data(keyword=None):
        """Tải danh sách chấm công, có tìm kiếm và bao gồm MaCa thật."""
        for item in tree.get_children():
            tree.delete(item)

        query = """
            SELECT c.MaCham, c.MaNV, nv.HoTen, c.MaCa, cl.TenCa,
                c.NgayLam, c.ClockIn, c.ClockOut, c.GhiChu
            FROM ChamCong c
            LEFT JOIN NhanVien nv ON c.MaNV = nv.MaNV
            LEFT JOIN CaLam cl ON c.MaCa = cl.MaCa
        """
        params = ()

        if keyword:
            kw = f"%{keyword.strip()}%"
            query += """
                WHERE c.MaNV LIKE ? OR nv.HoTen LIKE ? OR cl.TenCa LIKE ?
            """
            params = (kw, kw, kw)

        try:
            db.cursor.execute(query, params)
            rows = db.cursor.fetchall()

            for row in rows:
                macham = row.MaCham
                manv = row.MaNV
                hoten = row.HoTen or ""
                maca = row.MaCa if row.MaCa else ""
                tenca = row.TenCa or ""
                calam_display = f"{maca} - {tenca}" if maca else tenca

                ngay_lam = format_for_display(row.NgayLam)
                clockin = row.ClockIn.strftime("%H:%M") if row.ClockIn else ""
                clockout = row.ClockOut.strftime("%H:%M") if row.ClockOut else ""
                ghichu = row.GhiChu or ""

                # ✅ Chèn vào tree: thêm MaCa vào value nhưng ẩn (nếu muốn)
                tree.insert(
                    "",
                    "end",
                    values=[macham, manv, hoten, calam_display, ngay_lam, clockin, clockout, ghichu],
                )

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải dữ liệu chấm công: {e}")

    load_data()

    # ===== NÚT CHỨC NĂNG =====
    ttk.Button(top_frame, text="🔄 Tải lại", style="Close.TButton",
               command=load_data).pack(side="left", padx=5)
    ttk.Button(top_frame, text="➕ Thêm", style="Add.TButton",
               command=lambda: add_attendance(load_data)).pack(side="left", padx=5)
    ttk.Button(top_frame, text="✏️ Sửa", style="Edit.TButton",
               command=lambda: edit_attendance(tree, load_data)).pack(side="left", padx=5)
    ttk.Button(top_frame, text="🗑 Xóa", style="Delete.TButton",
               command=lambda: delete_attendance(tree, load_data)).pack(side="left", padx=5)
    ttk.Button(top_frame, text="⬅ Quay lại", style="Close.TButton",
               command=lambda: go_back(root, username, role)).pack(side="right", padx=6)

    # ===== SỰ KIỆN TÌM KIẾM REALTIME =====
    def on_search_change(event=None):
        keyword = search_var.get().strip()
        load_data(keyword)
    entry_search.bind("<KeyRelease>", on_search_change)

    # ===== DOUBLE CLICK TO EDIT =====
    def on_double_click(_):
        sel = tree.selection()
        if sel:
            edit_attendance(tree, load_data)
    tree.bind("<Double-1>", on_double_click)


# ===================== CRUD (tạm thời khung) ===================== #

def add_attendance(refresh):
    """Thêm bản ghi chấm công — có combobox ca làm, giờ vào/ra tự động điền."""
    win = tk.Toplevel()
    win.title("➕ Thêm chấm công")
    win.geometry("500x420")
    win.configure(bg="#f8f9fa")

    form = tk.Frame(win, bg="#f8f9fa")
    form.pack(padx=20, pady=15, fill="both", expand=True)

    # === Mã nhân viên ===
    ttk.Label(form, text="Mã nhân viên:", background="#f8f9fa", font=("Arial", 11)).grid(row=0, column=0, sticky="w", pady=6)
    cb_nv = ttk.Combobox(form, font=("Arial", 11))
    cb_nv.grid(row=0, column=1, sticky="ew", padx=8, pady=6)

    # Nạp danh sách nhân viên
    db.cursor.execute("SELECT MaNV, HoTen FROM NhanVien WHERE TrangThai = N'Đang làm'")
    nv_list = [f"{row.MaNV.strip()} - {row.HoTen}" for row in db.cursor.fetchall()]
    cb_nv["values"] = nv_list

    # === Ca làm ===
    ttk.Label(form, text="Ca làm:", background="#f8f9fa", font=("Arial", 11)).grid(row=1, column=0, sticky="w", pady=6)
    cb_ca = ttk.Combobox(form, font=("Arial", 11))
    cb_ca.grid(row=1, column=1, sticky="ew", padx=8, pady=6)

    db.cursor.execute("SELECT MaCa, TenCa, GioBatDau, GioKetThuc FROM CaLam")
    shift_rows = db.cursor.fetchall()
    ca_map = {str(row.MaCa): (row.TenCa, row.GioBatDau, row.GioKetThuc) for row in shift_rows}
    cb_ca["values"] = [f"{row.MaCa} - {row.TenCa}" for row in shift_rows]

    # === Ngày làm ===
    ttk.Label(form, text="Ngày làm:", background="#f8f9fa", font=("Arial", 11)).grid(row=2, column=0, sticky="w", pady=6)
    cal_ngay = DateEntry(form, date_pattern="yyyy-mm-dd", font=("Arial", 11))
    cal_ngay.grid(row=2, column=1, padx=8, pady=6, sticky="ew")

    # === Giờ vào / Giờ ra ===
    ttk.Label(form, text="Giờ vào:", background="#f8f9fa", font=("Arial", 11)).grid(row=3, column=0, sticky="w", pady=6)
    ttk.Label(form, text="Giờ ra:", background="#f8f9fa", font=("Arial", 11)).grid(row=4, column=0, sticky="w", pady=6)

    time_options = [f"{h:02d}:00" for h in range(0, 24)]
    cb_giovao = ttk.Combobox(form, values=time_options, font=("Arial", 11))
    cb_giora = ttk.Combobox(form, values=time_options, font=("Arial", 11))
    cb_giovao.grid(row=3, column=1, padx=8, pady=6, sticky="ew")
    cb_giora.grid(row=4, column=1, padx=8, pady=6, sticky="ew")

    # === Auto-fill giờ khi chọn ca ===
    def auto_fill_shift(event=None):
        try:
            selected = cb_ca.get().split(" - ")[0].strip()
            if selected in ca_map:
                _, gio_bd, gio_kt = ca_map[selected]
                cb_giovao.set(gio_bd.strftime("%H:%M") if gio_bd else "")
                cb_giora.set(gio_kt.strftime("%H:%M") if gio_kt else "")
        except Exception as e:
            return

    cb_ca.bind("<<ComboboxSelected>>", auto_fill_shift)

    # === Ghi chú ===
    ttk.Label(form, text="Ghi chú:", background="#f8f9fa", font=("Arial", 11)).grid(row=5, column=0, sticky="w", pady=6)
    txt_note = ttk.Entry(form, font=("Arial", 11))
    txt_note.grid(row=5, column=1, padx=8, pady=6, sticky="ew")

    # === Nút lưu ===
    def submit():
        try:
            manv = cb_nv.get().split(" - ")[0].strip()
            maca = cb_ca.get().split(" - ")[0].strip()
            ngay_lam = cal_ngay.get_date()
            gio_vao = cb_giovao.get().strip()
            gio_ra = cb_giora.get().strip()
            ghichu = txt_note.get().strip() or None

            if not manv or not maca:
                messagebox.showwarning("Thiếu thông tin", "⚠️ Vui lòng chọn nhân viên và ca làm.", parent=win)
                return

            # Giờ hợp lệ
            if gio_ra and gio_vao:
                t_in = datetime.strptime(gio_vao, "%H:%M")
                t_out = datetime.strptime(gio_ra, "%H:%M")
                if t_out <= t_in:
                    messagebox.showwarning("Giờ không hợp lệ", "⚠️ Giờ ra phải lớn hơn giờ vào.", parent=win)
                    return

            clock_in = combine_date_time(ngay_lam, gio_vao)
            clock_out = combine_date_time(ngay_lam, gio_ra)

            # === GỌI HELPER SINH MÃ CHẤM CÔNG ===
            macham = generate_next_macc(db.cursor)

            # === GHI VÀO DB ===
            query = """
                INSERT INTO ChamCong (MaCham, MaNV, MaCa, NgayLam, ClockIn, ClockOut, GhiChu)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (macham, manv, maca, ngay_lam, clock_in, clock_out, ghichu)
            if execute_query(query, params):
                messagebox.showinfo("✅ Thành công", f"Đã thêm chấm công cho NV {manv}.", parent=win)
                win.destroy()
                refresh()

        except Exception as e:
            db.conn.rollback()
            messagebox.showerror("Lỗi", f"Không thể thêm chấm công: {e}", parent=win)

    ttk.Button(form, text="💾 Lưu chấm công", style="Add.TButton", command=submit).grid(row=6, column=0, columnspan=2, pady=10)
    form.grid_columnconfigure(1, weight=1)

def edit_attendance(tree, refresh):
    """Sửa bản ghi chấm công (đồng bộ cấu trúc với add_attendance)"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn bản ghi cần sửa!")
        return

    # --- Lấy dữ liệu hiện tại ---
    values = tree.item(selected[0])["values"]
    macham, manv, hoten, tenca, ngaylam, clockin, clockout, ghichu = values

    win = tk.Toplevel()
    win.title(f"✏️ Sửa chấm công #{macham}")
    win.geometry("460x480")
    win.configure(bg="#f8f9fa")

    form = tk.Frame(win, bg="#f8f9fa")
    form.pack(padx=20, pady=15, fill="both", expand=True)

    # === Mã chấm công / Nhân viên (readonly) ===
    ttk.Label(form, text=f"Mã chấm công: {macham}", font=("Arial", 11, "bold"), background="#f8f9fa").grid(row=0, column=0, columnspan=2, sticky="w", pady=4)
    ttk.Label(form, text=f"Nhân viên: {manv} - {hoten}", font=("Arial", 11), background="#f8f9fa").grid(row=1, column=0, columnspan=2, sticky="w", pady=4)

    # === Ca làm ===
    ttk.Label(form, text="Ca làm", font=("Arial", 11), background="#f8f9fa").grid(row=2, column=0, sticky="w", padx=8, pady=6)
    cb_calam = ttk.Combobox(form, font=("Arial", 11))
    try:
        db.cursor.execute("SELECT MaCa, TenCa FROM CaLam ORDER BY MaCa")
        calam_list = [f"{row.MaCa} - {row.TenCa}" for row in db.cursor.fetchall()]
        cb_calam["values"] = calam_list
    except Exception:
        cb_calam["values"] = []
    cb_calam.set(f"{tenca}")  # hiển thị tên ca hiện tại
    cb_calam.grid(row=2, column=1, padx=8, pady=6, sticky="ew")

    # === Ngày làm ===
    ttk.Label(form, text="Ngày làm", font=("Arial", 11), background="#f8f9fa").grid(row=3, column=0, sticky="w", padx=8, pady=6)
    cal_ngay = DateEntry(form, date_pattern="yyyy-mm-dd", font=("Arial", 11))
    try:
        cal_ngay.set_date(parse_date(ngaylam))
    except Exception:
        cal_ngay.set_date(datetime.now().date())
    cal_ngay.grid(row=3, column=1, padx=8, pady=6, sticky="ew")

    # === Giờ vào / ra ===
    ttk.Label(form, text="Giờ vào", font=("Arial", 11), background="#f8f9fa").grid(row=4, column=0, sticky="w", padx=8, pady=6)
    ent_in = ttk.Entry(form, font=("Arial", 11))
    ent_in.insert(0, str(clockin).strip() if clockin else "")
    ent_in.grid(row=4, column=1, padx=8, pady=6, sticky="ew")

    ttk.Label(form, text="Giờ ra", font=("Arial", 11), background="#f8f9fa").grid(row=5, column=0, sticky="w", padx=8, pady=6)
    ent_out = ttk.Entry(form, font=("Arial", 11))
    ent_out.insert(0, str(clockout).strip() if clockout else "")
    ent_out.grid(row=5, column=1, padx=8, pady=6, sticky="ew")

    # === Ghi chú ===
    ttk.Label(form, text="Ghi chú", font=("Arial", 11), background="#f8f9fa").grid(row=6, column=0, sticky="nw", padx=8, pady=6)
    txt_note = tk.Text(form, font=("Arial", 11), height=3, width=25)
    txt_note.insert("1.0", str(ghichu or ""))
    txt_note.grid(row=6, column=1, padx=8, pady=6, sticky="ew")

    form.grid_columnconfigure(1, weight=1)

    # === Hàm Lưu thay đổi ===
    def save():
        try:
            maca_str = cb_calam.get().strip().split(" - ")[0]
            maca = int(maca_str) if maca_str.isdigit() else None
            ngay_lam = normalize_date_input(cal_ngay.get_date())

            giovao = ent_in.get().strip()
            giora = ent_out.get().strip()
            ghichu_new = txt_note.get("1.0", "end").strip() or None

            # --- kiểm tra dữ liệu ---
            if not maca:
                messagebox.showwarning("Thiếu thông tin", "⚠️ Vui lòng chọn ca làm hợp lệ.", parent=win)
                return

            if giovao and giora:
                start_dt = combine_date_time(ngay_lam, giovao)
                end_dt = combine_date_time(ngay_lam, giora)
                if not start_dt or not end_dt:
                    messagebox.showwarning("Định dạng sai", "⚠️ Giờ vào / giờ ra phải có dạng HH:MM.", parent=win)
                    return
                if end_dt <= start_dt:
                    messagebox.showwarning("Giờ không hợp lệ", "⚠️ Giờ ra phải lớn hơn giờ vào.", parent=win)
                    return
            else:
                start_dt, end_dt = None, None

            # --- cập nhật DB ---
            query = """
                UPDATE ChamCong
                SET MaCa=?, NgayLam=?, ClockIn=?, ClockOut=?, GhiChu=?
                WHERE MaCham=?
            """
            params = (maca, ngay_lam, start_dt, end_dt, ghichu_new, macham)

            if execute_query(query , params):
                messagebox.showinfo("✅ Thành công", f"Đã cập nhật chấm công #{macham}.", parent=win)
                refresh()
                win.destroy()

        except Exception as e:
            db.conn.rollback()
            messagebox.showerror("Lỗi", f"Không thể cập nhật chấm công: {e}", parent=win)

    ttk.Button(form, text="💾 Lưu thay đổi", style="Add.TButton", command=save).grid(row=8, column=0, columnspan=2, pady=15)

def delete_attendance(tree, refresh):
    """Xóa bản ghi chấm công (sử dụng helper safe_delete)"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn bản ghi cần xóa!")
        return

    values = tree.item(selected[0])["values"]
    macham = values[0]  # cột đầu tiên luôn là MaCham

    try:
        safe_delete(
            table_name="ChamCong",
            key_column="MaCham",
            key_value=macham,
            cursor=db.cursor,
            conn=db.conn,
            refresh_func=refresh,
            item_label="chấm công"
        )
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể xóa chấm công: {e}")
