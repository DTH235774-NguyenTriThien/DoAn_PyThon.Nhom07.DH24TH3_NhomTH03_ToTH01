# app/utils/employee/tab_info.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from tkcalendar import DateEntry
from app import db

# Import helpers
from app.db import execute_query, fetch_query, execute_scalar
from app.utils.utils import create_form_window
from app.utils.time_helpers import normalize_date_input
from app.utils.id_helpers import generate_next_manv
from app.utils.business_helpers import safe_delete
from app.utils.treeview_helpers import fill_treeview_chunked
from app.theme import setup_styles

# SỬA 1: Thay đổi tham số hàm (không còn root, username, role)
def build_tab(parent, on_back_callback=None):
    """Tab 1 - Thông tin nhân viên (Đã refactor cho GĐ 2)"""
    setup_styles()
    parent.configure(bg="#f5e6ca")
    
    # (Xóa center_window)

    # ===== THANH CHỨC NĂNG =====
    # (Sắp xếp lại layout cho nhất quán)
    top_frame = tk.Frame(parent, bg="#f9fafb")
    top_frame.pack(fill="x", pady=10, padx=10)

    # --- Frame Nút (Bên phải) ---
    btn_frame = tk.Frame(top_frame, bg="#f9fafb")
    btn_frame.pack(side="right", anchor="n", padx=(10, 0))

    # --- Frame Lọc (Bên trái) ---
    filter_frame = tk.Frame(top_frame, bg="#f9fafb")
    filter_frame.pack(side="left", fill="x", expand=True)

    tk.Label(filter_frame, text="🔎 Tìm NV:", font=("Arial", 11),
             bg="#f9fafb").pack(side="left", padx=(5, 2))
    search_var = tk.StringVar()
    entry_search = ttk.Entry(filter_frame, textvariable=search_var, width=30)
    entry_search.pack(side="left", padx=5, fill="x", expand=True)
    
    status_label_var = tk.StringVar(value="")
    status_label = ttk.Label(filter_frame, textvariable=status_label_var, font=("Arial", 10, "italic"), background="#f9fafb", foreground="blue")
    status_label.pack(side="left", padx=10)


    # ====== BẢNG HIỂN THỊ ======
    # (SỬA 4: Đặt TreeView vào 1 Frame riêng để pack)
    tree_frame = tk.Frame(parent, bg="#f5e6ca")
    tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    headers_vn = {
        "MaNV": "Mã NV", "HoTen": "Họ tên", "GioiTinh": "Giới tính", 
        "NgaySinh": "Ngày sinh", "ChucVu": "Chức vụ", "LuongCoBan": "Lương cơ bản", 
        "TrangThai": "Trạng thái"
    }
    columns = list(headers_vn.keys())
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)

    for col in columns:
        tree.heading(col, text=headers_vn[col])
        tree.column(col, anchor="center", width=120)
    tree.pack(fill="both", expand=True) # Đặt tree vào tree_frame

    # ====== HÀM TẢI DỮ LIỆU (Đã chuẩn hóa) ======
    def load_data(tree_widget, status_var, keyword=None):
        status_var.set("Đang tải dữ liệu...")
        tree_widget.update_idletasks()
        query = "SELECT * FROM NhanVien" # Lấy * để đảm bảo mọi cột đều có
        params = ()
        if keyword:
            kw = f"%{keyword.strip()}%"
            query += " WHERE MaNV LIKE ? OR HoTen LIKE ? OR ChucVu LIKE ? OR TrangThai LIKE ?"
            params = (kw, kw, kw, kw)
        query += " ORDER BY MaNV"
        try:
            rows = db.fetch_query(query, params)
            tree_data = []
            for row in rows:
                ngaysinh_obj = row["NgaySinh"]
                ngaysinh = ngaysinh_obj.strftime("%d/%m/%Y") if ngaysinh_obj else ""
                luong_obj = row["LuongCoBan"]
                luong = f"{int(luong_obj):,}" if luong_obj is not None else "0"
                values_tuple = (
                    row["MaNV"], row["HoTen"], row["GioiTinh"], 
                    ngaysinh, row["ChucVu"], luong, row["TrangThai"]
                )
                tree_data.append({"iid": row["MaNV"], "values": values_tuple})
            
            fill_treeview_chunked(
                tree_widget, 
                tree_data, 
                on_complete=lambda: status_var.set(f"Đã tải {len(rows)} nhân viên.")
            )
        except Exception as e:
            status_var.set("Lỗi tải!")
            messagebox.showerror("Lỗi", f"Không thể tải hoặc hiển thị dữ liệu: {e}")

    # ====== NÚT CHỨC NĂNG (trong btn_frame) ======
    def refresh_data():
        load_data(tree, status_label_var, search_var.get().strip())

    ttk.Button(btn_frame, text="🔄 Tải lại", style="Close.TButton",
               command=refresh_data).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="➕ Thêm", style="Add.TButton",
               command=lambda: add_employee(refresh_data)).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="✏️ Sửa", style="Edit.TButton",
               command=lambda: edit_employee(tree, refresh_data)).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="🗑 Xóa", style="Delete.TButton",
               command=lambda: delete_employee(tree, refresh_data)).pack(side="left", padx=5)
    
    # SỬA 2: Sửa nút "Quay lại"
    if on_back_callback:
        ttk.Button(btn_frame, text="⬅ Quay lại Dashboard", style="Close.TButton",
                   command=on_back_callback).pack(side="left", padx=5)

    # ====== GẮN SỰ KIỆN ======
    def on_search_change(event=None):
        refresh_data()
    entry_search.bind("<KeyRelease>", on_search_change) # SỬA 3: Đổi trace thành bind

    def on_double_click(event):
        sel = tree.selection()
        if sel:
            edit_employee(tree, refresh_data)
    tree.bind("<Double-1>", on_double_click)

    # Tải dữ liệu lần đầu
    refresh_data()


