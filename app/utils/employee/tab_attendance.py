# app/utils/employee/tab_attendance.py
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from app import db
from app.theme import setup_styles
from datetime import datetime

# Import helpers
from app.db import fetch_query, execute_query
from app.utils.business_helpers import safe_delete
from app.utils.time_helpers import (
    format_for_display, parse_date, parse_time, 
    combine_date_time, normalize_date_input
)
from app.utils.id_helpers import generate_next_macc
from app.utils.treeview_helpers import fill_treeview_chunked

# SỬA 1: Thay đổi tham số hàm
# (Các import giữ nguyên)
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
from app import db
from app.theme import setup_styles
from app.db import fetch_query, execute_query, execute_scalar
from app.utils.treeview_helpers import fill_treeview_chunked
# (Các hàm CRUD: add_attendance, edit_attendance, delete_attendance 
#  được giả định là ở cuối file và không thay đổi)


def build_tab(parent, on_back_callback=None):
    """Tab Chấm công — Đồng bộ layout giống tab_shift"""
    setup_styles()
    parent.configure(bg="#f5e6ca")

    # ===== SỬA 1: TÁI CẤU TRÚC TOP_FRAME (DÙNG GRID) =====
    top_frame = tk.Frame(parent, bg="#f9fafb")
    top_frame.pack(fill="x", pady=10, padx=10) 
    
    # Cấu hình Cột 0 (filter) co giãn, Cột 1 (button) cố định
    top_frame.grid_columnconfigure(0, weight=1) 

    # --- Frame NÚT CHỨC NĂNG (Bên phải - Cột 1) ---
    btn_frame = tk.Frame(top_frame, bg="#f9fafb")
    # Xóa .pack(), dùng .grid()
    btn_frame.grid(row=0, column=1, sticky="ne", padx=(10, 0)) 
    
    # --- Frame LỌC (Bên trái, tự mở rộng - Cột 0) ---
    filter_frame = tk.Frame(top_frame, bg="#f9fafb")
    # Xóa .pack(), dùng .grid()
    filter_frame.grid(row=0, column=0, sticky="nsew") 

    # ===== SỬA 2: TÁI CẤU TRÚC FILTER_FRAME (DÙNG GRID) =====
    
    # --- Hàng 0: Các bộ lọc ---
    tk.Label(filter_frame, text="📅 Lọc theo ngày:", font=("Arial", 11),
             bg="#f9fafb").grid(row=0, column=0, padx=(5, 2), pady=5, sticky="w")
    
    cal_filter = DateEntry(filter_frame, date_pattern="dd/mm/yyyy", font=("Arial", 11),
                           background="#3e2723", foreground="white", borderwidth=2,
                           width=12) 
    cal_filter.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    cal_filter.set_date(datetime.now()) 

    tk.Label(filter_frame, text="🔎 Tìm nhân viên:", font=("Arial", 11),
             bg="#f9fafb").grid(row=0, column=2, padx=(10, 2), pady=5, sticky="w")
    
    entry_search = ttk.Entry(filter_frame, width=30) 
    entry_search.grid(row=0, column=3, padx=5, pady=5, sticky="ew") 
    
    # Cấu hình cột tìm kiếm (cột 3) co giãn
    filter_frame.grid_columnconfigure(3, weight=1) 

    # --- Hàng 1: Nhãn Trạng thái ---
    status_label_var = tk.StringVar(value="")
    status_label = ttk.Label(filter_frame, textvariable=status_label_var, 
                             font=("Arial", 10, "italic"), background="#f9fafb", 
                             foreground="blue")
    # Đặt ở Hàng 1, kéo dài 4 cột
    status_label.grid(row=1, column=0, columnspan=4, padx=5, pady=(0, 5), sticky="w")


    # ===== SỬA 3: TÁI CẤU TRÚC BTN_FRAME (DÙNG GRID) =====
    # (Giúp các nút không bị xô lệch khi resize)
    
    ttk.Button(btn_frame, text="🔄 Tải lại", style="Close.TButton",
               command=lambda: refresh_data()).grid(row=0, column=0, padx=5)
    
    ttk.Button(btn_frame, text="➕ Chấm công", style="Add.TButton",
               command=lambda: add_attendance(refresh_data, cal_filter.get_date())).grid(row=0, column=1, padx=5)
    
    ttk.Button(btn_frame, text="✏️ Sửa", style="Edit.TButton",
               command=lambda: edit_attendance(tree, refresh_data)).grid(row=0, column=2, padx=5)
    
    ttk.Button(btn_frame, text="🗑 Xóa", style="Delete.TButton",
               command=lambda: delete_attendance(tree, refresh_data)).grid(row=0, column=3, padx=5)
    
    if on_back_callback:
        ttk.Button(btn_frame, text="⬅ Quay lại", style="Close.TButton", # Đã sửa tên nút cho ngắn gọn
                   command=on_back_callback).grid(row=0, column=4, padx=5)


    # ===== TREEVIEW (Không thay đổi) =====
    tree_frame = tk.Frame(parent, bg="#f5e6ca")
    tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    columns = ["MaCham", "MaNV", "HoTen", "NgayLam", "TenCa", "ClockIn", "ClockOut", "GhiChu"]
    headers = {
        "MaCham": "Mã Chấm", "MaNV": "Mã NV", "HoTen": "Họ Tên",
        "NgayLam": "Ngày Làm", "TenCa": "Ca Làm", "ClockIn": "Giờ Vào",
        "ClockOut": "Giờ Ra", "GhiChu": "Ghi Chú"
    }

    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
    for col, text in headers.items():
        tree.heading(col, text=text)
        tree.column(col, anchor="center", width=120)
    
    tree.column("MaCham", width=80); tree.column("MaNV", width=80)
    tree.column("HoTen", width=150); tree.column("TenCa", width=100)
    tree.column("ClockIn", width=80); tree.column("ClockOut", width=80)
    tree.column("GhiChu", width=200, anchor="center") 
    tree.pack(fill="both", expand=True)

    # ===== HÀM LOAD DATA (Không thay đổi) =====
    def load_data(tree_widget, status_var, filter_date, filter_keyword):
        status_var.set("Đang tải dữ liệu...")
        tree_widget.update_idletasks() 
        query = """
            SELECT 
                cc.MaCham, cc.MaNV, nv.HoTen, cc.NgayLam, 
                cl.TenCa, cc.ClockIn, cc.ClockOut, cc.GhiChu
            FROM ChamCong cc
            LEFT JOIN NhanVien nv ON cc.MaNV = nv.MaNV
            LEFT JOIN CaLam cl ON cc.MaCa = cl.MaCa
            WHERE 1=1
        """
        params = []
        try:
            date_obj = cal_filter.get_date()
            query += " AND cc.NgayLam = ? "
            params.append(date_obj)
        except Exception: pass 
        
        if filter_keyword:
            kw = f"%{filter_keyword.strip()}%"
            query += " AND (cc.MaNV LIKE ? OR nv.HoTen LIKE ?) "
            params.extend([kw, kw])
        query += " ORDER BY cc.NgayLam DESC, cc.ClockIn DESC"

        try:
            rows = db.fetch_query(query, tuple(params))
            tree_data = []
            for row in rows:
                macham = row["MaCham"]; manv = row["MaNV"]; hoten = row["HoTen"] or ""
                ngaylam_obj = row["NgayLam"]; ngaylam = ngaylam_obj.strftime("%d/%m/%Y") if ngaylam_obj else ""
                tenca = row["TenCa"] or "N/A"
                clockin_obj = row["ClockIn"]; clockin = clockin_obj.strftime("%H:%M") if clockin_obj else "--:--"
                clockout_obj = row["ClockOut"]; clockout = clockout_obj.strftime("%H:%M") if clockout_obj else "--:--"
                ghichu = row["GhiChu"] or ""
                values_tuple = (macham, manv, hoten, ngaylam, tenca, clockin, clockout, ghichu)
                tree_data.append({"iid": macham, "values": values_tuple})

            def on_load_complete():
                status_var.set(f"Đã tải {len(rows)} bản ghi.")
            fill_treeview_chunked(
                tree=tree_widget, rows=tree_data, batch=100,
                on_complete=on_load_complete
            )
        except Exception as e:
            status_var.set("Lỗi tải dữ liệu!")
            messagebox.showerror("Lỗi", f"Không thể tải dữ liệu chấm công: {e}")

    # ===== CÁC HÀM TIỆN ÍCH (Không thay đổi) =====
    def refresh_data():
        filter_date = cal_filter.get() # Lấy giá trị ngày (dạng chuỗi 'dd/mm/yyyy')
        filter_keyword = entry_search.get().strip()
        # Hàm load_data sẽ tự lấy cal_filter.get_date() (dạng object)
        load_data(tree, status_label_var, filter_date, filter_keyword) 

    # ===== SỰ KIỆN TÌM KIẾM REALTIME (Không thay đổi) =====
    cal_filter.bind("<<DateEntrySelected>>", lambda e: refresh_data())
    entry_search.bind("<KeyRelease>", lambda e: refresh_data())

    # ===== DOUBLE CLICK TO EDIT (Không thay đổi) =====
    def on_double_click(_):
        sel = tree.selection()
        if sel:
            edit_attendance(tree, refresh_data)
    tree.bind("<Double-1>", on_double_click)
    
    # Tải lần đầu
    refresh_data()
