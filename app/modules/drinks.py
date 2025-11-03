# app/modules/drinks.py
import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation
from app import db
from app.db import execute_query
from app.theme import setup_styles
from app.utils.utils import create_form_window
from app.utils.business_helpers import safe_delete
from app.utils.id_helpers import generate_next_masp

def create_drinks_module(parent_frame, on_back_callback):
    """Tạo giao diện module Quản lý Sản phẩm / Đồ uống."""
    
    setup_styles()

    module_frame = tk.Frame(parent_frame, bg="#f5e6ca")
    
    # --- Header ---
    header = tk.Frame(module_frame, bg="#4b2e05", height=70)
    header.pack(fill="x")
    tk.Label(header, text="☕ QUẢN LÝ SẢN PHẨM / ĐỒ UỐNG",
             bg="#4b2e05", fg="white", font=("Segoe UI", 16, "bold")).pack(pady=12)

    # --- Khung Chức năng ---
    top = tk.Frame(module_frame, bg="#f5e6ca")
    top.pack(fill="x", pady=8, padx=12)

    search_var = tk.StringVar()
    tk.Label(top, text="🔎 Tìm:", bg="#f5e6ca", font=("Arial", 11)).pack(side="left", padx=(0,6))
    entry_search = ttk.Entry(top, textvariable=search_var, width=30)
    entry_search.pack(side="left", padx=(0,6))

    status_label_var = tk.StringVar(value="")
    status_label = ttk.Label(top, textvariable=status_label_var, 
                             font=("Arial", 10, "italic"), 
                             background="#f5e6ca", foreground="blue")
    status_label.pack(side="left", padx=10, pady=5)

    # --- Treeview ---
    columns = ("MaSP", "TenSP", "LoaiSP", "DonGia", "TrangThai")
    tree = ttk.Treeview(module_frame, columns=columns, show="headings", height=16)
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

    def load_data(keyword=None):
        """Tải và hiển thị dữ liệu sản phẩm."""
        status_label_var.set("Đang tải dữ liệu...")
        tree.update_idletasks() 

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

            status_label_var.set(f"Đã tải {len(rows)} sản phẩm.")
        except Exception as e:
            status_label_var.set("Lỗi tải dữ liệu!")
            messagebox.showerror("Lỗi", f"Không thể tải dữ liệu: {e}")

    # --- Nút thanh công cụ ---
    ttk.Button(top, text="🔄 Tải lại", style="Close.TButton",
             command=load_data).pack(side="left", padx=5)
    ttk.Button(top, text="➕ Thêm", style="Add.TButton",
             command=lambda: add_drink(load_data)).pack(side="left", padx=5)
    ttk.Button(top, text="✏️ Sửa", style="Edit.TButton",
             command=lambda: edit_drink(tree, load_data)).pack(side="left", padx=5)
    ttk.Button(top, text="🗑 Xóa", style="Delete.TButton",
             command=lambda: delete_drink(tree, load_data)).pack(side="left", padx=5)
    ttk.Button(top, text="⬅ Quay lại", style="Close.TButton",
             command=on_back_callback).pack(side="right", padx=5)

    load_data()

    # --- Gán sự kiện ---
    search_after_id = {"id": None}
    def on_search_change(event=None):
        """Hàm debounce cho tìm kiếm"""
        if search_after_id["id"]:
            module_frame.after_cancel(search_after_id["id"])
        search_after_id["id"] = module_frame.after(250, lambda: load_data(search_var.get().strip()))
    entry_search.bind("<KeyRelease>", on_search_change)

    def on_double_click(event):
        """Sửa khi double click"""
        sel = tree.selection()
        if sel:
            edit_drink(tree, load_data)
    tree.bind("<Double-1>", on_double_click)

    def refresh():
        load_data()
        
    return module_frame


# ================================================
# CÁC HÀM CRUD (POP-UP)
# ================================================

