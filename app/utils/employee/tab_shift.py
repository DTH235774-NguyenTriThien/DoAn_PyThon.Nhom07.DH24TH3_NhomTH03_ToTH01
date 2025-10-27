import tkinter as tk
from tkinter import ttk, messagebox
from app import db
from app.theme import setup_styles
from app.utils.utils import safe_delete, go_back, parse_time, validate_shift_time, generate_next_maca
from datetime import datetime, time

def build_tab(parent, root=None, username=None, role=None):
    """Tab Ca làm việc — Quản lý danh sách ca và CRUD cơ bản"""
    setup_styles()
    parent.configure(bg="#f5e6ca")

    # ===== THANH CÔNG CỤ =====
    top_frame = tk.Frame(parent, bg="#f9fafb")
    top_frame.pack(fill="x", pady=10)

    search_var = tk.StringVar()
    tk.Label(top_frame, text="🔎 Tìm ca làm:", font=("Arial", 11),
             bg="#f9fafb").pack(side="left", padx=5)
    entry_search = ttk.Entry(top_frame, textvariable=search_var, width=35)
    entry_search.pack(side="left", padx=5)

    # ===== TREEVIEW =====
    columns = ["MaCa", "TenCa", "GioBatDau", "GioKetThuc"]
    headers = {"MaCa": "Mã Ca", "TenCa": "Tên Ca", "GioBatDau": "Giờ Bắt đầu", "GioKetThuc": "Giờ Kết thúc"}

    tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)
    for col in columns:
        tree.heading(col, text=headers[col])
        tree.column(col, anchor="center", width=180)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    # ===== HÀM LOAD DATA =====
    def load_data(keyword=None):
        """Tải danh sách ca làm, hỗ trợ tìm kiếm theo mã, tên, giờ"""
        for item in tree.get_children():
            tree.delete(item)

        query = """
            SELECT MaCa, TenCa, GioBatDau, GioKetThuc
            FROM CaLam
        """
        params = ()
        if keyword and keyword.strip() != "":
            kw = f"%{keyword.strip()}%"
            query += """
                WHERE CAST(MaCa AS NVARCHAR(10)) LIKE ?
                   OR TenCa LIKE ?
                   OR FORMAT(GioBatDau, 'HH:mm') LIKE ?
                   OR FORMAT(GioKetThuc, 'HH:mm') LIKE ?
            """
            params = (kw, kw, kw, kw)

        try:
            db.cursor.execute(query, params)
            rows = db.cursor.fetchall()

            for row in rows:
                tree.insert("", "end", values=[
                    row.MaCa,
                    row.TenCa or "",
                    row.GioBatDau.strftime("%H:%M") if row.GioBatDau else "",
                    row.GioKetThuc.strftime("%H:%M") if row.GioKetThuc else ""
                ])
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải dữ liệu ca làm: {e}")

    load_data()

    # ===== CÁC NÚT CHỨC NĂNG =====
    ttk.Button(top_frame, text="🔄 Tải lại", style="Close.TButton",
               command=load_data).pack(side="left", padx=5)
    ttk.Button(top_frame, text="➕ Thêm", style="Add.TButton",
               command=lambda: add_shift(load_data)).pack(side="left", padx=5)
    ttk.Button(top_frame, text="✏️ Sửa", style="Edit.TButton",
               command=lambda: edit_shift(tree, load_data)).pack(side="left", padx=5)
    ttk.Button(top_frame, text="🗑 Xóa", style="Delete.TButton",
               command=lambda: delete_shift(tree, load_data)).pack(side="left", padx=5)
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
            edit_shift(tree, load_data)
    tree.bind("<Double-1>", on_double_click)

# ==============================================================
#  HÀM CRUD
# ==============================================================
from tkinter import messagebox, ttk
import tkinter as tk
from app import db
from app.utils.utils import parse_time  # dùng helper chuẩn của bạn

