# app/modules/drinks.py
import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation
from app import db
from app.utils import clear_window, generate_next_masp

def show_drinks_module(root, username=None, role=None):

    clear_window(root)
    root.title("Quản lý đồ uống - SANPHAM")
    root.configure(bg="#f5e6ca")  # hoặc theme của bạn

    window_width = 1200
    window_height = 600
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width / 2) - (window_width / 2))
    y = int((screen_height / 2) - (window_height / 2))
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    root.minsize(1000, 550)

    # Header
    header = tk.Frame(root, bg="#4b2e05", height=70)
    header.pack(fill="x")
    tk.Label(header, text="☕ QUẢN LÝ SẢN PHẨM / ĐỒ UỐNG",
             bg="#4b2e05", fg="white", font=("Segoe UI", 16, "bold")).pack(pady=12)

    # Top controls
    top = tk.Frame(root, bg="#f5e6ca")
    top.pack(fill="x", pady=8, padx=12)

    search_var = tk.StringVar()
    tk.Label(top, text="🔎 Tìm:", bg="#f5e6ca", font=("Arial", 11)).pack(side="left", padx=(0,6))
    entry_search = ttk.Entry(top, textvariable=search_var, width=30)
    entry_search.pack(side="left", padx=(0,6))

    # Real-time search debounce
    search_after_id = {"id": None}
    def schedule_search(event=None):
        if search_after_id["id"]:
            root.after_cancel(search_after_id["id"])
        search_after_id["id"] = root.after(250, lambda: load_data(search_var.get().strip()))

    entry_search.bind("<KeyRelease>", schedule_search)

    #ttk.Button(top, text="Tải lại", command=lambda: load_data()).pack(side="left", padx=6)
    #ttk.Button(top, text="➕ Thêm", command=lambda: add_drink(load_data)).pack(side="left", padx=6)
    #ttk.Button(top, text="✏️ Sửa", command=lambda: edit_drink(tree, load_data, role)).pack(side="left", padx=6)
    #ttk.Button(top, text="🗑️ Xóa", command=lambda: delete_drink(tree, load_data)).pack(side="left", padx=6)
    #ttk.Button(top, text="⬅ Quay lại", command=lambda: go_back(root, username, role)).pack(side="right", padx=6)

    # Treeview
    columns = ("MaSP", "TenSP", "LoaiSP", "DonGia", "TrangThai")
    tree = ttk.Treeview(root, columns=columns, show="headings", height=16)
    headers_vn = {
        "MaSP": "Mã SP",
        "TenSP": "Tên sản phẩm",
        "LoaiSP": "Loại",
        "DonGia": "Đơn giá (đ)",
        "TrangThai": "Trạng thái"
    }
    for col in columns:
        tree.heading(col, text=headers_vn[col])
        tree.column(col, anchor="center", width=140 if col!="TenSP" else 260)
    tree.pack(fill="both", expand=True, padx=12, pady=(4,12))

    # Load data function
    def load_data(keyword=None):
        try:
            for i in tree.get_children():
                tree.delete(i)
            sql = "SELECT MaSP, TenSP, LoaiSP, DonGia, TrangThai FROM SANPHAM"
            params = ()
            if keyword:
                sql += " WHERE MaSP LIKE ? OR TenSP LIKE ? OR LoaiSP LIKE ? OR TrangThai LIKE ?"
                kw = f"%{keyword}%"
                params = (kw, kw, kw, kw)
                db.cursor.execute(sql, params)
            else:
                db.cursor.execute(sql)
            rows = db.cursor.fetchall()
            for row in rows:
                ma = row.MaSP.strip()
                ten = row.TenSP
                loai = row.LoaiSP or ""
                try:
                    gia = f"{int(row.DonGia):,}"
                except Exception:
                    gia = str(row.DonGia)
                tt = row.TrangThai or ""
                tree.insert("", "end", values=(ma, ten, loai, gia, tt))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải dữ liệu: {e}")


    # Button on top frame 
    
    ttk.Button(top, text="🔄 Tải lại", style="Close.TButton",
               command=load_data).pack(side="left", padx=5)
    ttk.Button(top, text="➕ Thêm", style="Add.TButton",
               command=lambda: add_drink(load_data)).pack(side="left", padx=5)
    ttk.Button(top, text="✏️ Sửa", style="Edit.TButton",
               command=lambda: edit_drink(tree, load_data, role)).pack(side="left", padx=5)
    ttk.Button(top, text="🗑 Xóa", style="Delete.TButton",
               command=lambda: delete_drink(tree, load_data)).pack(side="left", padx=5)
    ttk.Button(top, text="⬅ Quay lại", style="Close.TButton",
           command=lambda: go_back(root, username, role)).pack(side="right", padx=5)


    load_data()

    # Double-click to edit
    def on_double_click(event):
        sel = tree.selection()
        if sel:
            edit_drink(tree, load_data, role)
    tree.bind("<Double-1>", on_double_click)


