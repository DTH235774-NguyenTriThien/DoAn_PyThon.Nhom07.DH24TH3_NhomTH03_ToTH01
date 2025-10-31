# app/modules/invoices.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from decimal import Decimal, InvalidOperation
from datetime import datetime
from app import db

# SỬA 1: Cập nhật Imports
from app.db import fetch_query, execute_query, execute_scalar
from app.theme import setup_styles
# Các hàm UI chung
from app.utils.utils import clear_window, create_form_window, go_back, center_window
# Các hàm nghiệp vụ
from app.utils.business_helpers import recalc_invoice_total, safe_delete
# Hàm sinh mã
from app.utils.id_helpers import generate_next_mahd
# Helper TreeView
from app.utils.treeview_helpers import fill_treeview_chunked

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

    # SỬA 2: Thêm Label trạng thái
    status_label_var = tk.StringVar(value="")
    status_label = ttk.Label(top, textvariable=status_label_var, font=("Arial", 10, "italic"), background="#f5e6ca", foreground="blue")
    status_label.pack(side="left", padx=10)

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

    # SỬA 3: Nâng cấp load_data (dùng fetch_query và chunked)
    def load_data(tree_widget, status_var, keyword=None):
        status_var.set("Đang tải...")
        tree_widget.update_idletasks()
        try:
            sql = """
            SELECT h.MaHD, h.NgayLap, h.MaNV, k.TenKH, h.TongTien, h.TrangThai, h.GhiChu
            FROM HoaDon h
            LEFT JOIN KhachHang k ON h.MaKH = k.MaKH
            """
            params = ()
            if keyword:
                kw = f"%{keyword}%"
                sql += " WHERE h.MaHD LIKE ? OR h.MaNV LIKE ? OR h.TrangThai LIKE ? OR k.TenKH LIKE ?"
                params = (kw, kw, kw, kw)
            sql += " ORDER BY h.NgayLap DESC"
            
            # Dùng fetch_query
            rows = db.fetch_query(sql, params)
            
            tree_data = []
            for r in rows:
                ngay = r["NgayLap"].strftime("%d/%m/%Y %H:%M") if r["NgayLap"] else ""
                tong = f"{int(r['TongTien']):,}" if r['TongTien'] is not None else "0"
                values_tuple = (
                    r["MaHD"].strip(),
                    ngay,
                    r["MaNV"].strip(),
                    r["TenKH"] if r["TenKH"] else "",
                    tong,
                    r["TrangThai"] if r["TrangThai"] else "",
                    r["GhiChu"] if r["GhiChu"] else ""
                )
                tree_data.append({"iid": r["MaHD"], "values": values_tuple})
            
            # Dùng fill_treeview_chunked
            fill_treeview_chunked(
                tree_widget, 
                tree_data, 
                on_complete=lambda: status_var.set(f"Đã tải {len(rows)} hóa đơn.")
            )

        except Exception as e:
            status_var.set("Lỗi tải!")
            messagebox.showerror("Lỗi", f"Không thể tải danh sách hóa đơn: {e}")

    # Buttons on top frame
    
    # Cập nhật hàm refresh
    def refresh():
        load_data(tree, status_label_var, search_var.get().strip())

    ttk.Button(top, text="🔄 Tải lại", style="Close.TButton",
               command=refresh).pack(side="left", padx=5)

    ttk.Button(top, text="➕ Thêm", style = "Add.TButton",
               command=lambda: add_invoice(root, username, refresh)).pack(side="left", padx=6)
    
    ttk.Button(top, text="✏️ Sửa", style="Edit.TButton",
               command=lambda: open_invoice_detail(tree, refresh, role)).pack(side="left", padx=6)
    
    ttk.Button(top, text="🗑 Xóa", style="Delete.TButton",
               command=lambda: delete_invoice(tree, refresh)).pack(side="left", padx=6)

    ttk.Button(top, text="⬅ Quay lại", style="Close.TButton",
               command=lambda: go_back(root, username, role)).pack(side="right", padx=6)

    # Tải lần đầu
    refresh()

    # realtime search debounce
    search_after = {"id": None}
    def on_search_change(event=None):
        if search_after["id"]:
            root.after_cancel(search_after["id"])
        search_after["id"] = root.after(250, refresh) # Gọi refresh chuẩn
    entry_search.bind("<KeyRelease>", on_search_change)

    # double-click open detail
    def on_double_click(event):
        sel = tree.selection()
        if sel:
            open_invoice_detail(tree, refresh, role)
    tree.bind("<Double-1>", on_double_click)