def add_shift(refresh):
    """Thêm ca làm mới — đồng bộ với edit_shift (có auto-fill giờ và combobox)"""
    win = tk.Toplevel()
    win.title("➕ Thêm ca làm")
    win.geometry("420x320")
    win.configure(bg="#f8f9fa")

    form = tk.Frame(win, bg="#f8f9fa")
    form.pack(padx=20, pady=15, fill="both", expand=True)

    # === Tên ca ===
    ttk.Label(form, text="Tên Ca", font=("Arial", 11),
              background="#f8f9fa").grid(row=0, column=0, sticky="w", padx=8, pady=6)
    ca_options = ["Sáng", "Chiều", "Tối", "Khác"]
    ca_var = tk.StringVar(value="Sáng")
    cb_tenca = ttk.Combobox(form, values=ca_options, textvariable=ca_var, font=("Arial", 11))
    cb_tenca.grid(row=0, column=1, padx=8, pady=6, sticky="ew")

    # === Giờ bắt đầu / kết thúc ===
    ttk.Label(form, text="Giờ Bắt đầu", font=("Arial", 11),
              background="#f8f9fa").grid(row=1, column=0, sticky="w", padx=8, pady=6)
    ttk.Label(form, text="Giờ Kết thúc", font=("Arial", 11),
              background="#f8f9fa").grid(row=2, column=0, sticky="w", padx=8, pady=6)

    time_options = [f"{h:02d}:00" for h in range(0, 24)]
    cb_batdau = ttk.Combobox(form, values=time_options, font=("Arial", 11))
    cb_ketthuc = ttk.Combobox(form, values=time_options, font=("Arial", 11))
    cb_batdau.grid(row=1, column=1, padx=8, pady=6, sticky="ew")
    cb_ketthuc.grid(row=2, column=1, padx=8, pady=6, sticky="ew")

    # === Auto fill khi chọn ca ===
    def auto_fill_time(event=None):
        ca = ca_var.get().lower()
        if ca == "sáng":
            cb_batdau.set("07:00")
            cb_ketthuc.set("11:00")
        elif ca == "chiều":
            cb_batdau.set("13:00")
            cb_ketthuc.set("17:00")
        elif ca == "tối":
            cb_batdau.set("17:00")
            cb_ketthuc.set("22:00")
        else:
            cb_batdau.set("")
            cb_ketthuc.set("")

    cb_tenca.bind("<<ComboboxSelected>>", auto_fill_time)
    auto_fill_time()  # auto-fill mặc định khi mở form

    # === Hàm lưu ===
    def submit():
        try:
            ten = cb_tenca.get().strip()
            bd = cb_batdau.get().strip()
            kt = cb_ketthuc.get().strip()

                
            # ===== GỌI HELPER tự động tạo mã ca ===== #
            maca = generate_next_maca(db.cursor)

            # ===== KIỂM TRA DỮ LIỆU =====
            if not ten:
                messagebox.showwarning("Thiếu thông tin", "⚠️ Tên ca không được để trống.", parent=win)
                return
            if not bd or not kt:
                messagebox.showwarning("Thiếu thông tin", "⚠️ Giờ bắt đầu và kết thúc không được để trống.", parent=win)
                return

            # ===== KIỂM TRA GIỜ HỢP LỆ (GỌI HELPER) =====
            if not validate_shift_time(bd, kt, exclude_maca=maca, parent=win, allow_partial_overlap=False):
                return

            # ===== THÊM VÀO DATABASE =====
            db.cursor.execute("""
                INSERT INTO CaLam (MaCa, TenCa, GioBatDau, GioKetThuc)
                VALUES (?, ?, ?, ?)
            """, (maca, ten, bd, kt))
            db.conn.commit()

            messagebox.showinfo("✅ Thành công", f"Đã thêm ca làm '{ten}'.", parent=win)
            win.destroy()
            refresh()

        except Exception as e:
            db.conn.rollback()
            messagebox.showerror("Lỗi", f"Không thể thêm ca làm: {e}", parent=win)


    ttk.Button(form, text="💾 Lưu ca làm", style="Add.TButton",
               command=submit).grid(row=4, column=0, columnspan=2, pady=15)

    form.grid_columnconfigure(1, weight=1)


