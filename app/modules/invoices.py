# app/modules/invoices.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from decimal import Decimal, InvalidOperation
from datetime import datetime
from app import db
from app.utils import clear_window, generate_next_mahd, recalc_invoice_total, safe_delete

# ---------- SHOW MAIN INVOICE MODULE ----------
def show_invoices_module(root, username=None, role=None):
    clear_window(root)
    root.title("Quản lý Hóa đơn")
    root.configure(bg="#f5e6ca")

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
    cols = ("MaHD", "NgayLap", "MaNV", "TenKH", "TongTien", "TrangThai")
    tree = ttk.Treeview(root, columns=cols, show="headings", height=16)
    headers = {
    "MaHD": "Mã HD",
    "NgayLap": "Ngày lập",
    "MaNV": "Mã NV",
    "TenKH": "Khách hàng",
    "TongTien": "Tổng tiền (đ)",
    "TrangThai": "Trạng thái"
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
            SELECT h.MaHD, h.NgayLap, h.MaNV, k.TenKH, h.TongTien, h.TrangThai
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
                tree.insert("", "end", values=(r.MaHD.strip(), ngay, r.MaNV.strip(), tong, r.TrangThai))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách hóa đơn: {e}")

    # Buttons on top frame

    ttk.Button(top, text="🔄 Tải lại", style="Close.TButton",
               command=load_data).pack(side="left", padx=5)

    ttk.Button(top, text="➕ Thêm", style = "Add.TButton",
                command=lambda: create_invoice_window(root, username, refresh)).pack(side="left", padx=6)
    
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
    def schedule_search(event=None):
        if search_after["id"]:
            root.after_cancel(search_after["id"])
        search_after["id"] = root.after(250, lambda: load_data(search_var.get().strip()))
    entry_search.bind("<KeyRelease>", schedule_search)

    # double-click open detail
    def on_double(e):
        open_invoice_detail(tree, load_data, role)
    tree.bind("<Double-1>", on_double)

    # refresh wrapper
    def refresh():
        load_data()

# ---------- CREATE A NEW INVOICE ----------
def create_invoice_window(root, username, parent_refresh=None):
    """
    Tạo hóa đơn mới: tự sinh MaHD, chọn nhân viên (mặc định username), ngày lập, ghi chú.
    Sau khi tạo sẽ mở cửa sổ chi tiết (invoice_detail_window) để thêm món.
    """
    win = tk.Toplevel(root)
    win.title("➕ Tạo hóa đơn mới")
    win.geometry("420x260")
    win.resizable(False, False)

    frame = tk.Frame(win, padx=12, pady=12)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Mã hóa đơn:").grid(row=0, column=0, sticky="w", pady=6)
    mahd = generate_next_mahd(db.cursor)
    ent_ma = ttk.Entry(frame)
    ent_ma.insert(0, mahd)
    ent_ma.config(state="readonly")
    ent_ma.grid(row=0, column=1, sticky="ew", pady=6)

    ttk.Label(frame, text="Người lập (Mã NV):").grid(row=1, column=0, sticky="w", pady=6)
    ent_manv = ttk.Entry(frame)
    ent_manv.insert(0, username or "")
    ent_manv.grid(row=1, column=1, sticky="ew", pady=6)

    ttk.Label(frame, text="Ngày lập:").grid(row=2, column=0, sticky="w", pady=6)
    ent_ngay = ttk.Entry(frame)
    ent_ngay.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    ent_ngay.grid(row=2, column=1, sticky="ew", pady=6)

    ttk.Label(frame, text="Ghi chú:").grid(row=3, column=0, sticky="nw", pady=6)
    txt_note = tk.Text(frame, height=4, width=30)
    txt_note.grid(row=3, column=1, sticky="ew", pady=6)

    # --- Combobox chọn khách hàng ---
    ttk.Label(frame, text="Khách hàng (tuỳ chọn):").grid(row=4, column=0, sticky="w", pady=6)

    try:
        db.cursor.execute("SELECT MaKH, TenKH FROM KhachHang ORDER BY TenKH")
        kh_rows = db.cursor.fetchall()
        kh_map = {f"{r.MaKH.strip()} - {r.TenKH}": r.MaKH.strip() for r in kh_rows}
        kh_list = list(kh_map.keys())
    except Exception as e:
        kh_rows, kh_map, kh_list = [], {}, []
        messagebox.showwarning("Lỗi", f"Không thể tải danh sách khách hàng: {e}")

    kh_var = tk.StringVar()
    kh_cb = ttk.Combobox(frame, values=kh_list, textvariable=kh_var, state="readonly")
    kh_cb.grid(row=4, column=1, sticky="ew", pady=6)

    frame.grid_columnconfigure(1, weight=1)

    def create_and_open_detail():
        manv_val = ent_manv.get().strip()
        ghi_chu = txt_note.get("1.0", "end").strip()
        if not manv_val:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập Mã NV người lập.")
            return
        try:
            # Tạo hóa đơn (MaHD, NgayLap, MaNV, TongTien default 0)
            # Lấy mã khách hàng (nếu có chọn)
            makh = kh_map.get(kh_var.get()) if kh_var.get() else None

            # Tạo hóa đơn (MaHD, NgayLap, MaNV, MaKH, TongTien, TrangThai, GhiChu)
            db.cursor.execute("""
                INSERT INTO HoaDon (MaHD, NgayLap, MaNV, MaKH, TongTien, TrangThai, GhiChu)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (mahd, datetime.now(), manv_val, makh, 0.0, 'Chưa thanh toán', ghi_chu))
            db.conn.commit()
            messagebox.showinfo("Thành công", f"Đã tạo hóa đơn {mahd}.")
            win.destroy()
            # Mở cửa sổ chi tiết để thêm món
            invoice_detail_window(root, mahd, parent_refresh)
        except Exception as e:
            db.conn.rollback()
            messagebox.showerror("Lỗi", f"Không thể tạo hóa đơn: {e}")

    ttk.Button(frame, text="Tạo & Thêm mặt hàng", command=create_and_open_detail).grid(row=4, column=0, columnspan=2, pady=10)

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
    ttk.Button(btnf, text="➕ Thêm", style="Invoice.TButton", command=add_item).pack(fill="x", pady=4)
    ttk.Button(btnf, text="✏️ Sửa SL", style="Invoice.TButton", command=edit_qty).pack(fill="x", pady=4)
    ttk.Button(btnf, text="🗑 Xóa", style="Invoice.TButton", command=delete_item).pack(fill="x", pady=4)
    ttk.Button(btnf, text="Đóng", style="Invoice.TButton", command=win.destroy).pack(fill="x", pady=8)



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
        from app.utils import safe_delete
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
        db.cursor.execute("UPDATE KhachHang SET DiemTichLuy = ISNULL(DiemTichLuy,0) + ? WHERE MaKH=?", (diem_cong, makh))
        db.conn.commit()
    if not row or row.TrangThai != "Đã thanh toán":
        return  # chỉ tích điểm khi đã thanh toán

# ---------- GO BACK TO MAIN MENU ----------
def go_back(root, username, role):
    """Quay lại giao diện chính (main menu)."""
    from app.ui.mainmenu_frame import show_main_menu
    show_main_menu(root, username, role)
