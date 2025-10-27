import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from tkcalendar import DateEntry
from app import db
from app.db import execute_query
from app.utils.utils import normalize_date_input, create_form_window, safe_delete, go_back, generate_next_manv
from app.theme import setup_styles


def build_tab(parent, root=None, username=None, role=None):
    """Tab 1 - Thông tin nhân viên (chuẩn hoá từ module employee.py gốc)"""
    setup_styles()
    parent.configure(bg="#f5e6ca")

    # ===== THANH CHỨC NĂNG =====
    top_frame = tk.Frame(parent, bg="#f9fafb")
    top_frame.pack(fill="x", pady=10)

    search_var = tk.StringVar()
    tk.Label(top_frame, text="🔎 Tìm nhân viên:", font=("Arial", 11),
             bg="#f9fafb").pack(side="left", padx=5)
    entry_search = ttk.Entry(top_frame, textvariable=search_var, width=35)
    entry_search.pack(side="left", padx=5)
    entry_search.bind("<KeyRelease>", lambda e: load_data(search_var.get().strip()))


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

    # ====== HÀM TẢI DỮ LIỆU ======
    def load_data(keyword=None):
        """Tải danh sách nhân viên, hỗ trợ tìm kiếm theo nhiều cột"""
        for item in tree.get_children():
            tree.delete(item)

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

        try:
            db.cursor.execute(query, params)
            rows = db.cursor.fetchall()
            keyword_lower = keyword.lower().strip("%") if keyword else ""

            for row in rows:
                manv = row.MaNV.strip()
                hoten = row.HoTen
                ngaysinh = row.NgaySinh.strftime("%d/%m/%Y") if row.NgaySinh else ""
                chucvu = row.ChucVu
                luong = f"{int(row.LuongCoBan):,}"
                trangthai = row.TrangThai

                item_id = tree.insert("", "end", values=[
                    manv, hoten, row.GioiTinh, ngaysinh, chucvu, luong, trangthai
                ])

                # Highlight keyword
                #if keyword_lower and (
                #    keyword_lower in manv.lower()
                #    or keyword_lower in hoten.lower()
                #    or keyword_lower in row.GioiTinh.lower()
                #    or keyword_lower in chucvu.lower()
                #    or keyword_lower in trangthai.lower()
                #):
                #    tree.item(item_id, tags=("highlight",))

            tree.tag_configure("highlight", background="#fff3cd",
                               font=("Arial", 11, "bold"))

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải dữ liệu: {e}")

    # ====== NÚT CHỨC NĂNG ======
    ttk.Button(top_frame, text="🔄 Tải lại", style="Close.TButton",
               command=load_data).pack(side="left", padx=5)
    ttk.Button(top_frame, text="➕ Thêm", style="Add.TButton",
               command=lambda: add_employee(load_data)).pack(side="left", padx=5)
    ttk.Button(top_frame, text="✏️ Sửa", style="Edit.TButton",
               command=lambda: edit_employee(tree, load_data)).pack(side="left", padx=5)
    ttk.Button(top_frame, text="🗑 Xóa", style="Delete.TButton",
               command=lambda: delete_employee(tree, load_data)).pack(side="left", padx=5)
    ttk.Button(top_frame, text="⬅ Quay lại", style="Close.TButton",
                command=lambda: go_back(root, username, role)).pack(side="right", padx=6)

    # ====== GẮN SỰ KIỆN ======
    def on_search_change(event=None):
        kw = search_var.get().strip()
        load_data(kw)

    def on_double_click(event):
        sel = tree.selection()
        if sel:
            edit_employee(tree, load_data)
    tree.bind("<Double-1>", on_double_click)

    # Tải dữ liệu lần đầu
    load_data()


# =============================================================
# CÁC HÀM CRUD
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

    form.grid_columnconfigure(1, weight=1)
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

            if not manv:
                manv = generate_next_manv(db.cursor)

            db.cursor.execute("SELECT COUNT(*) FROM NhanVien WHERE MaNV=?", (manv,))
            if db.cursor.fetchone()[0] > 0:
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

    values = tree.item(selected[0])["values"]
    manv = values[0]

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

    current = dict(zip(labels, values[1:]))
    if current["Ngày sinh"]:
        try:
            current["Ngày sinh"] = datetime.strptime(current["Ngày sinh"], "%d/%m/%Y").date()
        except:
            current["Ngày sinh"] = datetime.today().date()

    for i, text in enumerate(labels):
        ttk.Label(form, text=text, font=("Arial", 11), background="#f8f9fa").grid(
            row=i, column=0, sticky="w", padx=8, pady=6
        )

        if text == "Chức vụ":
            cb = ttk.Combobox(form, values=positions, state="readonly", font=("Arial", 11))
            cb.set(current[text])
            cb.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = cb
        elif text == "Ngày sinh":
            cal = DateEntry(form, date_pattern="yyyy-mm-dd", font=("Arial", 11),
                            background="#3e2723", foreground="white", borderwidth=2)
            cal.set_date(current["Ngày sinh"])
            cal.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = cal
        elif text == "Trạng thái":
            cb = ttk.Combobox(form, values=statuses, state="readonly", font=("Arial", 11))
            cb.set(current[text] if current[text] in statuses else "Đang làm")
            cb.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = cb
        elif text == "Giới tính":
            gender_var = tk.StringVar(value=current.get("Giới tính", "Nam"))
            frame_gender = tk.Frame(form, bg="#f8f9fa")
            frame_gender.grid(row=i, column=1, padx=8, pady=6, sticky="w")
            tk.Radiobutton(frame_gender, text="Nam", variable=gender_var, value="Nam",
                           font=("Arial", 11), bg="#f8f9fa").pack(side="left", padx=5)
            tk.Radiobutton(frame_gender, text="Nữ", variable=gender_var, value="Nữ",
                           font=("Arial", 11), bg="#f8f9fa").pack(side="left", padx=5)
            entries[text] = gender_var
        else:
            ent = ttk.Entry(form, font=("Arial", 11))
            ent.insert(0, current[text])
            ent.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = ent

    form.grid_columnconfigure(1, weight=1)
    ttk.Button(form, text="💾 Lưu thay đổi", style="Add.TButton",
               command=lambda: save()).grid(row=len(labels), columnspan=2, pady=10)

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

    values = tree.item(selected[0])["values"]
    manv = values[0]

    safe_delete(
        table_name="NhanVien",
        key_column="MaNV",
        key_value=manv,
        cursor=db.cursor,
        conn=db.conn,
        refresh_func=refresh,
        item_label="nhân viên"
    )