# ==============================================================
#  HÀM CRUD (Giữ nguyên logic, không thay đổi)
# ==============================================================

_employee_list = None
_shift_list = None

def fetch_combobox_data():
    global _employee_list, _shift_list
    if _employee_list is None:
        rows = db.fetch_query("SELECT MaNV, HoTen FROM NhanVien WHERE TrangThai = N'Đang làm' ORDER BY HoTen")
        _employee_list = [f"{r['MaNV']} - {r['HoTen']}" for r in rows]
    if _shift_list is None:
        rows = db.fetch_query("SELECT MaCa, TenCa, GioBatDau, GioKetThuc FROM CaLam ORDER BY GioBatDau")
        _shift_list = [f"{r['MaCa']} - {r['TenCa']} ({r['GioBatDau'].strftime('%H:%M')} - {r['GioKetThuc'].strftime('%H:%M')})" for r in rows if r['GioBatDau'] and r['GioKetThuc']]

def add_attendance(refresh, default_date=None):
    fetch_combobox_data()
    win = tk.Toplevel()
    win.title("➕ Thêm chấm công")
    win.geometry("450x400")
    win.configure(bg="#f8f9fa")

    form = tk.Frame(win, bg="#f8f9fa")
    form.pack(padx=20, pady=15, fill="both", expand=True)

    labels = ["Nhân viên", "Ngày làm", "Ca làm", "Giờ vào (HH:MM)", "Giờ ra (HH:MM)", "Ghi chú"]
    entries = {}
    for i, text in enumerate(labels):
        ttk.Label(form, text=text, font=("Arial", 11), background="#f8f9fa").grid(row=i, column=0, sticky="w", padx=8, pady=6)
        if text == "Nhân viên":
            cb = ttk.Combobox(form, values=_employee_list, state="readonly", font=("Arial", 11))
            cb.grid(row=i, column=1, padx=8, pady=6, sticky="ew"); entries[text] = cb
        elif text == "Ca làm":
            cb = ttk.Combobox(form, values=_shift_list, state="normal", font=("Arial", 11))
            cb.grid(row=i, column=1, padx=8, pady=6, sticky="ew"); entries[text] = cb
        elif text == "Ngày làm":
            cal = DateEntry(form, date_pattern="dd/mm/yyyy", font=("Arial", 11), background="#3e2723", foreground="white", borderwidth=2)
            if default_date: cal.set_date(default_date)
            cal.grid(row=i, column=1, padx=8, pady=6, sticky="ew"); entries[text] = cal
        else:
            entry = ttk.Entry(form, font=("Arial", 11))
            entry.grid(row=i, column=1, padx=8, pady=6, sticky="ew"); entries[text] = entry
            
    entries["Giờ vào (HH:MM)"].insert(0, datetime.now().strftime("%H:%M"))
    form.grid_columnconfigure(1, weight=1)
    
    def submit():
        try:
            nv_text = entries["Nhân viên"].get().split(" - ")[0].strip()
            ngay_lam = entries["Ngày làm"].get_date()
            ca_text = entries["Ca làm"].get()
            maca = ca_text.split(" - ")[0].strip() if " - " in ca_text else None
            gio_vao_str = entries["Giờ vào (HH:MM)"].get().strip()
            gio_ra_str = entries["Giờ ra (HH:MM)"].get().strip()
            ghi_chu = entries["Ghi chú"].get().strip()

            if not nv_text or not ngay_lam:
                messagebox.showwarning("Thiếu thông tin", "Nhân viên và Ngày làm là bắt buộc.", parent=win); return
            clock_in_dt = combine_date_time(ngay_lam, gio_vao_str)
            clock_out_dt = combine_date_time(ngay_lam, gio_ra_str)
            
            if clock_in_dt and clock_out_dt and clock_out_dt < clock_in_dt:
                messagebox.showwarning("Lỗi Logic", "Giờ ra (ClockOut) không thể nhỏ hơn Giờ vào (ClockIn).", parent=win)
                return
            
            macham = generate_next_macc(db.cursor) 
            query = "INSERT INTO ChamCong (MaCham, MaNV, MaCa, NgayLam, ClockIn, ClockOut, GhiChu) VALUES (?, ?, ?, ?, ?, ?, ?)"
            params = (macham, nv_text, maca, ngay_lam, clock_in_dt, clock_out_dt, ghi_chu)
            if db.execute_query(query, params):
                messagebox.showinfo("Thành công", "Đã thêm bản ghi chấm công.", parent=win); win.destroy(); refresh()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm chấm công: {e}", parent=win)

    # Sửa tên nút (bị lỗi copy-paste)
    ttk.Button(form, text="💾 Lưu chấm công", style="Add.TButton",
               command=submit).grid(row=len(labels), columnspan=2, pady=15)