# ---------- CREATE A NEW INVOICE ----------

def add_invoice(root, username, refresh):
    """Thêm hóa đơn mới (chuẩn hóa giao diện form theo Employee/Drink)"""
    win, form = create_form_window("➕ Tạo hóa đơn mới", size="500x430")
    entries = {}
    labels = ["Mã hóa đơn", "Mã NV (người lập)", "Khách hàng", "Ngày lập", "Ghi chú", "Trạng thái"]

    # SỬA 4: Tải danh sách khách hàng dùng fetch_query
    try:
        kh_rows = db.fetch_query("SELECT MaKH, TenKH FROM KhachHang ORDER BY TenKH")
        kh_map = {f"{r['MaKH'].strip()} - {r['TenKH']}": r['MaKH'].strip() for r in kh_rows}
        kh_list = [""] # Thêm lựa chọn rỗng
        kh_list.extend(list(kh_map.keys()))
    except Exception as e:
        kh_rows, kh_map, kh_list = [], {}, []
        messagebox.showwarning("Lỗi", f"Không thể tải danh sách khách hàng: {e}", parent=win)

    # Sinh mã hóa đơn mới
    mahd_auto = generate_next_mahd(db.cursor)

    for i, text in enumerate(labels):
        ttk.Label(form, text=text, font=("Arial", 11), background="#f8f9fa")\
            .grid(row=i, column=0, sticky="w", padx=8, pady=8)

        if text == "Khách hàng":
            cb = ttk.Combobox(form, values=kh_list, state="readonly", font=("Arial", 11))
            cb.grid(row=i, column=1, padx=8, pady=8, sticky="ew")
            entries[text] = cb
        # ... (các
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

    btn_frame = tk.Frame(win, bg="#f8f9fa")
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="💾 Lưu & Thêm mặt hàng", style="Add.TButton",
               command=lambda: submit()).pack(ipadx=10, ipady=6)

    def submit():
        try:
            mahd = entries["Mã hóa đơn"].get().strip()
            manv = entries["Mã NV (người lập)"].get().strip()
            trangthai = entries["Trạng thái"].get().strip()
            ngaylap_raw = entries["Ngày lập"].get().strip()
            ghichu = entries["Ghi chú"].get("1.0", "end").strip()
            kh_val = entries["Khách hàng"].get().strip()
            makh = kh_map.get(kh_val) if kh_val else None

            if not manv:
                messagebox.showwarning("Thiếu thông tin", "⚠️ Mã nhân viên không được trống.", parent=win)
                return
            try:
                ngaylap = datetime.strptime(ngaylap_raw, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                messagebox.showwarning("Lỗi ngày", "⚠️ Ngày lập không hợp lệ. Định dạng: YYYY-MM-DD HH:MM:SS", parent=win)
                return

            # SỬA 5: Dùng execute_scalar để kiểm tra trùng
            if db.execute_scalar("SELECT COUNT(*) FROM HoaDon WHERE MaHD=?", (mahd,)) > 0:
                messagebox.showwarning("Trùng mã", f"Hóa đơn {mahd} đã tồn tại.", parent=win)
                return

            # Dùng execute_query (đã chuẩn)
            query = """
                INSERT INTO HoaDon (MaHD, NgayLap, MaNV, MaKH, TongTien, TrangThai, GhiChu)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (mahd, ngaylap, manv, makh, 0.0, trangthai, ghichu)

            if execute_query(query, params):
                messagebox.showinfo("✅ Thành công", f"Đã tạo hóa đơn {mahd}.", parent=win)
                win.destroy()
                refresh()
                # Mở cửa sổ chi tiết hóa đơn
                invoice_detail_window(root, mahd, refresh)

        except Exception as e:
            # Không cần rollback, execute_query đã xử lý
            messagebox.showerror("Lỗi", f"Không thể thêm hóa đơn: {e}", parent=win)

# ---------- OPEN INVOICE DETAIL WINDOW ----------
def open_invoice_detail(tree, parent_refresh, role=None):
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Chưa chọn", "Vui lòng chọn hóa đơn để xem chi tiết.")
        return
    # SỬA 6: Lấy MaHD từ iid
    mahd = sel[0] 
    invoice_detail_window(tree.master, mahd, parent_refresh)


def invoice_detail_window(root, mahd, parent_refresh=None):
    win = tk.Toplevel(root)
    win.title(f"Chi tiết Hóa đơn {mahd}")
    win.geometry("760x520")
    win.configure(bg="#f5f5f5")
    win.state('zoomed') 

    # Left: Treeview chi tiết
    left = tk.Frame(win, bg="#f5f5f5")
    left.pack(side="left", fill="both", expand=True, padx=8, pady=8)

    # SỬA 7: Thêm status_label cho TreeView con
    status_label_var_detail = tk.StringVar(value="")
    status_label_detail = ttk.Label(left, textvariable=status_label_var_detail, font=("Arial", 10, "italic"), background="#f5f5f5", foreground="blue")
    status_label_detail.pack(anchor="w")

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
    
    # SỬA 8: Tải sản phẩm dùng fetch_query
    try:
        query_sp = "SELECT MaSP, TenSP, DonGia, TrangThai FROM SANPHAM WHERE TrangThai = N'Có hàng'"
        products = db.fetch_query(query_sp)
        prod_map = {f"{r['MaSP'].strip()} - {r['TenSP']}": (r['MaSP'].strip(), float(r['DonGia'])) for r in products}
        prod_list = list(prod_map.keys())
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể tải danh sách sản phẩm: {e}", parent=win)
        prod_map = {}
        prod_list = []
        
    prod_var = tk.StringVar()
    prod_cb = ttk.Combobox(right, values=prod_list, textvariable=prod_var, state="readonly", 
    width=35)
    prod_cb.pack(pady=6)

    # ... (Phần logic combobox, entry, label giữ nguyên)
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

    # SỬA 9: Nâng cấp add_item (dùng execute_scalar và execute_query)
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
            # Kiểm tra xem SP đã tồn tại trong CTHD chưa
            current_qty = db.execute_scalar(
                "SELECT SoLuong FROM ChiTietHoaDon WHERE MaHD=? AND MaSP=?", 
                (mahd, masp)
            )
            
            if current_qty is not None:
                # Đã tồn tại -> UPDATE
                new_qty = int(current_qty) + qty
                query = "UPDATE ChiTietHoaDon SET SoLuong=?, DonGia=? WHERE MaHD=? AND MaSP=?"
                params = (new_qty, price, mahd, masp)
            else:
                # Chưa tồn tại -> INSERT
                query = "INSERT INTO ChiTietHoaDon (MaHD, MaSP, SoLuong, DonGia) VALUES (?, ?, ?, ?)"
                params = (mahd, masp, qty, price)

            if db.execute_query(query, params):
                # Cập nhật tổng tiền hóa đơn (và điểm KH nếu cần)
                total = recalc_invoice_total(db.cursor, db.conn, mahd)
                update_customer_points(mahd)
                
                load_items() # Tải lại CTHD
                parent_refresh() # Tải lại DS Hóa đơn chính
                
                # Cập nhật tiêu đề cửa sổ ngay lập tức
                win.title(f"Chi tiết Hóa đơn {mahd} - Tổng: {int(total):,} đ")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm mặt hàng: {e}", parent=win)

    # SỬA 10: Nâng cấp load_items (dùng fetch_query và chunked)
    def load_items():
        status_label_var_detail.set("Đang tải chi tiết...")
        tree.update_idletasks()
        try:
            query = "SELECT c.MaSP, s.TenSP, c.SoLuong, c.DonGia, c.ThanhTien FROM ChiTietHoaDon c JOIN SANPHAM s ON c.MaSP = s.MaSP WHERE c.MaHD=?"
            rows = db.fetch_query(query, (mahd,))
            
            tree_data = []
            for r in rows:
                values_tuple = (
                    r["MaSP"].strip(), 
                    r["TenSP"], 
                    r["SoLuong"], 
                    f"{int(r['DonGia']):,}", 
                    f"{int(r['ThanhTien']):,}"
                )
                tree_data.append({"iid": r["MaSP"], "values": values_tuple})

            def on_load_complete():
                # Cập nhật tổng tiền trên tiêu đề cửa sổ
                try:
                    tong = db.execute_scalar("SELECT TongTien FROM HoaDon WHERE MaHD=?", (mahd,)) or 0
                    win.title(f"Chi tiết Hóa đơn {mahd} - Tổng: {int(tong):,} đ")
                    status_label_var_detail.set(f"Đã tải {len(rows)} mặt hàng.")
                except Exception as e:
                    win.title(f"Chi tiết Hóa đơn {mahd} - Lỗi lấy tổng")
                    status_label_var_detail.set("Lỗi!")
            
            fill_treeview_chunked(
                tree, 
                tree_data, 
                on_complete=on_load_complete
            )
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải chi tiết hóa đơn: {e}", parent=win)

    # SỬA 11: Nâng cấp delete_item (dùng iid và execute_query)
    def delete_item():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn mặt hàng để xóa.", parent=win)
            return
        
        masp_sel = sel[0] # Lấy iid (MaSP)
        
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa {masp_sel} khỏi hóa đơn?"):
            query = "DELETE FROM ChiTietHoaDon WHERE MaHD=? AND MaSP=?"
            if db.execute_query(query, (mahd, masp_sel)):
                recalc_invoice_total(db.cursor, db.conn, mahd)
                load_items()
                parent_refresh()

    # SỬA 12: Nâng cấp edit_qty (dùng iid và execute_query)
    def edit_qty():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn mặt hàng để sửa.", parent=win)
            return
        
        masp_sel = sel[0] # Lấy iid (MaSP)
        
        new_q = simpledialog.askinteger("Sửa SL", f"Nhập SL mới cho {masp_sel}:", minvalue=1, parent=win)
        if new_q is None:
            return
        
        query = "UPDATE ChiTietHoaDon SET SoLuong=? WHERE MaHD=? AND MaSP=?"
        if db.execute_query(query, (new_q, mahd, masp_sel)):
            recalc_invoice_total(db.cursor, db.conn, mahd)
            load_items()
            parent_refresh()

    # Khung chứa các nút bên phải
    btnf = tk.Frame(right, bg="#f5f5f5")
    btnf.pack(fill="x", pady=8)
    
    # ... (Các nút giữ nguyên)
    ttk.Button(btnf, text="➕ Thêm", style="Add.TButton", command=add_item).pack(fill="x", pady=4)
    ttk.Button(btnf, text="✏️ Sửa SL", style="Edit.TButton", command=edit_qty).pack(fill="x", pady=4)
    ttk.Button(btnf, text="🗑 Xóa", style="Delete.TButton", command=delete_item).pack(fill="x", pady=4)
    ttk.Button(btnf, text="Đóng", style="Close.TButton", command=win.destroy).pack(fill="x", pady=8)

    # load initial
    load_items()

# ---------- DELETE INVOICE ----------
# SỬA 13: Nâng cấp delete_invoice (dùng iid và execute_scalar)
# (Giả định bạn đã import 'db' ở đầu file app/modules/invoices.py)
# from app import db

def delete_invoice(tree, refresh):
    """Xóa hóa đơn (sử dụng helper safe_delete, có xử lý chi tiết hóa đơn)."""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn hóa đơn cần xóa!")
        return

    mahd = selected[0] # Lấy MaHD (iid)

    try:
        # =========================================================
        # SỬA LỖI TOÀN VẸN: KIỂM TRA TRẠNG THÁI TRƯỚC KHI XÓA
        # =========================================================
        trang_thai = db.execute_scalar("SELECT TrangThai FROM HoaDon WHERE MaHD = ?", (mahd,))
        
        # So sánh chuỗi Python bình thường (không có N'')
        if trang_thai == 'Đã thanh toán': 
            messagebox.showwarning(
                "Không thể xóa", 
                f"Hóa đơn {mahd} đã được thanh toán và không thể xóa."
            )
            return
        # =========================================================

        # Kiểm tra xem hóa đơn có chi tiết không
        count = db.execute_scalar("SELECT COUNT(*) FROM ChiTietHoaDon WHERE MaHD = ?", (mahd,)) or 0

        if count > 0:
            confirm = messagebox.askyesno(
                "Xác nhận",
                f"Hóa đơn {mahd} có {count} mặt hàng.\n"
                "Bạn có muốn xóa toàn bộ chi tiết trước khi xóa hóa đơn không?"
            )
            if not confirm:
                return
            
            # Xóa ChiTietHoaDon trước
            if not db.execute_query("DELETE FROM ChiTietHoaDon WHERE MaHD = ?", (mahd,)):
                messagebox.showerror("Lỗi", "Không thể xóa chi tiết hóa đơn, thao tác đã hủy.")
                return

        # Gọi helper để xóa hóa đơn (bảng cha)
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
# SỬA 14: Sửa lỗi logic và chuẩn hóa update_customer_points
def update_customer_points(mahd):
    """
    Cập nhật điểm tích lũy cho khách hàng DỰA TRÊN HÓA ĐƠN.
    Chỉ cộng điểm nếu hóa đơn 'Đã thanh toán'.
    """
    try:
        # Lấy thông tin hóa đơn (MaKH, TongTien, TrangThai)
        record = db.fetch_query("SELECT MaKH, TongTien, TrangThai FROM HoaDon WHERE MaHD=?", (mahd,))
        if not record:
            return # Không tìm thấy hóa đơn
        
        row = record[0]
        
        # Chỉ cộng điểm nếu có MaKH và TrangThai = 'Đã thanh toán'
        if row["MaKH"] and row["TrangThai"] == 'Đã thanh toán':
            makh = row["MaKH"]
            tongtien = row["TongTien"] or 0
            
            # Tính điểm (ví dụ: 10,000đ = 1 điểm)
            diem_cong = int(tongtien // 10000)
            
            if diem_cong > 0:
                # Cập nhật bảng KhachHang
                query = "UPDATE KhachHang SET DiemTichLuy = DiemTichLuy + ? WHERE MaKH = ?"
                db.execute_query(query, (diem_cong, makh))
                
                # nếu hóa đơn 'Đã thanh toán'. 
                # Cần cân nhắc chuyển logic này ra ngoài,
                # ví dụ: chỉ chạy khi Hóa đơn chuyển trạng thái sang 'Đã thanh toán'.)
                
    except Exception as e:
        print(f"Lỗi cập nhật điểm khách hàng: {e}")
        # Không hiển thị messagebox lỗi ở đây để tránh làm phiền khi thêm/sửa CTHD