def add_drink(refresh):
    """Form thêm sản phẩm / đồ uống"""
    win = tk.Toplevel()
    win.title("➕ Thêm sản phẩm")
    win.geometry("480x380")
    win.resizable(False, False)
    win.configure(bg="#f8f9fa")

    form = tk.Frame(win, bg="#f8f9fa")
    form.pack(padx=12, pady=12, fill="both", expand=True)

    labels = ["Mã SP", "Tên sản phẩm", "Loại", "Đơn giá", "Trạng thái"]
    entries = {}
    types = ["Cà phê", "Trà sữa", "Sinh tố", "Nước ngọt", "Khác"]
    statuses = ["Có hàng", "Hết hàng", "Ngưng bán"]

    for i, text in enumerate(labels):
        ttk.Label(form, text=text, font=("Arial", 11), background="#f8f9fa").grid(row=i, column=0, sticky="w", padx=8, pady=8)
        if text == "Loại":
            cb = ttk.Combobox(form, values=types, state="readonly", font=("Arial", 11))
            cb.set(types[0])
            cb.grid(row=i, column=1, padx=8, pady=8, sticky="ew")
            entries[text] = cb
        elif text == "Trạng thái":
            cb = ttk.Combobox(form, values=statuses, state="readonly", font=("Arial", 11))
            cb.set(statuses[0])
            cb.grid(row=i, column=1, padx=8, pady=8, sticky="ew")
            entries[text] = cb
        else:
            ent = ttk.Entry(form, font=("Arial", 11))
            ent.grid(row=i, column=1, padx=8, pady=8, sticky="ew")
            entries[text] = ent

    form.grid_columnconfigure(1, weight=1)

    btnf = tk.Frame(win, bg="#f8f9fa")
    btnf.pack(pady=8)

    def submit():
        try:
            ma = entries["Mã SP"].get().strip().upper()
            ten = entries["Tên sản phẩm"].get().strip()
            loai = entries["Loại"].get().strip()
            gia_raw = entries["Đơn giá"].get().strip().replace(",", "")
            trangthai = entries["Trạng thái"].get().strip()

            if not ten:
                messagebox.showwarning("Thiếu thông tin", "Tên sản phẩm không được để trống.")
                return

            # Giá kiểm tra số
            try:
                gia = Decimal(gia_raw) if gia_raw!="" else Decimal(0)
                if gia < 0:
                    raise InvalidOperation("Giá phải >= 0")
            except Exception:
                messagebox.showwarning("Lỗi", "Đơn giá không hợp lệ. Vui lòng nhập số.")
                return

            # Sinh mã nếu bỏ trống
            if not ma:
                ma = generate_next_masp(db.cursor)

            # Kiểm tra trùng
            db.cursor.execute("SELECT COUNT(*) FROM SANPHAM WHERE MaSP=?", (ma,))
            if db.cursor.fetchone()[0] > 0:
                messagebox.showwarning("Trùng mã", f"Mã sản phẩm {ma} đã tồn tại.")
                return

            # Insert
            db.cursor.execute("""
                INSERT INTO SANPHAM (MaSP, TenSP, LoaiSP, DonGia, TrangThai)
                VALUES (?, ?, ?, ?, ?)
            """, (ma, ten, loai, float(gia), trangthai))
            db.conn.commit()
            messagebox.showinfo("Thành công", f"Đã thêm {ma} - {ten}")
            refresh()
            win.destroy()

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm sản phẩm: {e}")

    ttk.Button(btnf, text="💾 Lưu", command=submit).pack(ipadx=10, ipady=6)