# =============================================================
# CÁC HÀM CRUD (Giữ nguyên logic, không thay đổi)
# (Đã được chuẩn hóa từ trước)
# =============================================================
def add_employee(refresh):
    win, form = create_form_window("➕ Thêm nhân viên mới", "430x480") # Sửa size
    entries = {}
    labels = ["Mã NV", "Họ tên", "Giới tính", "Ngày sinh", "Chức vụ", "Lương cơ bản", "Trạng thái"]
    positions = ["Quản lý", "Thu ngân", "Phục vụ", "Pha chế", "Tạp vụ", "Bảo vệ"]
    statuses = ["Đang làm", "Tạm nghỉ", "Đào tạo", "Đã nghỉ"]
    for i, text in enumerate(labels):
        ttk.Label(form, text=text, font=("Arial", 11), background="#f8f9fa").grid(row=i, column=0, sticky="w", padx=8, pady=6)
        if text == "Chức vụ":
            cb = ttk.Combobox(form, values=positions, state="readonly", font=("Arial", 11)); cb.current(1)
            cb.grid(row=i, column=1, padx=8, pady=6, sticky="ew"); entries[text] = cb
        elif text == "Ngày sinh":
            cal = DateEntry(form, date_pattern="yyyy-mm-dd", font=("Arial", 11), background="#3e2723", foreground="white", borderwidth=2)
            cal.grid(row=i, column=1, padx=8, pady=6, sticky="ew"); entries[text] = cal
        elif text == "Trạng thái":
            cb = ttk.Combobox(form, values=statuses, state="readonly", font=("Arial", 11)); cb.set("Đang làm")
            cb.grid(row=i, column=1, padx=8, pady=6, sticky="ew"); entries[text] = cb
        elif text == "Giới tính":
            gender_var = tk.StringVar(value="Nam"); frame_gender = tk.Frame(form, bg="#f8f9fa")
            frame_gender.grid(row=i, column=1, padx=8, pady=6, sticky="w")
            tk.Radiobutton(frame_gender, text="Nam", variable=gender_var, value="Nam", font=("Arial", 11), bg="#f8f9fa").pack(side="left", padx=5)
            tk.Radiobutton(frame_gender, text="Nữ", variable=gender_var, value="Nữ", font=("Arial", 11), bg="#f8f9fa").pack(side="left", padx=5)
            entries[text] = gender_var
        else:
            entry = ttk.Entry(form, font=("Arial", 11)); entry.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = entry
            
    # Tự động điền mã NV
    manv_auto = generate_next_manv(db.cursor)
    entries["Mã NV"].insert(0, manv_auto)
            
    form.grid_columnconfigure(1, weight=1)
    
    # Sửa tên nút cho nhất quán
    ttk.Button(form, text="💾 Lưu nhân viên", style="Add.TButton", 
               command=lambda: submit()).grid(row=len(labels), columnspan=2, pady=10)

    def submit():
        try:
            manv = entries["Mã NV"].get().strip().upper()
            hoten = entries["Họ tên"].get().strip()
            gt = entries["Giới tính"].get()
            ngs = normalize_date_input(entries["Ngày sinh"].get_date())
            cv = entries["Chức vụ"].get().strip()
            luong = float(entries["Lương cơ bản"].get().strip() or 0)
            tt = entries["Trạng thái"].get().strip() or "Đang làm"

            if not manv or not hoten:
                 messagebox.showwarning("Thiếu thông tin", "Mã NV và Họ tên là bắt buộc.", parent=win)
                 return

            count = db.execute_scalar("SELECT COUNT(*) FROM NhanVien WHERE MaNV=?", (manv,))
            if count > 0:
                messagebox.showwarning("⚠️ Trùng mã NV", f"Mã {manv} đã tồn tại!", parent=win)
                return

            query = "INSERT INTO NhanVien (MaNV, HoTen, GioiTinh, NgaySinh, ChucVu, LuongCoBan, TrangThai) VALUES (?, ?, ?, ?, ?, ?, ?)"
            params = (manv, hoten, gt, ngs, cv, luong, tt)
            if execute_query(query, params):
                messagebox.showinfo("✅ Thành công", f"Đã thêm nhân viên {manv}!", parent=win)
                refresh()
                win.destroy()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm nhân viên: {e}", parent=win)