def edit_attendance(tree, refresh):
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn bản ghi cần sửa!"); return
    macham = selected[0]
    row = db.fetch_query("SELECT * FROM ChamCong WHERE MaCham = ?", (macham,))
    if not row:
        messagebox.showerror("Lỗi", "Không tìm thấy bản ghi chấm công!"); return
    current = row[0]; fetch_combobox_data()
    win = tk.Toplevel()
    win.title(f"✏️ Sửa chấm công {macham}")
    win.geometry("450x400")
    win.configure(bg="#f8f9fa")

    form = tk.Frame(win, bg="#f8f9fa")
    form.pack(padx=20, pady=15, fill="both", expand=True)

    labels = ["Nhân viên", "Ngày làm", "Ca làm", "Giờ vào (HH:MM)", "Giờ ra (HH:MM)", "Ghi chú"]
    entries = {}
    for i, text in enumerate(labels):
        ttk.Label(form, text=text, font=("Arial", 11), background="#f8f9fa").grid(row=i, column=0, sticky="w", padx=8, pady=6)
        if text == "Nhân viên":
            cb = ttk.Combobox(form, values=_employee_list, state="readonly", font=("Arial", 11))
            for item in _employee_list:
                if item.startswith(current["MaNV"]): cb.set(item); break
            cb.grid(row=i, column=1, padx=8, pady=6, sticky="ew"); entries[text] = cb
        elif text == "Ca làm":
            cb = ttk.Combobox(form, values=_shift_list, state="normal", font=("Arial", 11))
            if current["MaCa"]:
                for item in _shift_list:
                    if item.startswith(str(current["MaCa"])): cb.set(item); break
            cb.grid(row=i, column=1, padx=8, pady=6, sticky="ew"); entries[text] = cb
        elif text == "Ngày làm":
            cal = DateEntry(form, date_pattern="dd/mm/yyyy", font=("Arial", 11), background="#3e2723", foreground="white", borderwidth=2)
            cal.set_date(current["NgayLam"]); cal.grid(row=i, column=1, padx=8, pady=6, sticky="ew"); entries[text] = cal
        else:
            entry = ttk.Entry(form, font=("Arial", 11))
            if text == "Giờ vào (HH:MM)" and current["ClockIn"]: entry.insert(0, current["ClockIn"].strftime("%H:%M"))
            elif text == "Giờ ra (HH:MM)" and current["ClockOut"]: entry.insert(0, current["ClockOut"].strftime("%H:%M"))
            elif text == "Ghi chú": entry.insert(0, current["GhiChu"] or "")
            entry.grid(row=i, column=1, padx=8, pady=6, sticky="ew"); entries[text] = entry
    form.grid_columnconfigure(1, weight=1)
    
    def save():
        try:
            nv_text = entries["Nhân viên"].get().split(" - ")[0].strip()
            ngay_lam = entries["Ngày làm"].get_date()
            ca_text = entries["Ca làm"].get()
            maca = ca_text.split(" - ")[0].strip() if " - " in ca_text else None
            gio_vao_str = entries["Giờ vào (HH:MM)"].get().strip()
            gio_ra_str = entries["Giờ ra (HH:MM)"].get().strip()
            ghi_chu = entries["Ghi chú"].get().strip()

            if not nv_text or not ngay_lam:
                messagebox.showwarning("Thiếu thông tin", "Nhân viên và Ngày làm là bắt buộc.", parent=win); return
            clock_in_dt = combine_date_time(ngay_lam, gio_vao_str)
            clock_out_dt = combine_date_time(ngay_lam, gio_ra_str)
            
            if clock_in_dt and clock_out_dt and clock_out_dt < clock_in_dt:
                messagebox.showwarning("Lỗi Logic", "Giờ ra (ClockOut) không thể nhỏ hơn Giờ vào (ClockIn).", parent=win)
                return

            query = "UPDATE ChamCong SET MaNV=?, MaCa=?, NgayLam=?, ClockIn=?, ClockOut=?, GhiChu=? WHERE MaCham=?"
            params = (nv_text, maca, ngay_lam, clock_in_dt, clock_out_dt, ghi_chu, macham)
            if db.execute_query(query, params):
                messagebox.showinfo("Thành công", "Đã cập nhật bản ghi chấm công.", parent=win); win.destroy(); refresh()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể cập nhật chấm công: {e}", parent=win)

    # Sửa tên nút (bị lỗi copy-paste)
    ttk.Button(form, text="💾 Lưu thay đổi", style="Add.TButton",
               command=save).grid(row=len(labels), columnspan=2, pady=15)

def delete_attendance(tree, refresh):
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn bản ghi cần xóa!"); return
    macham = selected[0] 
    safe_delete(
        table_name="ChamCong", key_column="MaCham", key_value=macham,
        cursor=db.cursor, conn=db.conn,
        refresh_func=refresh, item_label="bản ghi chấm công"
    )