def edit_drink(tree, refresh, role=None):
    """Sửa sản phẩm (đồng bộ giao diện với add)"""
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Chưa chọn", "Vui lòng chọn sản phẩm cần sửa.")
        return

    values = tree.item(sel[0])["values"]
    ma = values[0]

    # Lấy dữ liệu từ DB chính xác (ở dạng đầy đủ)
    db.cursor.execute("SELECT MaSP, TenSP, LoaiSP, DonGia, TrangThai FROM SANPHAM WHERE MaSP=?", (ma,))
    row = db.cursor.fetchone()
    if not row:
        messagebox.showerror("Lỗi", "Không tìm thấy sản phẩm trong cơ sở dữ liệu.")
        return

    win = tk.Toplevel()
    win.title(f"✏️ Sửa sản phẩm {ma}")
    win.geometry("480x380")
    win.resizable(False, False)
    win.configure(bg="#f8f9fa")

    form = tk.Frame(win, bg="#f8f9fa")
    form.pack(padx=12, pady=12, fill="both", expand=True)

    labels = ["Tên sản phẩm", "Loại", "Đơn giá", "Trạng thái"]
    entries = {}
    types = ["Cà phê", "Trà sữa", "Sinh tố", "Nước ngọt", "Khác"]
    statuses = ["Có hàng", "Hết hàng", "Ngưng bán"]

    # current data
    current = {
        "Ten sản phẩm": row.TenSP,
        "Ten sản phẩm?": row.TenSP  
    }

    # Build fields
    for i, text in enumerate(labels):
        ttk.Label(form, text=text, font=("Arial", 11), background="#f8f9fa").grid(row=i, column=0, sticky="w", padx=8, pady=8)
        if text == "Loại":
            cb = ttk.Combobox(form, values=types, state="readonly", font=("Arial", 11))
            cb.set(row.LoaiSP or types[0])
            cb.grid(row=i, column=1, padx=8, pady=8, sticky="ew")
            entries[text] = cb
        elif text == "Trạng thái":
            cb = ttk.Combobox(form, values=statuses, state="readonly", font=("Arial", 11))
            cb.set(row.TrangThai or statuses[0])
            cb.grid(row=i, column=1, padx=8, pady=8, sticky="ew")
            entries[text] = cb
        elif text == "Đơn giá":
            ent = ttk.Entry(form, font=("Arial", 11))
            ent.insert(0, f"{int(row.DonGia):,}")
            ent.grid(row=i, column=1, padx=8, pady=8, sticky="ew")
            entries[text] = ent
        else:  # Tên sản phẩm
            ent = ttk.Entry(form, font=("Arial", 11))
            ent.insert(0, row.TenSP)
            ent.grid(row=i, column=1, padx=8, pady=8, sticky="ew")
            entries[text] = ent

    form.grid_columnconfigure(1, weight=1)

    btnf = tk.Frame(win, bg="#f8f9fa")
    btnf.pack(pady=8)

    def save():
        try:
            ten = entries["Tên sản phẩm"].get().strip()
            loai = entries["Loại"].get().strip()
            gia_raw = entries["Đơn giá"].get().strip().replace(",", "")
            trangthai = entries["Trạng thái"].get().strip()

            if not ten:
                messagebox.showwarning("Thiếu thông tin", "Tên sản phẩm không được để trống.")
                return

            try:
                gia = Decimal(gia_raw) if gia_raw!="" else Decimal(0)
                if gia < 0:
                    raise InvalidOperation()
            except Exception:
                messagebox.showwarning("Lỗi", "Đơn giá không hợp lệ.")
                return

            db.cursor.execute("""
                UPDATE SANPHAM
                SET TenSP=?, LoaiSP=?, DonGia=?, TrangThai=?
                WHERE MaSP=?
            """, (ten, loai, float(gia), trangthai, ma))
            db.conn.commit()
            messagebox.showinfo("Thành công", f"Đã cập nhật {ma}")
            refresh()
            win.destroy()

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể cập nhật sản phẩm: {e}")

    ttk.Button(btnf, text="💾 Lưu", command=save).pack(ipadx=10, ipady=6)


def delete_drink(tree, refresh):
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn sản phẩm cần xóa!")
        return

    values = tree.item(selected[0])["values"]
    masp = values[0]

    from app.utils import safe_delete
    safe_delete(
        table_name="SanPham",
        key_column="MaSP",
        key_value=masp,
        cursor=db.cursor,
        conn=db.conn,
        refresh_func=refresh,
        item_label="sản phẩm"
    )


def go_back(root, username, role):
    from app.ui.mainmenu_frame import show_main_menu
    show_main_menu(root, username, role)