def edit_employee(tree, refresh):
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn nhân viên cần sửa!"); return
    manv = selected[0]; values = tree.item(manv)["values"]
    win, form = create_form_window(f"✏️ Sửa nhân viên {manv}", "430x480")
    
    labels = ["Họ tên", "Giới tính", "Ngày sinh", "Chức vụ", "Lương cơ bản", "Trạng thái"]
    entries = {}; positions = ["Quản lý", "Thu ngân", "Phục vụ", "Pha chế", "Tạp vụ", "Bảo vệ"]
    statuses = ["Đang làm", "Tạm nghỉ", "Đào tạo", "Đã nghỉ"]
    
    item_values = tree.item(manv)["values"]
    current_data = {
        "Họ tên": item_values[1], "Giới tính": item_values[2], "Ngày sinh": item_values[3],
        "Chức vụ": item_values[4], "Lương cơ bản": item_values[5], "Trạng thái": item_values[6]
    }
    if current_data["Ngày sinh"]:
        try: current_data["Ngày sinh"] = datetime.strptime(current_data["Ngày sinh"], "%d/%m/%Y").date()
        except: current_data["Ngày sinh"] = datetime.today().date()
    else:
        current_data["Ngày sinh"] = None # Xử lý nếu ngày sinh là rỗng

    for i, text in enumerate(labels):
        ttk.Label(form, text=text, font=("Arial", 11), background="#f8f9fa").grid(row=i, column=0, sticky="w", padx=8, pady=6)
        current_val = current_data[text]
        if text == "Chức vụ":
            cb = ttk.Combobox(form, values=positions, state="readonly", font=("Arial", 11)); cb.set(current_val)
            cb.grid(row=i, column=1, padx=8, pady=6, sticky="ew"); entries[text] = cb
        elif text == "Ngày sinh":
            cal = DateEntry(form, date_pattern="yyyy-mm-dd", font=("Arial", 11), background="#3e2723", foreground="white", borderwidth=2)
            if current_val: cal.set_date(current_val) # Chỉ set nếu ngày hợp lệ
            cal.grid(row=i, column=1, padx=8, pady=6, sticky="ew"); entries[text] = cal
        elif text == "Trạng thái":
            cb = ttk.Combobox(form, values=statuses, state="readonly", font=("Arial", 11))
            cb.set(current_val if current_val in statuses else "Đang làm"); cb.grid(row=i, column=1, padx=8, pady=6, sticky="ew"); entries[text] = cb
        elif text == "Giới tính":
            gender_var = tk.StringVar(value=current_val or "Nam"); frame_gender = tk.Frame(form, bg="#f8f9fa")
            frame_gender.grid(row=i, column=1, padx=8, pady=6, sticky="w")
            tk.Radiobutton(frame_gender, text="Nam", variable=gender_var, value="Nam", font=("Arial", 11), bg="#f8f9fa").pack(side="left", padx=5)
            tk.Radiobutton(frame_gender, text="Nữ", variable=gender_var, value="Nữ", font=("Arial", 11), bg="#f8f9fa").pack(side="left", padx=5)
            entries[text] = gender_var
        else:
            ent = ttk.Entry(form, font=("Arial", 11)); ent.insert(0, str(current_val).replace(",", ""))
            ent.grid(row=i, column=1, padx=8, pady=6, sticky="ew"); entries[text] = ent
            
    form.grid_columnconfigure(1, weight=1)
    
    # Sửa tên nút cho nhất quán
    ttk.Button(form, text="💾 Lưu thay đổi", style="Add.TButton", 
               command=lambda: save()).grid(row=len(labels), columnspan=2, pady=10)

    def save():
        try:
            hoten = entries["Họ tên"].get().strip()
            gt = entries["Giới tính"].get().strip()
            # Lấy ngày, chấp nhận None
            ngs_date = entries["Ngày sinh"].get_date()
            ngs = normalize_date_input(ngs_date) if ngs_date else None
            
            cv = entries["Chức vụ"].get().strip()
            luong = float(entries["Lương cơ bản"].get().replace(",", "").strip() or 0)
            tt = entries["Trạng thái"].get().strip()
            if not hoten: messagebox.showwarning("Thiếu thông tin", "⚠️ Họ tên không được để trống.", parent=win); return
            
            query = "UPDATE NhanVien SET HoTen=?, GioiTinh=?, NgaySinh=?, ChucVu=?, LuongCoBan=?, TrangThai=? WHERE MaNV=?"
            params = (hoten, gt, ngs, cv, luong, tt, manv)
            
            if execute_query(query, params):
                messagebox.showinfo("✅ Thành công", f"Đã cập nhật nhân viên {manv}.", parent=win); refresh(); win.destroy()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể cập nhật nhân viên: {e}", parent=win)

def delete_employee(tree, refresh):
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn nhân viên cần xóa!"); return
    manv = selected[0]
    safe_delete(table_name="NhanVien", key_column="MaNV", key_value=manv,
                cursor=db.cursor, conn=db.conn, refresh_func=refresh, item_label="nhân viên")