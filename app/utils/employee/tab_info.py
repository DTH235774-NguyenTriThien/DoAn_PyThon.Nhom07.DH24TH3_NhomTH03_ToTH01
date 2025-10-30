# app/utils/employee/tab_info.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from tkcalendar import DateEntry
from app import db

# SỬA 1: Import helper mới
from app.db import execute_query, fetch_query 
from app.utils.utils import create_form_window, go_back,center_window
from app.utils.time_helpers import normalize_date_input
from app.utils.id_helpers import generate_next_manv
from app.utils.business_helpers import safe_delete
from app.utils.treeview_helpers import fill_treeview_chunked # <-- HELPER MỚI
from app.theme import setup_styles


def build_tab(parent, root=None, username=None, role=None):
    """Tab 1 - Thông tin nhân viên (chuẩn hoá từ module employee.py gốc)"""
    setup_styles()
    parent.configure(bg="#f5e6ca")
    center_window(root, 1200, 600, offset_y=-60)

    # ===== THANH CHỨC NĂNG =====
    top_frame = tk.Frame(parent, bg="#f9fafb")
    top_frame.pack(fill="x", pady=10)

    search_var = tk.StringVar()
    tk.Label(top_frame, text="🔎 Tìm nhân viên:", font=("Arial", 11),
             bg="#f9fafb").pack(side="left", padx=5)
    entry_search = ttk.Entry(top_frame, textvariable=search_var, width=35)
    entry_search.pack(side="left", padx=5)
    
    # Label hiển thị trạng thái (ví dụ: "Đang tải...")
    status_label_var = tk.StringVar(value="")
    status_label = ttk.Label(top_frame, textvariable=status_label_var, font=("Arial", 10, "italic"), background="#f9fafb", foreground="blue")
    status_label.pack(side="left", padx=10)

    entry_search.bind("<KeyRelease>", lambda e: load_data(tree, status_label_var, search_var.get().strip()))


    # ====== BẢNG HIỂN THỊ ======
    headers_vn = {
        "MaNV": "Mã NV",
        "HoTen": "Họ tên",
        "GioiTinh": "Giới tính",
        "NgaySinh": "Ngày sinh",
        "ChucVu": "Chức vụ",
        "LuongCoBan": "Lương cơ bản",
        "TrangThai": "Trạng thái"
    }
    columns = list(headers_vn.keys())
    tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)

    for col in columns:
        tree.heading(col, text=headers_vn[col])
        tree.column(col, anchor="center", width=120)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    # ==================================================
    # SỬA 2: NÂNG CẤP load_data VỚI fill_treeview_chunked
    # ==================================================
    def load_data(tree_widget, status_var, keyword=None):
        """Tải danh sách nhân viên, hỗ trợ tìm kiếm và chèn theo từng mẻ (chunked)"""
        
        # Xóa TreeView ngay lập tức (fill_treeview_chunked sẽ tự xóa, 
        # nhưng chúng ta xóa ở đây để người dùng thấy phản hồi ngay)
        tree_widget.delete(*tree_widget.get_children()) 
        status_var.set("Đang tải dữ liệu...")
        tree_widget.update_idletasks() # Ép Tkinter cập nhật UI

        query = """
            SELECT MaNV, HoTen, GioiTinh, NgaySinh, ChucVu, LuongCoBan, TrangThai
            FROM NhanVien
        """
        params = ()

        if keyword:
            keyword = f"%{keyword.strip()}%"
            query += """
                WHERE MaNV LIKE ? OR
                      HoTen LIKE ? OR
                      GioiTinh LIKE ? OR
                      ChucVu LIKE ? OR
                      TrangThai LIKE ?
            """
            params = (keyword, keyword, keyword, keyword, keyword)
        
        query += " ORDER BY MaNV" 

        try:
            # 1. Lấy dữ liệu (nhanh)
            rows = db.fetch_query(query, params)

            # ===== MÃ GIẢ ĐỂ KIỂM TRA HIỆU SUẤT (Stress Test) =====
            #if not keyword: # Chỉ test khi không tìm kiếm
            #   print("--- ĐANG CHẠY STRESS TEST 5000 DÒNG (ĐÃ SỬA LỖI IID) ---")

                # Tạo 5000 dòng test với MaNV duy nhất
                #test_rows = []
                #for i in range(5000):
                #   test_rows.append({
                #        "MaNV": f"NV_TEST_{i}", # <-- MaNV (iid) duy nhất
                #        "HoTen": f"Nhân viên Test {i}", 
                #        "GioiTinh": "Nam", 
                #        "NgaySinh": None, 
                #        "ChucVu": "Tester", 
                #        "LuongCoBan": 100000, 
                #        "TrangThai": "Testing"
                #    })
                # Ghi đè 'rows' bằng dữ liệu test
                #rows = test_rows
            # ================= HẾT MÃ GIẢ =======================
            
            # 2. Chuẩn bị dữ liệu (nhanh)
            tree_data = []
            for row in rows:
                manv = row["MaNV"].strip()
                hoten = row["HoTen"]
                ngaysinh_obj = row["NgaySinh"]
                ngaysinh = ngaysinh_obj.strftime("%d/%m/%Y") if ngaysinh_obj else ""
                chucvu = row["ChucVu"]
                luong_obj = row["LuongCoBan"]
                luong = f"{int(luong_obj):,}" if luong_obj is not None else "0"
                trangthai = row["TrangThai"]
                gioitinh = row["GioiTinh"]

                # Chuẩn bị 1 tuple (danh sách) các giá trị
                values_tuple = (manv, hoten, gioitinh, ngaysinh, chucvu, luong, trangthai)
                
                # Thêm vào danh sách để chèn
                # Chúng ta dùng định dạng (iid, values) mà helper hỗ trợ
                tree_data.append({"iid": manv, "values": values_tuple})

            # 3. "Vẽ" lên TreeView (mượt mà)
            def on_load_complete():
                status_var.set(f"Đã tải {len(rows)} nhân viên.")
                
            fill_treeview_chunked(
                tree=tree_widget, 
                rows=tree_data, 
                batch=100, # Tải 100 dòng mỗi 10ms
                on_complete=on_load_complete
            )

        except Exception as e:
            status_var.set("Lỗi tải dữ liệu!")
            messagebox.showerror("Lỗi", f"Không thể tải hoặc hiển thị dữ liệu: {e}")

    # ====== NÚT CHỨC NĂNG ======
    # (Cập nhật các hàm lambda để truyền tree và status_label_var)
    def refresh_data():
        load_data(tree, status_label_var)

    ttk.Button(top_frame, text="🔄 Tải lại", style="Close.TButton",
               command=refresh_data).pack(side="left", padx=5)
    ttk.Button(top_frame, text="➕ Thêm", style="Add.TButton",
               command=lambda: add_employee(refresh_data)).pack(side="left", padx=5)
    ttk.Button(top_frame, text="✏️ Sửa", style="Edit.TButton",
               command=lambda: edit_employee(tree, refresh_data)).pack(side="left", padx=5)
    ttk.Button(top_frame, text="🗑 Xóa", style="Delete.TButton",
               command=lambda: delete_employee(tree, refresh_data)).pack(side="left", padx=5)
    ttk.Button(top_frame, text="⬅ Quay lại", style="Close.TButton",
               command=lambda: go_back(root, username, role)).pack(side="right", padx=6)

    # ====== GẮN SỰ KIỆN ======
    def on_search_change(event=None):
        kw = search_var.get().strip()
        load_data(tree, status_label_var, kw) 

    def on_double_click(event):
        sel = tree.selection()
        if sel:
            edit_employee(tree, refresh_data)
    tree.bind("<Double-1>", on_double_click)

    # Tải dữ liệu lần đầu
    refresh_data()


