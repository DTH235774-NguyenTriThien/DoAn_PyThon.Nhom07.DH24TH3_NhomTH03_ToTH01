# app/modules/invoices.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from decimal import Decimal, InvalidOperation
from datetime import datetime
from app import db
from app.utils.utils import clear_window, generate_next_mahd, recalc_invoice_total, safe_delete, create_form_window, go_back, center_window
from app.theme import setup_styles

# ---------- SHOW MAIN INVOICE MODULE ----------
def show_invoices_module(root, username=None, role=None):
    clear_window(root)
    setup_styles()
    root.title("Quản lý Hóa đơn")
    root.configure(bg="#f5e6ca")

    # ====== CẤU HÌNH FORM CHÍNH ======
    center_window(root, 1200, 700, offset_y=-60)
    root.minsize(1000, 550)

    header = tk.Frame(root, bg="#4b2e05", height=70)
    header.pack(fill="x")
    tk.Label(header, text="🧾 QUẢN LÝ HÓA ĐƠN", bg="#4b2e05", fg="white",
             font=("Segoe UI", 16, "bold")).pack(pady=12)

    top = tk.Frame(root, bg="#f5e6ca")
    top.pack(fill="x", pady=6, padx=12)


    search_var = tk.StringVar()
    ttk.Label(top, text="🔎 Tìm:", background="#f5e6ca").pack(side="left", padx=(0,6))
    entry_search = ttk.Entry(top, textvariable=search_var, width=30)
    entry_search.pack(side="left", padx=(0,6))

    # Treeview
    cols = ("MaHD", "NgayLap", "MaNV", "TenKH", "TongTien", "TrangThai", "GhiChu")
    tree = ttk.Treeview(root, columns=cols, show="headings", height=16)
    headers = {
    "MaHD": "Mã HD",
    "NgayLap": "Ngày lập",
    "MaNV": "Mã NV",
    "TenKH": "Khách hàng",
    "TongTien": "Tổng tiền (đ)",
    "TrangThai": "Trạng thái",
    "GhiChu": "Ghi Chú"
    }
    for c in cols:
        tree.heading(c, text=headers[c])
        tree.column(c, anchor="center", width=130 if c!="TongTien" else 160)
    tree.pack(fill="both", expand=True, padx=12, pady=(6,12))

    # load_data
    def load_data(keyword=None):
        try:
            for it in tree.get_children():
                tree.delete(it)
            sql = """
            SELECT h.MaHD, h.NgayLap, h.MaNV, k.TenKH, h.TongTien, h.TrangThai, h.GhiChu
            FROM HoaDon h
            LEFT JOIN KhachHang k ON h.MaKH = k.MaKH
            """
            params = ()
            if keyword:
                kw = f"%{keyword}%"
                sql += " WHERE MaHD LIKE ? OR MaNV LIKE ? OR TrangThai LIKE ?"
                params = (kw, kw, kw)
                db.cursor.execute(sql, params)
            else:
                db.cursor.execute(sql)
            rows = db.cursor.fetchall()
            for r in rows:
                ngay = r.NgayLap.strftime("%d/%m/%Y %H:%M") if r.NgayLap else ""
                tong = f"{int(r.TongTien):,}" if r.TongTien is not None else "0"
                tree.insert("", "end", values=(
                    r.MaHD.strip(),
                    ngay,
                    r.MaNV.strip(),
                    r.TenKH if r.TenKH else "",
                    tong,
                    r.TrangThai if r.TrangThai else "",
                    r.GhiChu if r.GhiChu else ""
                ))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách hóa đơn: {e}")

    # Buttons on top frame

    ttk.Button(top, text="🔄 Tải lại", style="Close.TButton",
               command=load_data).pack(side="left", padx=5)

    ttk.Button(top, text="➕ Thêm", style = "Add.TButton",
                command=lambda: add_invoice(root, username, refresh)).pack(side="left", padx=6)
    
    ttk.Button(top, text="✏️ Sửa", style="Edit.TButton",
                command=lambda: open_invoice_detail(tree, refresh, role)).pack(side="left", padx=6
                                                                               )
    
    ttk.Button(top, text="🗑 Xóa", style="Delete.TButton",
                command=lambda: delete_invoice(tree, refresh)).pack(side="left", padx=6)

    ttk.Button(top, text="⬅ Quay lại", style="Close.TButton",
                command=lambda: go_back(root, username, role)).pack(side="right", padx=6)


    load_data()

    # realtime search debounce
    search_after = {"id": None}
    def on_search_change(event=None):
        if search_after["id"]:
            root.after_cancel(search_after["id"])
        search_after["id"] = root.after(250, lambda: load_data(search_var.get().strip()))
    entry_search.bind("<KeyRelease>", on_search_change)

    # double-click open detail
    def on_double_click(event):
        sel = tree.selection()
        if sel:
            open_invoice_detail(tree, load_data, role)
    tree.bind("<Double-1>", on_double_click)

    # refresh wrapper
    def refresh():
        load_data()

