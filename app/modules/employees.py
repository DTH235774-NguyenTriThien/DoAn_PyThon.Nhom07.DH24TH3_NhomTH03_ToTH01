import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from app import db
from app.utils import clear_window


def show_employee_module(root, username=None, role=None):
    """Giao diện quản lý nhân viên (phiên bản frame-based)"""
    clear_window(root)
    root.title("Quản lý nhân viên")

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
    ttk.Button(top_frame, text="✏️ Sửa", command=lambda: edit_employee(tree, load_data)).pack(side="left", padx=5)
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
    """Thêm nhân viên mới (đẹp, căn chỉnh chuẩn, có combobox chức vụ)"""
    win = tk.Toplevel()
    win.title("➕ Thêm nhân viên mới")
    win.geometry("430x480")
    win.resizable(False, False)
    win.configure(bg="#f8f9fa")

    # ====== FRAME CHÍNH ======
    form = tk.Frame(win, bg="#f8f9fa")
    form.pack(padx=20, pady=15, fill="both", expand=True)

    # Danh sách nhãn và trường
    labels = ["Mã NV", "Họ tên", "Giới tính", "Ngày sinh (YYYY-MM-DD)",
              "Chức vụ", "Lương cơ bản", "Trạng thái"]
    entries = {}

    # Danh sách chức vụ
    positions = ["Quản lý", "Thu ngân", "Phục vụ", "Pha chế", "Tạp vụ", "Bảo vệ"]

    for i, text in enumerate(labels):
        lbl = ttk.Label(form, text=text, font=("Arial", 11), background="#f8f9fa")
        lbl.grid(row=i, column=0, sticky="w", padx=8, pady=6)

        # Ô nhập liệu hoặc combobox
        if text == "Chức vụ":
            cb = ttk.Combobox(form, values=positions, state="readonly", font=("Arial", 11))
            cb.current(1)  # Mặc định là Thu ngân
            cb.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = cb
        else:
            entry = ttk.Entry(form, font=("Arial", 11))
            entry.grid(row=i, column=1, padx=8, pady=6, sticky="ew")
            entries[text] = entry

    # Cho phép cột 1 (textbox) mở rộng linh hoạt
    form.grid_columnconfigure(1, weight=1)

    # ====== NÚT LƯU ======
    btn_frame = tk.Frame(win, bg="#f8f9fa")
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="💾 Lưu nhân viên", command=lambda: submit()).pack(ipadx=10, ipady=5)

    # ====== HÀM XỬ LÝ LƯU ======
    def submit():
        try:
            manv = entries["Mã NV"].get().strip()
            hoten = entries["Họ tên"].get().strip()
            gt = entries["Giới tính"].get().strip()
            ngs = entries["Ngày sinh (YYYY-MM-DD)"].get().strip()
            cv = entries["Chức vụ"].get().strip()
            luong = float(entries["Lương cơ bản"].get().strip() or 0)
            tt = entries["Trạng thái"].get().strip() or "Đang làm"

            if not manv or not hoten:
                messagebox.showwarning("Thiếu thông tin", "⚠️ Mã NV và Họ tên là bắt buộc.")
                return

            if ngs:
                ngs = datetime.strptime(ngs, "%Y-%m-%d").date()

            db.cursor.execute("""
                INSERT INTO NhanVien (MaNV, HoTen, GioiTinh, NgaySinh, ChucVu, LuongCoBan, TrangThai)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (manv, hoten, gt, ngs, cv, luong, tt))
            db.conn.commit()

            messagebox.showinfo("✅ Thành công", "Đã thêm nhân viên mới!")
            refresh()
            win.destroy()

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm nhân viên: {e}")


def edit_employee(tree, refresh):
    """Sửa thông tin nhân viên"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Chưa chọn", "Vui lòng chọn nhân viên cần sửa!")
        return

    values = tree.item(selected[0])["values"]
    manv = values[0]

    win = tk.Toplevel()
    win.title(f"Sửa nhân viên {manv}")
    win.geometry("400x400")

    labels = ["Họ tên", "Giới tính", "Ngày sinh (YYYY-MM-DD)",
              "Chức vụ", "Lương cơ bản", "Trạng thái"]
    entries = {}
    current = dict(zip(labels, values[1:]))

    for i, text in enumerate(labels):
        ttk.Label(win, text=text).grid(row=i, column=0, padx=10, pady=5, sticky="w")
        entry = ttk.Entry(win, width=30)
        entry.grid(row=i, column=1, padx=10, pady=5)

        if text == "Ngày sinh (YYYY-MM-DD)" and current[text]:
            try:
                # chuyển từ dd/mm/yyyy sang yyyy-mm-dd khi mở form sửa
                current[text] = datetime.strptime(current[text], "%d/%m/%Y").strftime("%Y-%m-%d")
            except:
                pass

        entry.insert(0, current[text])
        entries[text] = entry

    def save():
        try:
            hoten = entries["Họ tên"].get().strip()
            gt = entries["Giới tính"].get().strip()
            ngs = entries["Ngày sinh (YYYY-MM-DD)"].get().strip()
            cv = entries["Chức vụ"].get().strip()
            luong = float(entries["Lương cơ bản"].get().replace(",", "").strip() or 0)
            tt = entries["Trạng thái"].get().strip()

            if ngs:
                ngs = datetime.strptime(ngs, "%Y-%m-%d").date()
            else:
                ngs = None

            db.cursor.execute("""
                UPDATE NhanVien
                SET HoTen=?, GioiTinh=?, NgaySinh=?, ChucVu=?, LuongCoBan=?, TrangThai=?
                WHERE MaNV=?
            """, (hoten, gt, ngs, cv, luong, tt, manv))
            db.conn.commit()
            messagebox.showinfo("Thành công", "Cập nhật thông tin thành công!")
            win.destroy()
            refresh()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể cập nhật: {e}")

    ttk.Button(win, text="Lưu", command=save).grid(row=len(labels), column=0, columnspan=2, pady=10)


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
