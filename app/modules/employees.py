import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from app import db
from tkcalendar import DateEntry
from datetime import datetime
from app.utils import clear_window
from app.utils import normalize_date_input

def show_employee_module(root, username=None, role=None):
    """Giao diện quản lý nhân viên (phiên bản frame-based)"""
    clear_window(root)
    root.title("Quản lý nhân viên")

    window_width = 1200
    window_height = 600
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width / 2) - (window_width / 2))
    y = int((screen_height / 2) - (window_height / 2))
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    root.minsize(1000, 550)

    # ====== THANH TIÊU ĐỀ ======
    header = tk.Frame(root, bg="#3e2723", height=70)
    header.pack(fill="x")
    tk.Label(header, text="📋 QUẢN LÝ NHÂN VIÊN", bg="#3e2723", fg="white",
             font=("Arial", 18, "bold")).pack(pady=15)

    # ====== KHUNG CHỨC NĂNG ======
    top_frame = tk.Frame(root, bg="#f9fafb")
    top_frame.pack(fill="x", pady=10)

    search_var = tk.StringVar()
    tk.Label(top_frame, text="🔎 Tìm nhân viên:", font=("Arial", 11), bg="#f9fafb").pack(side="left", padx=5)
    entry_search = ttk.Entry(top_frame, textvariable=search_var, width=40)
    entry_search.pack(side="left", padx=5)

    ttk.Button(top_frame, text="Tải lại", command=lambda: load_data()).pack(side="left", padx=5)
    ttk.Button(top_frame, text="➕ Thêm", command=lambda: add_employee(load_data)).pack(side="left", padx=5)
    ttk.Button(top_frame, text="✏️ Sửa", command=lambda: edit_employee(tree, load_data, role)).pack(side="left", padx=5)
    ttk.Button(top_frame, text="🗑️ Xóa", command=lambda: delete_employee(tree, load_data)).pack(side="left", padx=5)
    ttk.Button(top_frame, text="⬅ Quay lại", command=lambda: go_back(root, username, role)).pack(side="right", padx=10)

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
    tree = ttk.Treeview(root, columns=columns, show="headings", height=15)

    for col in columns:
        tree.heading(col, text=headers_vn[col])
        tree.column(col, anchor="center", width=120)

    tree.pack(fill="both", expand=True, padx=10, pady=10)


    def load_data(keyword=None):
        """Tải danh sách nhân viên, hỗ trợ tìm kiếm theo nhiều cột"""
        for item in tree.get_children():
            tree.delete(item)

        # Chuẩn bị câu truy vấn cơ bản
        query = """
            SELECT MaNV, HoTen, GioiTinh, NgaySinh, ChucVu, LuongCoBan, TrangThai
            FROM NhanVien
        """
        params = ()

        # Nếu có từ khóa, tìm ở nhiều cột (không phân biệt hoa/thường)
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

                # Highlight dòng chứa từ khóa
                if keyword_lower and (
                    keyword_lower in manv.lower()
                    or keyword_lower in hoten.lower()
                    or keyword_lower in row.GioiTinh.lower()
                    or keyword_lower in chucvu.lower()
                    or keyword_lower in trangthai.lower()
                ):
                    tree.item(item_id, tags=("highlight",))

            tree.tag_configure("highlight", background="#fff3cd", font=("Arial", 11, "bold"))

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải dữ liệu: {e}")



    # ====== GẮN SỰ KIỆN TÌM KIẾM REALTIME ======
    def on_search_change(*args):
        keyword = search_var.get().strip()
        load_data(keyword)

    search_var.trace_add("write", on_search_change)

    load_data()