def add_drink(refresh):
    """Mở cửa sổ pop-up để thêm sản phẩm / đồ uống mới."""
    win, form = create_form_window("➕ Thêm sản phẩm", size="460x400")
    entries = {}

    labels = ["Mã SP", "Tên sản phẩm", "Loại", "Đơn giá", "Trạng thái"]
    types = ["Cà phê", "Trà sữa", "Sinh tố", "Nước ngọt", "Khác"]
    statuses = ["Còn bán", "Hết hàng", "Ngưng bán"]

    for i, text in enumerate(labels):
        ttk.Label(form, text=text, font=("Arial", 11), background="#f8f9fa")\
            .grid(row=i, column=0, sticky="w", padx=8, pady=8)

        if text == "Loại":
            cb = ttk.Combobox(form, values=types, state="readonly", font=("Arial", 11))
            cb.current(0)
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

    btn_frame = tk.Frame(win, bg="#f8f9fa")
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="💾 Lưu sản phẩm", style="Add.TButton",
             command=lambda: submit()).pack(ipadx=10, ipady=6)

    def submit():
        try:
            ma = entries["Mã SP"].get().strip().upper()
            ten = entries["Tên sản phẩm"].get().strip()
            loai = entries["Loại"].get().strip()
            gia_raw = entries["Đơn giá"].get().strip().replace(",", "")
            trangthai = entries["Trạng thái"].get().strip()

            if not ten:
                messagebox.showwarning("Thiếu thông tin", "⚠️ Tên sản phẩm không được để trống.", parent=win)
                return
            try:
                gia = Decimal(gia_raw) if gia_raw != "" else Decimal(0)
                if gia < 0:
                    raise InvalidOperation("Giá phải >= 0")
            except Exception:
                messagebox.showwarning("Lỗi", "Đơn giá không hợp lệ. Vui lòng nhập số dương.", parent=win)
                return

            if not ma:
                ma = generate_next_masp(db.cursor)

            db.cursor.execute("SELECT COUNT(*) FROM SANPHAM WHERE MaSP=?", (ma,))
            if db.cursor.fetchone()[0] > 0:
                messagebox.showwarning("Trùng mã", f"⚠️ Mã sản phẩm {ma} đã tồn tại.", parent=win)
                return

            query = """
                INSERT INTO SANPHAM (MaSP, TenSP, LoaiSP, DonGia, TrangThai)
                VALUES (?, ?, ?, ?, ?)
            """
            params = (ma, ten, loai, float(gia), trangthai)

            if execute_query(query, params):
                messagebox.showinfo("✅ Thành công", f"Đã thêm sản phẩm {ma} - {ten}.", parent=win)
                refresh()
                win.destroy()

        except Exception as e:
            db.conn.rollback()
            messagebox.showerror("Lỗi", f"Không thể thêm sản phẩm: {e}", parent=win)


def edit_drink(tree, refresh):
    """Mở cửa sổ pop-up để sửa sản phẩm."""
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Chưa chọn", "Vui lòng chọn sản phẩm cần sửa.")
        return

    ma = sel[0] 

    db.cursor.execute("SELECT MaSP, TenSP, LoaiSP, DonGia, TrangThai FROM SANPHAM WHERE MaSP=?", (ma,))
    row = db.cursor.fetchone()
    if not row:
        messagebox.showerror("Lỗi", "Không tìm thấy sản phẩm trong cơ sở dữ liệu.")
        return

    win, form = create_form_window(f"✏️ Sửa sản phẩm {ma}", "460x400")

    labels = ["Tên sản phẩm", "Loại", "Đơn giá", "Trạng thái"]
    entries = {}
    types = ["Cà phê", "Trà sữa", "Sinh tố", "Nước ngọt", "Đồ ăn vặt", "Trà", "Trà trái cây", "Nước ép", "Khác"]
    statuses = ["Còn bán", "Hết hàng", "Ngưng bán"]

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
        else: # Tên sản phẩm
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
                messagebox.showwarning("Thiếu thông tin", "Tên sản phẩm không được để trống.", parent=win)
                return

            try:
                gia = Decimal(gia_raw) if gia_raw!="" else Decimal(0)
                if gia < 0:
                    raise InvalidOperation()
            except Exception:
                messagebox.showwarning("Lỗi", "Đơn giá không hợp lệ.", parent=win)
                return

            query = """
                UPDATE SANPHAM
                SET TenSP=?, LoaiSP=?, DonGia=?, TrangThai=?
                WHERE MaSP=?
            """
            params = (ten, loai, float(gia), trangthai, ma)

            if execute_query(query, params):
                messagebox.showinfo("Thành công", f"Đã cập nhật {ma}", parent=win)
                win.destroy()
                refresh()
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể cập nhật sản phẩm: {e}", parent=win)

    ttk.Button(btnf, text="💾 Lưu", style="Add.TButton", command=save).pack(ipadx=10, ipady=6)


def delete_drink(tree, refresh):
    """Xóa sản phẩm đã chọn."""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn sản phẩm cần xóa!")
        return

    ma = selected[0] 

    safe_delete(
        table_name="SanPham",
        key_column="MaSP",
        key_value=ma,
        cursor=db.cursor,
        conn=db.conn,
        refresh_func=refresh,
        item_label="sản phẩm"
    )