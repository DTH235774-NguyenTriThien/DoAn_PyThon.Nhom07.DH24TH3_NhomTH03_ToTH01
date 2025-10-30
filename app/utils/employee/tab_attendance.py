# app/utils/employee/tab_attendance.py
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from app import db
from app.theme import setup_styles
from datetime import datetime

# SỬA 1: Imports
from app.db import fetch_query, execute_query
from app.utils.utils import go_back
from app.utils.business_helpers import safe_delete
from app.utils.time_helpers import (
    format_for_display, parse_date, parse_time, 
    combine_date_time, normalize_date_input
)
from app.utils.id_helpers import generate_next_macc
from app.utils.treeview_helpers import fill_treeview_chunked

def build_tab(parent, root=None, username=None, role=None):
    """Tab Chấm công — Đồng bộ layout giống tab_shift"""
    setup_styles()
    parent.configure(bg="#f5e6ca")

    # ===== THANH CÔNG CỤ (TOP FRAME) =====
    top_frame = tk.Frame(parent, bg="#f9fafb")
    top_frame.pack(fill="x", pady=10, padx=10) 

    # --- Frame NÚT CHỨC NĂNG (Bên phải) ---
    # (Tất cả các nút đều nằm bên phải, giống tab_shift)
    btn_frame = tk.Frame(top_frame, bg="#f9fafb")
    btn_frame.pack(side="right", anchor="n", padx=(10, 0)) # Nằm bên phải
    
    ttk.Button(btn_frame, text="🔄 Tải lại", style="Close.TButton",
               command=lambda: refresh_data()).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="➕ Chấm công", style="Add.TButton",
               command=lambda: add_attendance(refresh_data, cal_filter.get_date())).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="✏️ Sửa", style="Edit.TButton",
               command=lambda: edit_attendance(tree, refresh_data)).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="🗑 Xóa", style="Delete.TButton",
               command=lambda: delete_attendance(tree, refresh_data)).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="⬅ Quay lại", style="Close.TButton",
               command=lambda: go_back(root, username, role)).pack(side="left", padx=5)

    # --- Frame LỌC (Bên trái, tự mở rộng) ---
    filter_frame = tk.Frame(top_frame, bg="#f9fafb")
    filter_frame.pack(side="left", fill="x", expand=True) # Tự lấp đầy

    tk.Label(filter_frame, text="📅 Lọc theo ngày:", font=("Arial", 11),
             bg="#f9fafb").pack(side="left", padx=(5, 2))
    cal_filter = DateEntry(filter_frame, date_pattern="dd/mm/yyyy", font=("Arial", 11),
                           background="#3e2723", foreground="white", borderwidth=2,
                           width=12) 
    cal_filter.pack(side="left", padx=5)
    cal_filter.set_date(datetime.now()) 

    tk.Label(filter_frame, text="🔎 Tìm nhân viên:", font=("Arial", 11),
             bg="#f9fafb").pack(side="left", padx=(10, 2))
    entry_search = ttk.Entry(filter_frame, width=30) 
    entry_search.pack(side="left", padx=5, fill="x", expand=True) 

    # Label trạng thái
    status_label_var = tk.StringVar(value="")
    status_label = ttk.Label(filter_frame, textvariable=status_label_var, font=("Arial", 10, "italic"), background="#f9fafb", foreground="blue")
    status_label.pack(side="left", padx=10)


    # ===== TREEVIEW =====
    columns = ["MaCham", "MaNV", "HoTen", "NgayLam", "TenCa", "ClockIn", "ClockOut", "GhiChu"]
    headers = {
        "MaCham": "Mã Chấm",
        "MaNV": "Mã NV",
        "HoTen": "Họ Tên",
        "NgayLam": "Ngày Làm",
        "TenCa": "Ca Làm",
        "ClockIn": "Giờ Vào",
        "ClockOut": "Giờ Ra",
        "GhiChu": "Ghi Chú"
    }

    tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)
    for col, text in headers.items():
        tree.heading(col, text=text)
        tree.column(col, anchor="center", width=120)
    
    # Điều chỉnh cột
    tree.column("MaCham", width=80)
    tree.column("MaNV", width=80)
    tree.column("HoTen", width=150)
    tree.column("TenCa", width=100)
    tree.column("ClockIn", width=80)
    tree.column("ClockOut", width=80)
    tree.column("GhiChu", width=200, anchor="center") 
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    # (Hàm load_data giữ nguyên như cũ)
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
        except Exception:
            pass 
        if filter_keyword:
            kw = f"%{filter_keyword.strip()}%"
            query += " AND (cc.MaNV LIKE ? OR nv.HoTen LIKE ?) "
            params.extend([kw, kw])
        query += " ORDER BY cc.NgayLam DESC, cc.ClockIn DESC"

        try:
            rows = db.fetch_query(query, tuple(params))
            tree_data = []
            for row in rows:
                macham = row["MaCham"]
                manv = row["MaNV"]
                hoten = row["HoTen"] or ""
                ngaylam_obj = row["NgayLam"]
                ngaylam = ngaylam_obj.strftime("%d/%m/%Y") if ngaylam_obj else ""
                tenca = row["TenCa"] or "N/A"
                clockin_obj = row["ClockIn"]
                clockin = clockin_obj.strftime("%H:%M") if clockin_obj else "--:--"
                clockout_obj = row["ClockOut"]
                clockout = clockout_obj.strftime("%H:%M") if clockout_obj else "--:--"
                ghichu = row["GhiChu"] or ""
                values_tuple = (macham, manv, hoten, ngaylam, tenca, clockin, clockout, ghichu)
                tree_data.append({"iid": macham, "values": values_tuple})

            def on_load_complete():
                status_var.set(f"Đã tải {len(rows)} bản ghi.")
                
            fill_treeview_chunked(
                tree=tree_widget, 
                rows=tree_data, 
                batch=100,
                on_complete=on_load_complete
            )
        except Exception as e:
            status_var.set("Lỗi tải dữ liệu!")
            messagebox.showerror("Lỗi", f"Không thể tải dữ liệu chấm công: {e}")

    # ===== CÁC NÚT CHỨC NĂNG (Cập nhật command) =====
    def refresh_data():
        filter_date = cal_filter.get()
        filter_keyword = entry_search.get().strip()
        load_data(tree, status_label_var, filter_date, filter_keyword)

    # ===== SỰ KIỆN TÌM KIẾM REALTIME (Cập nhật command) =====
    cal_filter.bind("<<DateEntrySelected>>", lambda e: refresh_data())
    entry_search.bind("<KeyRelease>", lambda e: refresh_data())

    # ===== DOUBLE CLICK TO EDIT (Cập nhật command) =====
    def on_double_click(_):
        sel = tree.selection()
        if sel:
            edit_attendance(tree, refresh_data)
    tree.bind("<Double-1>", on_double_click)
    
    # Tải lần đầu
    refresh_data()