def edit_shift(tree, refresh):
    """Sửa ca làm (có combobox giờ gợi ý và auto fill)"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn ca làm cần sửa!")
        return

    values = tree.item(selected[0])["values"]
    maca, tenca, giobd, giokt = values

    win = tk.Toplevel()
    win.title(f"✏️ Sửa ca làm {maca}")
    win.geometry("420x320")
    win.configure(bg="#f8f9fa")

    form = tk.Frame(win, bg="#f8f9fa")
    form.pack(padx=20, pady=15, fill="both", expand=True)

    ttk.Label(form, text=f"Mã Ca: {maca}", background="#f8f9fa",
              font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=6)

    # === Tên ca ===
    ttk.Label(form, text="Tên Ca", font=("Arial", 11),
              background="#f8f9fa").grid(row=1, column=0, sticky="w", padx=8, pady=6)
    ca_options = ["Sáng", "Chiều", "Tối", "Khác"]
    ca_var = tk.StringVar(value=tenca)
    cb_tenca = ttk.Combobox(form, values=ca_options, textvariable=ca_var, font=("Arial", 11))
    cb_tenca.grid(row=1, column=1, padx=8, pady=6, sticky="ew")

    # === Giờ bắt đầu / kết thúc ===
    ttk.Label(form, text="Giờ Bắt đầu", font=("Arial", 11),
              background="#f8f9fa").grid(row=2, column=0, sticky="w", padx=8, pady=6)
    ttk.Label(form, text="Giờ Kết thúc", font=("Arial", 11),
              background="#f8f9fa").grid(row=3, column=0, sticky="w", padx=8, pady=6)

    time_options = [f"{h:02d}:00" for h in range(0, 24)]
    cb_batdau = ttk.Combobox(form, values=time_options, font=("Arial", 11))
    cb_ketthuc = ttk.Combobox(form, values=time_options, font=("Arial", 11))
    cb_batdau.set(giobd)
    cb_ketthuc.set(giokt)
    cb_batdau.grid(row=2, column=1, padx=8, pady=6, sticky="ew")
    cb_ketthuc.grid(row=3, column=1, padx=8, pady=6, sticky="ew")

    # === Auto fill khi chọn ca ===
    def auto_fill_time(event=None):
        ca = ca_var.get().lower()
        if ca == "sáng":
            cb_batdau.set("07:00")
            cb_ketthuc.set("11:00")
        elif ca == "chiều":
            cb_batdau.set("13:00")
            cb_ketthuc.set("17:00")
        elif ca == "tối":
            cb_batdau.set("17:00")
            cb_ketthuc.set("22:00")

    cb_tenca.bind("<<ComboboxSelected>>", auto_fill_time)

    def save():
        try:
            ten = cb_tenca.get().strip()
            bd = cb_batdau.get().strip()
            kt = cb_ketthuc.get().strip()

            # ===== KIỂM TRA DỮ LIỆU =====
            if not ten:
                messagebox.showwarning("Thiếu thông tin", "⚠️ Tên ca không được để trống.", parent=win)
                return

            if not bd or not kt:
                messagebox.showwarning("Thiếu thông tin", "⚠️ Giờ bắt đầu và kết thúc không được để trống.", parent=win)
                return

            # ===== KIỂM TRA GIỜ HỢP LỆ =====
            if not validate_shift_time(bd, kt, exclude_maca=maca, parent=win):
                return

            # ===== CẬP NHẬT DATABASE =====
            db.cursor.execute("""
                UPDATE CaLam
                SET TenCa=?, GioBatDau=?, GioKetThuc=?
                WHERE MaCa=?
            """, (ten, bd, kt, maca))
            db.conn.commit()

            messagebox.showinfo("✅ Thành công", f"Đã cập nhật ca làm {maca}.", parent=win)
            refresh()
            win.destroy()

        except Exception as e:
            db.conn.rollback()
            messagebox.showerror("Lỗi", f"Không thể cập nhật ca làm: {e}", parent=win)
        

    ttk.Button(form, text="💾 Lưu thay đổi", style="Add.TButton",
               command=save).grid(row=5, column=0, columnspan=2, pady=15)


def delete_shift(tree, refresh):
    """Xóa bản ghi chấm công (sử dụng helper safe_delete)"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn bản ghi cần xóa!")
        return

    values = tree.item(selected[0])["values"]
    maca = values[0]  # cột đầu tiên luôn là Maca

    try:
        safe_delete(
            table_name="CaLam",
            key_column="MaCa",
            key_value=maca,
            cursor=db.cursor,
            conn=db.conn,
            refresh_func=refresh,
            item_label="ca làm"
        )
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể xóa Ca làm: {e}")