# ---------- CREATE A NEW INVOICE ----------

def add_invoice(root, username, refresh):
    """Thêm hóa đơn mới (chuẩn hóa giao diện form theo Employee/Drink)"""

    # --- Tạo cửa sổ form chuẩn ---
    win, form = create_form_window("➕ Tạo hóa đơn mới", size="500x430")
    entries = {}

    # --- Danh sách label ---
    labels = ["Mã hóa đơn", "Mã NV (người lập)", "Khách hàng", "Ngày lập", "Ghi chú", "Trạng thái"]

    # --- Tải danh sách khách hàng ---
    try:
        db.cursor.execute("SELECT MaKH, TenKH FROM KhachHang ORDER BY TenKH")
        kh_rows = db.cursor.fetchall()
        kh_map = {f"{r.MaKH.strip()} - {r.TenKH}": r.MaKH.strip() for r in kh_rows}
        kh_list = list(kh_map.keys())
    except Exception as e:
        kh_rows, kh_map, kh_list = [], {}, []
        messagebox.showwarning("Lỗi", f"Không thể tải danh sách khách hàng: {e}", parent=win)

    # --- Sinh mã hóa đơn mới ---
    mahd_auto = generate_next_mahd(db.cursor)

    for i, text in enumerate(labels):
        ttk.Label(form, text=text, font=("Arial", 11), background="#f8f9fa")\
            .grid(row=i, column=0, sticky="w", padx=8, pady=8)

        if text == "Khách hàng":
            cb = ttk.Combobox(form, values=kh_list, state="readonly", font=("Arial", 11))
            cb.grid(row=i, column=1, padx=8, pady=8, sticky="ew")
            entries[text] = cb

        elif text == "Ngày lập":
            ent = ttk.Entry(form, font=("Arial", 11))
            ent.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            ent.grid(row=i, column=1, padx=8, pady=8, sticky="ew")
            entries[text] = ent

        elif text == "Trạng thái":
            cb = ttk.Combobox(form, values=["Chưa thanh toán", "Đã thanh toán", "Hủy"], state="readonly", font=("Arial", 11))
            cb.set("Chưa thanh toán")
            cb.grid(row=i, column=1, padx=8, pady=8, sticky="ew")
            entries[text] = cb

        elif text == "Ghi chú":
            txt = tk.Text(form, height=3, font=("Arial", 11))
            txt.grid(row=i, column=1, padx=8, pady=8, sticky="ew")
            entries[text] = txt

        else:
            ent = ttk.Entry(form, font=("Arial", 11))
            if text == "Mã hóa đơn":
                ent.insert(0, mahd_auto)
                ent.config(state="readonly")
            elif text == "Mã NV (người lập)":
                ent.insert(0, username or "")
            ent.grid(row=i, column=1, padx=8, pady=8, sticky="ew")
            entries[text] = ent

    form.grid_columnconfigure(1, weight=1)

    # --- Khung nút ---
    btn_frame = tk.Frame(win, bg="#f8f9fa")
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="💾 Lưu & Thêm mặt hàng", style="Add.TButton",
               command=lambda: submit()).pack(ipadx=10, ipady=6)

    # --- Hàm submit ---
    def submit():
        try:
            mahd = entries["Mã hóa đơn"].get().strip()
            manv = entries["Mã NV (người lập)"].get().strip()
            trangthai = entries["Trạng thái"].get().strip()
            ngaylap_raw = entries["Ngày lập"].get().strip()
            ghichu = entries["Ghi chú"].get("1.0", "end").strip()
            kh_val = entries["Khách hàng"].get().strip()
            makh = kh_map.get(kh_val) if kh_val else None

            # --- Kiểm tra dữ liệu ---
            if not manv:
                messagebox.showwarning("Thiếu thông tin", "⚠️ Mã nhân viên không được trống.", parent=win)
                return

            try:
                ngaylap = datetime.strptime(ngaylap_raw, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                messagebox.showwarning("Lỗi ngày", "⚠️ Ngày lập không hợp lệ. Định dạng: YYYY-MM-DD HH:MM:SS", parent=win)
                return

            # --- Kiểm tra trùng mã hóa đơn ---
            db.cursor.execute("SELECT COUNT(*) FROM HoaDon WHERE MaHD=?", (mahd,))
            if db.cursor.fetchone()[0] > 0:
                messagebox.showwarning("Trùng mã", f"Hóa đơn {mahd} đã tồn tại.", parent=win)
                return

            # --- Lưu vào DB ---
            db.cursor.execute("""
                INSERT INTO HoaDon (MaHD, NgayLap, MaNV, MaKH, TongTien, TrangThai, GhiChu)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (mahd, ngaylap, manv, makh, 0.0, trangthai, ghichu))
            db.conn.commit()

            messagebox.showinfo("✅ Thành công", f"Đã tạo hóa đơn {mahd}.", parent=win)
            win.destroy()

            # --- Mở cửa sổ chi tiết hóa đơn ---
            invoice_detail_window(root, mahd, refresh)

        except Exception as e:
            db.conn.rollback()
            messagebox.showerror("Lỗi", f"Không thể thêm hóa đơn: {e}", parent=win)

# ---------- OPEN INVOICE DETAIL WINDOW ----------
def open_invoice_detail(tree, parent_refresh, role=None):
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Chưa chọn", "Vui lòng chọn hóa đơn để xem chi tiết.")
        return
    mahd = tree.item(sel[0])['values'][0]
    invoice_detail_window(tree.master, mahd, parent_refresh)


def invoice_detail_window(root, mahd, parent_refresh=None):
    """
    Quản lý chi tiết: thêm/sửa/xóa mặt hàng trong hóa đơn.
    Khi thay đổi, gọi recalc_invoice_total để cập nhật tổng.
    """
    win = tk.Toplevel(root)
    win.title(f"Chi tiết Hóa đơn {mahd}")
    win.geometry("760x520")
    win.configure(bg="#f5f5f5")

    #Fullscreen cho CTHD
    win.state('zoomed')  # phóng to toàn màn hình

    # Left: Treeview chi tiết
    left = tk.Frame(win, bg="#f5f5f5")
    left.pack(side="left", fill="both", expand=True, padx=8, pady=8)

    cols = ("MaSP", "TenSP", "SoLuong", "DonGia", "ThanhTien")
    tree = ttk.Treeview(left, columns=cols, show="headings", height=20)
    headers = {"MaSP":"Mã SP", "TenSP":"Tên SP", "SoLuong":"SL", "DonGia":"Đơn giá", "ThanhTien":"Thành tiền"}
    for c in cols:
        tree.heading(c, text=headers[c])
        tree.column(c, anchor="center", width=140 if c!='TenSP' else 260)
    tree.pack(fill="both", expand=True)

    # Right: controls thêm hàng
    right = tk.Frame(win, bg="#f5f5f5", width=320)
    right.pack(side="right", fill="y", padx=8, pady=8)

    ttk.Label(right, text="Chọn sản phẩm:").pack(anchor="w", pady=(6,2))
    # load product list
    db.cursor.execute("SELECT MaSP, TenSP, DonGia FROM SANPHAM WHERE TrangThai = N'Có hàng'")
    products = db.cursor.fetchall()
    prod_map = {f"{r.MaSP.strip()} - {r.TenSP}": (r.MaSP.strip(), float(r.DonGia)) for r in products}
    prod_list = list(prod_map.keys())
    prod_var = tk.StringVar()
    prod_cb = ttk.Combobox(right, values=prod_list, textvariable=prod_var, state="readonly", width=35)
    prod_cb.pack(pady=6)

    ttk.Label(right, text="Số lượng:").pack(anchor="w", pady=(6,2))
    qty_var = tk.StringVar(value="1")
    qty_entry = ttk.Entry(right, textvariable=qty_var)
    qty_entry.pack(pady=6)

    price_lbl = ttk.Label(right, text="Đơn giá: -")
    price_lbl.pack(anchor="w", pady=(6,2))

    total_lbl = ttk.Label(right, text="Thành tiền: 0")
    total_lbl.pack(anchor="w", pady=(6,6))

    def on_product_select(e=None):
        key = prod_var.get()
        if key in prod_map:
            _, price = prod_map[key]
            price_lbl.config(text=f"Đơn giá: {int(price):,} đ")
            # cập nhật thành tiền
            try:
                q = int(qty_var.get())
            except:
                q = 1
            total_lbl.config(text=f"Thành tiền: {int(price * q):,} đ")
    prod_cb.bind("<<ComboboxSelected>>", on_product_select)

    def calc_total_preview(*args):
        key = prod_var.get()
        if key in prod_map:
            _, price = prod_map[key]
            try:
                q = int(qty_var.get())
            except:
                q = 1
            total_lbl.config(text=f"Thành tiền: {int(price * q):,} đ")
    qty_var.trace_add("write", lambda *a: calc_total_preview())

    # Buttons
    def add_item():
        key = prod_var.get()
        if not key:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn sản phẩm.", parent=win)
            return
        try:
            masp, price = prod_map[key]
            qty = int(qty_var.get())
            if qty <= 0:
                raise ValueError("Số lượng > 0")
        except Exception as e:
            messagebox.showwarning("Sai dữ liệu", f"Số lượng không hợp lệ: {e}", parent=win)
            return
        try:
            db.cursor.execute("SELECT SoLuong FROM ChiTietHoaDon WHERE MaHD=? AND MaSP=?", (mahd, masp))
            r = db.cursor.fetchone()
            if r:
                new_qty = int(r.SoLuong) + qty
                db.cursor.execute("UPDATE ChiTietHoaDon SET SoLuong=?, DonGia=? WHERE MaHD=? AND MaSP=?",
                                (new_qty, price, mahd, masp))
            else:
                db.cursor.execute("INSERT INTO ChiTietHoaDon (MaHD, MaSP, SoLuong, DonGia) VALUES (?, ?, ?, ?)",
                                (mahd, masp, qty, price))
            db.conn.commit()
            # Cập nhật điểm tích lũy cho khách hàng
            total = recalc_invoice_total(db.cursor, db.conn, mahd)
            update_customer_points(mahd)
            messagebox.showinfo("OK", f"Đã thêm {qty} x {masp}. Tổng: {int(total):,} đ", parent=win)
            load_items()
        except Exception as e:
            db.conn.rollback()
            messagebox.showerror("Lỗi", f"Không thể thêm mặt hàng: {e}", parent=win)


    def load_items():
        for it in tree.get_children():
            tree.delete(it)
        db.cursor.execute("SELECT c.MaSP, s.TenSP, c.SoLuong, c.DonGia, c.ThanhTien FROM ChiTietHoaDon c JOIN SANPHAM s ON c.MaSP = s.MaSP WHERE c.MaHD=?", (mahd,))
        rows = db.cursor.fetchall()
        for r in rows:
            tree.insert("", "end", values=(r.MaSP.strip(), r.TenSP, r.SoLuong, f"{int(r.DonGia):,}", f"{int(r.ThanhTien):,}"))
        # cập nhật tổng hiển thị
        db.cursor.execute("SELECT TongTien FROM HoaDon WHERE MaHD=?", (mahd,))
        row = db.cursor.fetchone()
        tong = int(row.TongTien) if row and row.TongTien is not None else 0
        win.title(f"Chi tiết Hóa đơn {mahd} - Tổng: {tong:,} đ")

    def delete_item():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn mặt hàng để xóa.")
            return
        values = tree.item(sel[0])["values"]
        masp_sel = values[0]
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa {masp_sel} khỏi hóa đơn?"):
            try:
                db.cursor.execute("DELETE FROM ChiTietHoaDon WHERE MaHD=? AND MaSP=?", (mahd, masp_sel))
                db.conn.commit()
                recalc_invoice_total(db.cursor, db.conn, mahd)
                load_items()
            except Exception as e:
                db.conn.rollback()
                messagebox.showerror("Lỗi", f"Không thể xóa mặt hàng: {e}")

    def edit_qty():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn mặt hàng để sửa.")
            return
        values = tree.item(sel[0])["values"]
        masp_sel = values[0]
        # ask new qty
        new_q = simpledialog.askinteger("Sửa SL", f"Nhập SL mới cho {masp_sel}:", minvalue=1)
        if new_q is None:
            return
        try:
            db.cursor.execute("UPDATE ChiTietHoaDon SET SoLuong=? WHERE MaHD=? AND MaSP=?", (new_q, mahd, masp_sel))
            db.conn.commit()
            recalc_invoice_total(db.cursor, db.conn, mahd)
            load_items()
        except Exception as e:
            db.conn.rollback()
            messagebox.showerror("Lỗi", f"Không thể cập nhật SL: {e}")

    # Khung chứa các nút bên phải
    btnf = tk.Frame(right, bg="#f5f5f5")
    btnf.pack(fill="x", pady=8)

    # Style thống nhất cho tất cả các nút
    style = ttk.Style()
    style.configure("Invoice.TButton",
                    font=("Segoe UI", 10, "bold"),
                    anchor="center",
                    padding=(5, 8))


    # Nút thao tác
    ttk.Button(btnf, text="➕ Thêm", style="Add.TButton", command=add_item).pack(fill="x", pady=4)
    ttk.Button(btnf, text="✏️ Sửa SL", style="Edit.TButton", command=edit_qty).pack(fill="x", pady=4)
    ttk.Button(btnf, text="🗑 Xóa", style="Delete.TButton", command=delete_item).pack(fill="x", pady=4)
    ttk.Button(btnf, text="Đóng", style="Close.TButton", command=win.destroy).pack(fill="x", pady=8)



    # load initial
    load_items()

# ---------- DELETE INVOICE ----------
def delete_invoice(tree, refresh):
    """Xóa hóa đơn (sử dụng helper safe_delete, có xử lý chi tiết hóa đơn)."""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn hóa đơn cần xóa!")
        return

    values = tree.item(selected[0])["values"]
    mahd = values[0]

    try:
        # Kiểm tra xem hóa đơn có chi tiết không
        db.cursor.execute("SELECT COUNT(*) AS SoLuong FROM ChiTietHoaDon WHERE MaHD = ?", (mahd,))
        row = db.cursor.fetchone()
        count = row.SoLuong if row else 0

        if count > 0:
            confirm = messagebox.askyesno(
                "Xác nhận",
                f"Hóa đơn {mahd} có {count} mặt hàng.\n"
                "Bạn có muốn xóa toàn bộ chi tiết trước khi xóa hóa đơn không?"
            )
            if not confirm:
                return
            db.cursor.execute("DELETE FROM ChiTietHoaDon WHERE MaHD = ?", (mahd,))
            db.conn.commit()

        # Gọi helper để xóa hóa đơn
        safe_delete(
            table_name="HoaDon",
            key_column="MaHD",
            key_value=mahd,
            cursor=db.cursor,
            conn=db.conn,
            refresh_func=refresh,
            item_label="hóa đơn"
        )

    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể xóa hóa đơn: {e}")


def update_customer_points(mahd):
    """Cộng điểm tích lũy cho khách hàng sau khi thanh toán"""
    db.cursor.execute("SELECT MaKH, TongTien FROM HoaDon WHERE MaHD=?", (mahd,))
    row = db.cursor.fetchone()
    if row and row.MaKH:
        makh, tongtien = row.MaKH, row.TongTien or 0
        diem_cong = int(tongtien // 10000)  # mỗi 10,000đ = 1 điểm
        db.cursor.execute("SELECT MaKH, TongTien, TrangThai FROM HoaDon WHERE MaHD=?", (mahd,))
        db.conn.commit()
    if not row or row.TrangThai != "Đã thanh toán":
        return  # chỉ tích điểm khi đã thanh toán