# =============================================================
# CÁC HÀM CRUD (Không thay đổi, giữ nguyên)
# =============================================================
def add_employee(refresh):
    """Thêm nhân viên mới"""
    win, form = create_form_window("➕ Thêm nhân viên mới")
    entries = {}

    labels = ["Mã NV", "Họ tên", "Giới tính", "Ngày sinh",
              "Chức vụ", "Lương cơ bản", "Trạng thái"]
    positions = ["Quản lý", "Thu ngân", "Phục vụ", "Pha chế", "Tạp vụ", "Bảo vệ"]
    statuses = ["Đang làm", "Tạm nghỉ", "Đào tạo", "Đã nghỉ"]

    for i, text in enumerate(labels):
        ttk.Label(form, text=text, font=("Arial", 11),
                  background="#f8f9fa").grid(row=i, column=0, sticky="w", padx=8, pady=6)

        if text == "Chức vụ":
            cb = ttk.Combobox(form, values=positions, state="readonly", font=("Arial", 11))
            cb.current(1)
            cb.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = cb

        elif text == "Ngày sinh":
            cal = DateEntry(form, date_pattern="yyyy-mm-dd", font=("Arial", 11),
                            background="#3e2723", foreground="white", borderwidth=2)
            cal.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = cal

        elif text == "Trạng thái":
            cb = ttk.Combobox(form, values=statuses, state="readonly", font=("Arial", 11))
            cb.set("Đang làm")
            cb.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = cb

        elif text == "Giới tính":
            gender_var = tk.StringVar(value="Nam")
            frame_gender = tk.Frame(form, bg="#f8f9fa")
            frame_gender.grid(row=i, column=1, padx=8, pady=6, sticky="w")

            tk.Radiobutton(frame_gender, text="Nam", variable=gender_var, value="Nam",
                           font=("Arial", 11), bg="#f8f9fa").pack(side="left", padx=5)
            tk.Radiobutton(frame_gender, text="Nữ", variable=gender_var, value="Nữ",
                           font=("Arial", 11), bg="#f8f9fa").pack(side="left", padx=5)
            entries[text] = gender_var
        else:
            entry = ttk.Entry(form, font=("Arial", 11))
            entry.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = entry

    btn_frame = tk.Frame(win, bg="#f8f9fa")
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="💾 Lưu sản phẩm", style="Add.TButton",
               command=lambda: submit()).pack(ipadx=10, ipady=6)

    def submit():
        try:
            manv = entries["Mã NV"].get().strip().upper()
            hoten = entries["Họ tên"].get().strip()
            gt = entries["Giới tính"].get()
            ngs = normalize_date_input(entries["Ngày sinh"].get_date())
            cv = entries["Chức vụ"].get().strip()
            luong = float(entries["Lương cơ bản"].get().strip() or 0)
            tt = entries["Trạng thái"].get().strip() or "Đang làm"

            if not manv:
                manv = generate_next_manv(db.cursor)

            # SỬA NHỎ: Dùng execute_scalar cho chuẩn
            count = db.execute_scalar("SELECT COUNT(*) FROM NhanVien WHERE MaNV=?", (manv,))
            
            if count > 0:
                messagebox.showwarning("⚠️ Trùng mã NV", f"Mã {manv} đã tồn tại!")
                return

            query = """
            INSERT INTO NhanVien (MaNV, HoTen, GioiTinh, NgaySinh, ChucVu, LuongCoBan, TrangThai)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (manv, hoten, gt, ngs, cv, luong, tt)

            if execute_query(query, params):
                messagebox.showinfo("✅ Thành công", f"Đã thêm nhân viên {manv}!")
                refresh()
                win.destroy()

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm nhân viên: {e}")


def edit_employee(tree, refresh):
    """Sửa nhân viên"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn nhân viên cần sửa!")
        return

    # SỬA NHỎ: Lấy iid (MaNV) từ tree.selection()
    # thay vì tree.item(..., "values")[0]
    # Điều này an toàn hơn nếu cột bị đổi thứ tự
    manv = selected[0] 
    values = tree.item(manv)["values"]


    win = tk.Toplevel()
    win.title(f"✏️ Sửa nhân viên {manv}")
    win.geometry("430x480")
    win.configure(bg="#f8f9fa")

    form = tk.Frame(win, bg="#f8f9fa")
    form.pack(padx=20, pady=15, fill="both", expand=True)

    labels = ["Họ tên", "Giới tính", "Ngày sinh", "Chức vụ",
              "Lương cơ bản", "Trạng thái"]
    entries = {}
    positions = ["Quản lý", "Thu ngân", "Phục vụ", "Pha chế", "Tạp vụ", "Bảo vệ"]
    statuses = ["Đang làm", "Tạm nghỉ", "Đào tạo", "Đã nghỉ"]
    
    # values[0] là MaNV, nên ta bắt đầu từ values[1]
    current = dict(zip(labels, values)) 
    
    # SỬA NHỎ: Chuyển đổi tên cột TreeView (values)
    # sang tên cột trong form (labels)
    # Vì values giờ có 7 cột (gồm MaNV),
    # nhưng 'current' dict chỉ cần 6 cột (theo 'labels')
    
    # Lấy giá trị từ TreeView bằng tên cột (đã định nghĩa ở headers_vn)
    item_values = tree.item(manv)["values"]
    current_data = {
        "Họ tên": item_values[1],
        "Giới tính": item_values[2],
        "Ngày sinh": item_values[3],
        "Chức vụ": item_values[4],
        "Lương cơ bản": item_values[5],
        "Trạng thái": item_values[6]
    }

    if current_data["Ngày sinh"]:
        try:
            current_data["Ngày sinh"] = datetime.strptime(current_data["Ngày sinh"], "%d/%m/%Y").date()
        except:
            current_data["Ngày sinh"] = datetime.today().date()

    for i, text in enumerate(labels):
        ttk.Label(form, text=text, font=("Arial", 11), background="#f8f9fa").grid(
            row=i, column=0, sticky="w", padx=8, pady=6
        )
        
        current_val = current_data[text]

        if text == "Chức vụ":
            cb = ttk.Combobox(form, values=positions, state="readonly", font=("Arial", 11))
            cb.set(current_val)
            cb.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = cb
        elif text == "Ngày sinh":
            cal = DateEntry(form, date_pattern="yyyy-mm-dd", font=("Arial", 11),
                            background="#3e2723", foreground="white", borderwidth=2)
            cal.set_date(current_val)
            cal.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = cal
        elif text == "Trạng thái":
            cb = ttk.Combobox(form, values=statuses, state="readonly", font=("Arial", 11))
            cb.set(current_val if current_val in statuses else "Đang làm")
            cb.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = cb
        elif text == "Giới tính":
            gender_var = tk.StringVar(value=current_val or "Nam")
            frame_gender = tk.Frame(form, bg="#f8f9fa")
            frame_gender.grid(row=i, column=1, padx=8, pady=6, sticky="w")
            tk.Radiobutton(frame_gender, text="Nam", variable=gender_var, value="Nam",
                           font=("Arial", 11), bg="#f8f9fa").pack(side="left", padx=5)
            tk.Radiobutton(frame_gender, text="Nữ", variable=gender_var, value="Nữ",
                           font=("Arial", 11), bg="#f8f9fa").pack(side="left", padx=5)
            entries[text] = gender_var
        else:
            ent = ttk.Entry(form, font=("Arial", 11))
            ent.insert(0, current_val)
            ent.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = ent

    btn_frame = tk.Frame(win, bg="#f8f9fa")
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="💾 Lưu sản phẩm", style="Add.TButton",
               command=lambda: save()).pack(ipadx=10, ipady=6)

    def save():
        try:
            hoten = entries["Họ tên"].get().strip()
            gt = entries["Giới tính"].get().strip()
            ngs = normalize_date_input(entries["Ngày sinh"].get_date())
            cv = entries["Chức vụ"].get().strip()
            luong = float(entries["Lương cơ bản"].get().replace(",", "").strip() or 0)
            tt = entries["Trạng thái"].get().strip()

            if not hoten:
                messagebox.showwarning("Thiếu thông tin", "⚠️ Họ tên không được để trống.")
                return

            query = """
                UPDATE NhanVien
                SET HoTen=?, GioiTinh=?, NgaySinh=?, ChucVu=?, LuongCoBan=?, TrangThai=?
                WHERE MaNV=?
            """
            params = (hoten, gt, ngs, cv, luong, tt, manv)

            if execute_query(query, params):
                messagebox.showinfo("✅ Thành công", f"Đã cập nhật nhân viên {manv}.")
                refresh()
                win.destroy()

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể cập nhật nhân viên: {e}")


def delete_employee(tree, refresh):
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn nhân viên cần xóa!")
        return
    
    # Lấy iid (MaNV) trực tiếp
    manv = selected[0]

    safe_delete(
        table_name="NhanVien",
        key_column="MaNV",
        key_value=manv,
        cursor=db.cursor,
        conn=db.conn,
        refresh_func=refresh,
        item_label="nhân viên"
    )