def add_employee(refresh):
    """Thêm nhân viên mới (có chọn ngày sinh bằng calendar + combobox chức vụ)"""
    win = tk.Toplevel()
    win.title("➕ Thêm nhân viên mới")
    win.geometry("430x500")
    win.resizable(False, False)
    win.configure(bg="#f8f9fa")

    form = tk.Frame(win, bg="#f8f9fa")
    form.pack(padx=20, pady=15, fill="both", expand=True)

    labels = ["Mã NV", "Họ tên", "Giới tính", "Ngày sinh",
              "Chức vụ", "Lương cơ bản", "Trạng thái"]
    entries = {}
    positions = ["Quản lý", "Thu ngân", "Phục vụ", "Pha chế", "Tạp vụ", "Bảo vệ"]
    statuses = ["Đang làm", "Tạm nghỉ", "Đào tạo", "Đã nghỉ"]

    for i, text in enumerate(labels):
        lbl = ttk.Label(form, text=text, font=("Arial", 11), background="#f8f9fa")
        lbl.grid(row=i, column=0, sticky="w", padx=8, pady=6)

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
            cb.set("Đang làm")  # mặc định
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

    btn_frame = tk.Frame(win, bg="#f8f9fa")
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="💾 Lưu nhân viên", command=lambda: submit()).pack(ipadx=10, ipady=5)

    def submit():
        try:
            manv = entries["Mã NV"].get().strip().upper()
            hoten = entries["Họ tên"].get().strip()
            gt = entries["Giới tính"].get()

            # --- Xử lý ngày sinh an toàn ---
            raw_ngs = None
            widget = entries["Ngày sinh"]
            try:
                raw_ngs = widget.get_date()
            except Exception:
                try:
                    raw_ngs = widget.get()
                except Exception:
                    raw_ngs = None

            try:
                ngs = normalize_date_input(raw_ngs)
            except ValueError as e:
                messagebox.showerror("Lỗi định dạng ngày", f"Ngày sinh không hợp lệ: {e}")
                return

            cv = entries["Chức vụ"].get().strip()
            luong = float(entries["Lương cơ bản"].get().strip() or 0)
            tt = entries["Trạng thái"].get().strip() or "Đang làm"

            # --- ✅ Tự động sinh mã NV nếu trống ---
            if not manv:
                from app.utils import generate_next_manv
                manv = generate_next_manv(db.cursor)

            # --- ✅ Kiểm tra trùng mã NV ---
            db.cursor.execute("SELECT COUNT(*) FROM NhanVien WHERE MaNV=?", (manv,))
            if db.cursor.fetchone()[0] > 0:
                messagebox.showwarning("⚠️ Trùng mã NV", f"Mã nhân viên {manv} đã tồn tại!")
                return

            # --- Lưu vào DB ---
            db.cursor.execute("""
                INSERT INTO NhanVien (MaNV, HoTen, GioiTinh, NgaySinh, ChucVu, LuongCoBan, TrangThai)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (manv, hoten, gt, ngs, cv, luong, tt))
            db.conn.commit()

            messagebox.showinfo("✅ Thành công", f"Đã thêm nhân viên {manv}!")
            refresh()
            win.destroy()

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm nhân viên: {e}")



def edit_employee(tree, refresh, role):
    """Sửa thông tin nhân viên (có chọn ngày sinh bằng calendar + combobox chức vụ)"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn nhân viên cần sửa!")
        return

    values = tree.item(selected[0])["values"]
    manv = values[0]

    win = tk.Toplevel()
    win.title(f"✏️ Sửa nhân viên {manv}")
    win.geometry("430x500")
    win.resizable(False, False)
    win.configure(bg="#f8f9fa")

    form = tk.Frame(win, bg="#f8f9fa")
    form.pack(padx=20, pady=15, fill="both", expand=True)

    labels = ["Họ tên", "Giới tính", "Ngày sinh",
              "Chức vụ", "Lương cơ bản", "Trạng thái"]
    entries = {}
    positions = ["Quản lý", "Thu ngân", "Phục vụ", "Pha chế", "Tạp vụ", "Bảo vệ"]
    statuses = ["Đang làm", "Tạm nghỉ", "Đào tạo", "Đã nghỉ"]

    # Xử lý ngày sinh định dạng dd/mm/yyyy -> datetime
    current = dict(zip(labels, values[1:]))
    if current["Ngày sinh"]:
        try:
            current["Ngày sinh"] = datetime.strptime(current["Ngày sinh"], "%d/%m/%Y").date()
        except:
            current["Ngày sinh"] = datetime.today().date()

    for i, text in enumerate(labels):
        lbl = ttk.Label(form, text=text, font=("Arial", 11), background="#f8f9fa")
        lbl.grid(row=i, column=0, sticky="w", padx=8, pady=6)

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

            state_mode = "readonly" if role == "Admin" else "disabled"
            cb = ttk.Combobox(form, values=statuses, state="readonly", font=("Arial", 11))
            # Nếu giá trị trong DB có thì hiển thị, không thì mặc định “Đang làm”
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
            entry = ttk.Entry(form, font=("Arial", 11))
            entry.insert(0, current[text])
            entry.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = entry

    form.grid_columnconfigure(1, weight=1)

    btn_frame = tk.Frame(win, bg="#f8f9fa")
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="💾 Lưu thay đổi", command=lambda: save()).pack(ipadx=10, ipady=5)

    def save():
        try:
            hoten = entries["Họ tên"].get().strip()
            gt = entries["Giới tính"].get().strip()
            #
            raw_ngs = None
            widget = entries["Ngày sinh"]
            try:
                raw_ngs = widget.get_date()
            except Exception:
                try:
                    raw_ngs = widget.get()
                except Exception:
                    raw_ngs = None

            try:
                ngs = normalize_date_input(raw_ngs)
            except ValueError as e:
                messagebox.showerror("Lỗi định dạng ngày", f"Ngày sinh không hợp lệ: {e}")
                return
            #
            cv = entries["Chức vụ"].get().strip()
            luong = float(entries["Lương cơ bản"].get().replace(",", "").strip() or 0)
            tt = entries["Trạng thái"].get().strip()

            if not hoten:
                messagebox.showwarning("Thiếu thông tin", "⚠️ Họ tên không được để trống.")
                return

            db.cursor.execute("""
                UPDATE NhanVien
                SET HoTen=?, GioiTinh=?, NgaySinh=?, ChucVu=?, LuongCoBan=?, TrangThai=?
                WHERE MaNV=?
            """, (hoten, gt, ngs, cv, luong, tt, manv))
            db.conn.commit()

            messagebox.showinfo("✅ Thành công", f"Đã cập nhật nhân viên {manv}.")
            refresh()
            win.destroy()

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể cập nhật nhân viên: {e}")


def delete_employee(tree, refresh):
    """Xóa nhân viên"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Chưa chọn", "Vui lòng chọn nhân viên cần xóa!")
        return

    values = tree.item(selected[0])["values"]
    manv = values[0]

    if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa nhân viên {manv}?"):
        try:
            db.cursor.execute("DELETE FROM NhanVien WHERE MaNV=?", (manv,))
            db.conn.commit()
            messagebox.showinfo("Thành công", "Đã xóa nhân viên.")
            refresh()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xóa: {e}")


def go_back(root, username, role):
    """Quay lại main menu"""
    from app.ui.mainmenu_frame import show_main_menu
    show_main_menu(root, username, role)