# ==============================================================
#  HÀM CRUD
# ==============================================================

# Biến cache cho ComboBox Nhân viên và Ca làm
_employee_list = None
_shift_list = None

def fetch_combobox_data():
    """Tải và cache danh sách NV, Ca làm để dùng trong form Add/Edit"""
    global _employee_list, _shift_list
    if _employee_list is None:
        # Lấy NV (Mã - Tên)
        rows = db.fetch_query("SELECT MaNV, HoTen FROM NhanVien WHERE TrangThai = N'Đang làm' ORDER BY HoTen")
        _employee_list = [f"{r['MaNV']} - {r['HoTen']}" for r in rows]
    
    if _shift_list is None:
        # Lấy Ca (Mã - Tên - Giờ)
        rows = db.fetch_query("SELECT MaCa, TenCa, GioBatDau, GioKetThuc FROM CaLam ORDER BY GioBatDau")
        _shift_list = [f"{r['MaCa']} - {r['TenCa']} ({r['GioBatDau'].strftime('%H:%M')} - {r['GioKetThuc'].strftime('%H:%M')})" for r in rows if r['GioBatDau'] and r['GioKetThuc']]


def add_attendance(refresh, default_date=None):
    """Thêm bản ghi chấm công mới"""
    fetch_combobox_data() # Đảm bảo có dữ liệu cho ComboBox

    win = tk.Toplevel()
    win.title("➕ Thêm chấm công")
    win.geometry("450x400")
    win.configure(bg="#f8f9fa")

    form = tk.Frame(win, bg="#f8f9fa")
    form.pack(padx=20, pady=15, fill="both", expand=True)

    labels = ["Nhân viên", "Ngày làm", "Ca làm", "Giờ vào (HH:MM)", "Giờ ra (HH:MM)", "Ghi chú"]
    entries = {}

    for i, text in enumerate(labels):
        ttk.Label(form, text=text, font=("Arial", 11),
                  background="#f8f9fa").grid(row=i, column=0, sticky="w", padx=8, pady=6)
        
        if text == "Nhân viên":
            cb = ttk.Combobox(form, values=_employee_list, state="readonly", font=("Arial", 11))
            cb.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = cb
        elif text == "Ca làm":
            cb = ttk.Combobox(form, values=_shift_list, state="normal", font=("Arial", 11))
            cb.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = cb
        elif text == "Ngày làm":
            cal = DateEntry(form, date_pattern="dd/mm/yyyy", font=("Arial", 11),
                            background="#3e2723", foreground="white", borderwidth=2)
            if default_date:
                cal.set_date(default_date)
            cal.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = cal
        else:
            entry = ttk.Entry(form, font=("Arial", 11))
            entry.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = entry

    # Gợi ý giờ vào là giờ hiện tại
    entries["Giờ vào (HH:MM)"].insert(0, datetime.now().strftime("%H:%M"))

    form.grid_columnconfigure(1, weight=1)
    
    def submit():
        try:
            # 1. Lấy và chuẩn hóa dữ liệu
            nv_text = entries["Nhân viên"].get().split(" - ")[0].strip()
            ngay_lam = entries["Ngày làm"].get_date()
            
            ca_text = entries["Ca làm"].get()
            maca = ca_text.split(" - ")[0].strip() if " - " in ca_text else None
            
            gio_vao_str = entries["Giờ vào (HH:MM)"].get().strip()
            gio_ra_str = entries["Giờ ra (HH:MM)"].get().strip()
            ghi_chu = entries["Ghi chú"].get().strip()

            if not nv_text or not ngay_lam:
                messagebox.showwarning("Thiếu thông tin", "Nhân viên và Ngày làm là bắt buộc.", parent=win)
                return

            # Kết hợp Ngày + Giờ
            clock_in_dt = combine_date_time(ngay_lam, gio_vao_str)
            clock_out_dt = combine_date_time(ngay_lam, gio_ra_str)
            
            # Nếu nhập 'ca' nhưng không nhập giờ, thử tự động lấy giờ
            if maca and (not clock_in_dt or not clock_out_dt):
                pass # (Có thể thêm logic tự lấy giờ ca ở đây nếu muốn)

            # ==================================================
            # THÊM VALIDATION ĐỂ SỬA LỖI
            # ==================================================
            if clock_in_dt and clock_out_dt and clock_out_dt < clock_in_dt:
                messagebox.showwarning("Lỗi Logic", 
                                      "Giờ ra (ClockOut) không thể nhỏ hơn Giờ vào (ClockIn) trong cùng một ngày.", 
                                      parent=win)
                return
            # ==================================================            

            # 2. Lấy MaCham mới
            macham = generate_next_macc(db.cursor) # Dùng helper sinh mã

            # 3. Lưu (SỬA 3: Dùng execute_query)
            query = """
                INSERT INTO ChamCong (MaCham, MaNV, MaCa, NgayLam, ClockIn, ClockOut, GhiChu)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (macham, nv_text, maca, ngay_lam, clock_in_dt, clock_out_dt, ghi_chu)
            
            if db.execute_query(query, params):
                messagebox.showinfo("Thành công", "Đã thêm bản ghi chấm công.", parent=win)
                win.destroy()
                refresh()
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm chấm công: {e}", parent=win)

    btn_frame = tk.Frame(win, bg="#f8f9fa")
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="💾 Lưu sản phẩm", style="Add.TButton",
               command=lambda: submit()).pack(ipadx=10, ipady=6)


def edit_attendance(tree, refresh):
    """Sửa bản ghi chấm công"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn bản ghi cần sửa!")
        return
    
    # SỬA 4: Lấy iid (MaCham) trực tiếp
    macham = selected[0]
    
    # Lấy dữ liệu thô từ CSDL để sửa (chính xác hơn là từ TreeView)
    row = db.fetch_query("SELECT * FROM ChamCong WHERE MaCham = ?", (macham,))
    if not row:
        messagebox.showerror("Lỗi", "Không tìm thấy bản ghi chấm công!")
        return
    
    current = row[0] # fetch_query trả về list[dict]
    fetch_combobox_data() # Tải data cho ComboBox

    win = tk.Toplevel()
    win.title(f"✏️ Sửa chấm công {macham}")
    win.geometry("450x400")
    win.configure(bg="#f8f9fa")

    form = tk.Frame(win, bg="#f8f9fa")
    form.pack(padx=20, pady=15, fill="both", expand=True)

    labels = ["Nhân viên", "Ngày làm", "Ca làm", "Giờ vào (HH:MM)", "Giờ ra (HH:MM)", "Ghi chú"]
    entries = {}

    for i, text in enumerate(labels):
        ttk.Label(form, text=text, font=("Arial", 11),
                  background="#f8f9fa").grid(row=i, column=0, sticky="w", padx=8, pady=6)
        
        if text == "Nhân viên":
            cb = ttk.Combobox(form, values=_employee_list, state="readonly", font=("Arial", 11))
            # Tìm giá trị khớp
            for item in _employee_list:
                if item.startswith(current["MaNV"]):
                    cb.set(item)
                    break
            cb.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = cb
        elif text == "Ca làm":
            cb = ttk.Combobox(form, values=_shift_list, state="normal", font=("Arial", 11))
            # Tìm giá trị khớp
            if current["MaCa"]:
                for item in _shift_list:
                    if item.startswith(str(current["MaCa"])):
                        cb.set(item)
                        break
            cb.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = cb
        elif text == "Ngày làm":
            cal = DateEntry(form, date_pattern="dd/mm/yyyy", font=("Arial", 11),
                            background="#3e2723", foreground="white", borderwidth=2)
            cal.set_date(current["NgayLam"])
            cal.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = cal
        else:
            entry = ttk.Entry(form, font=("Arial", 11))
            if text == "Giờ vào (HH:MM)" and current["ClockIn"]:
                entry.insert(0, current["ClockIn"].strftime("%H:%M"))
            elif text == "Giờ ra (HH:MM)" and current["ClockOut"]:
                entry.insert(0, current["ClockOut"].strftime("%H:%M"))
            elif text == "Ghi chú":
                entry.insert(0, current["GhiChu"] or "")
            entry.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = entry

    form.grid_columnconfigure(1, weight=1)
    
    def save():
        try:
            # 1. Lấy và chuẩn hóa dữ liệu
            nv_text = entries["Nhân viên"].get().split(" - ")[0].strip()
            ngay_lam = entries["Ngày làm"].get_date()
            
            ca_text = entries["Ca làm"].get()
            maca = ca_text.split(" - ")[0].strip() if " - " in ca_text else None
            
            gio_vao_str = entries["Giờ vào (HH:MM)"].get().strip()
            gio_ra_str = entries["Giờ ra (HH:MM)"].get().strip()
            ghi_chu = entries["Ghi chú"].get().strip()

            if not nv_text or not ngay_lam:
                messagebox.showwarning("Thiếu thông tin", "Nhân viên và Ngày làm là bắt buộc.", parent=win)
                return

            clock_in_dt = combine_date_time(ngay_lam, gio_vao_str)
            clock_out_dt = combine_date_time(ngay_lam, gio_ra_str)

            # ==================================================
            # THÊM VALIDATION ĐỂ SỬA LỖI
            # ==================================================
            if clock_in_dt and clock_out_dt and clock_out_dt < clock_in_dt:
                messagebox.showwarning("Lỗi Logic", 
                                      "Giờ ra (ClockOut) không thể nhỏ hơn Giờ vào (ClockIn) trong cùng một ngày.", 
                                      parent=win)
                return
            # ==================================================            

            # 2. Lưu (SỬA 5: Dùng execute_query)
            query = """
                UPDATE ChamCong 
                SET MaNV=?, MaCa=?, NgayLam=?, ClockIn=?, ClockOut=?, GhiChu=?
                WHERE MaCham=?
            """
            params = (nv_text, maca, ngay_lam, clock_in_dt, clock_out_dt, ghi_chu, macham)
            
            if db.execute_query(query, params):
                messagebox.showinfo("Thành công", "Đã cập nhật bản ghi chấm công.", parent=win)
                win.destroy()
                refresh()
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể cập nhật chấm công: {e}", parent=win)

    btn_frame = tk.Frame(win, bg="#f8f9fa")
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="💾 Lưu sản phẩm", style="Add.TButton",
               command=lambda: save()).pack(ipadx=10, ipady=6)


def delete_attendance(tree, refresh):
    """Xóa bản ghi chấm công"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn bản ghi cần xóa!")
        return

    # SỬA 6: Lấy iid (macham) trực tiếp
    macham = selected[0] 

    safe_delete(
        table_name="ChamCong",
        key_column="MaCham",
        key_value=macham,
        cursor=db.cursor,
        conn=db.conn,
        refresh_func=refresh,
        item_label="bản ghi chấm công"
    )