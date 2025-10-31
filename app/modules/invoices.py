# app/modules/invoices.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from decimal import Decimal, InvalidOperation
from datetime import datetime
from app import db

# SỬA 1: Cập nhật Imports (xóa go_back, clear_window, center_window)
from app.db import fetch_query, execute_query, execute_scalar
from app.theme import setup_styles
from app.utils.utils import create_form_window
# Các hàm nghiệp vụ
from app.utils.business_helpers import recalc_invoice_total, safe_delete
# Hàm sinh mã
from app.utils.id_helpers import generate_next_mahd
# Helper TreeView
from app.utils.treeview_helpers import fill_treeview_chunked

# =========================================================
# CÁC HÀM HELPER (CỬA SỔ CON VÀ NGHIỆP VỤ)
# (Giữ nguyên các hàm: update_customer_points, invoice_detail_window)
# =========================================================

# ---------- UPDATE CUSTOMER POINTS (HELPER) ----------
def update_customer_points(makh, tongtien):
    """
    Cập nhật điểm tích lũy cho khách hàng.
    Hàm này CHỈ NÊN được gọi SAU KHI thanh toán thành công.
    """
    try:
        # Chúng ta đã biết hóa đơn 'Đã thanh toán' và có MaKH
        if makh and tongtien > 0:
            diem_cong = int(float(tongtien) // 10000)
            
            if diem_cong > 0:
                query = "UPDATE KhachHang SET DiemTichLuy = DiemTichLuy + ? WHERE MaKH = ?"
                db.execute_query(query, (diem_cong, makh))
                
    except Exception as e:
        print(f"Lỗi cập nhật điểm khách hàng: {e}")
# ---------- INVOICE DETAIL WINDOW (CỬA SỔ CON) ----------
def invoice_detail_window(root, mahd, parent_refresh=None, trang_thai_hoa_don='Chưa thanh toán'):
    """
    Quản lý chi tiết: thêm/sửa/xóa mặt hàng trong hóa đơn.
    (Hàm này giữ nguyên, 'root' ở đây là cha của Toplevel, là đúng)
    """
    win = tk.Toplevel(root)
    win.title(f"Chi tiết Hóa đơn {mahd}")
    win.geometry("760x520")
    win.configure(bg="#f5f5f5")
    win.state('zoomed') 

    # (Code bên trong hàm này giữ nguyên)
    # Left: Treeview chi tiết
    left = tk.Frame(win, bg="#f5f5f5")
    left.pack(side="left", fill="both", expand=True, padx=8, pady=8)

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
    
    try:
        query_sp = "SELECT MaSP, TenSP, DonGia, TrangThai FROM SANPHAM WHERE TrangThai = N'Còn bán'"
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
            current_qty = db.execute_scalar(
                "SELECT SoLuong FROM ChiTietHoaDon WHERE MaHD=? AND MaSP=?", 
                (mahd, masp)
            )
            
            if current_qty is not None:
                new_qty = int(current_qty) + qty
                query = "UPDATE ChiTietHoaDon SET SoLuong=?, DonGia=? WHERE MaHD=? AND MaSP=?"
                params = (new_qty, price, mahd, masp)
            else:
                query = "INSERT INTO ChiTietHoaDon (MaHD, MaSP, SoLuong, DonGia) VALUES (?, ?, ?, ?)"
                params = (mahd, masp, qty, price)

            if db.execute_query(query, params):
                total = recalc_invoice_total(db.cursor, db.conn, mahd)
                
                load_items() 
                parent_refresh() 
                
                win.title(f"Chi tiết Hóa đơn {mahd} - Tổng: {int(total):,} đ")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm mặt hàng: {e}", parent=win)

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

    def delete_item():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn mặt hàng để xóa.", parent=win)
            return
        
        masp_sel = sel[0] 
        
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa {masp_sel} khỏi hóa đơn?"):
            query = "DELETE FROM ChiTietHoaDon WHERE MaHD=? AND MaSP=?"
            if db.execute_query(query, (mahd, masp_sel)):
                recalc_invoice_total(db.cursor, db.conn, mahd)
                load_items()
                parent_refresh()

    def edit_qty():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn mặt hàng để sửa.", parent=win)
            return
        
        masp_sel = sel[0] 
        
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
    
    # --- Logic nút (Thêm/Sửa/Xóa/Thanh toán) ---
    btn_add = ttk.Button(btnf, text="➕ Thêm", style="Add.TButton", command=add_item)
    btn_add.pack(fill="x", pady=4)
    btn_edit = ttk.Button(btnf, text="✏️ Sửa SL", style="Edit.TButton", command=edit_qty)
    btn_edit.pack(fill="x", pady=4)
    btn_delete = ttk.Button(btnf, text="🗑 Xóa", style="Delete.TButton", command=delete_item)
    btn_delete.pack(fill="x", pady=4)

    # Hàm xử lý thanh toán
    # Hàm xử lý thanh toán (ĐÃ SỬA LỖI)
    def perform_payment():
        try:
            # SỬA 1: LẤY dữ liệu hóa đơn TRƯỚC TIÊN
            record = db.fetch_query("SELECT MaKH, TongTien, TrangThai FROM HoaDon WHERE MaHD=?", (mahd,))
            if not record:
                messagebox.showerror("Lỗi", "Không tìm thấy hóa đơn.", parent=win)
                return

            row = record[0]
            current_status = row["TrangThai"]
            makh_to_update = row["MaKH"]
            tongtien_to_update = row["TongTien"] or 0

            # SỬA 2: KIỂM TRA LỖI CỘNG ĐIỂM NHIỀU LẦN
            if current_status == 'Đã thanh toán':
                messagebox.showinfo("Thông báo", "Hóa đơn này đã được thanh toán trước đó.", parent=win)
                # (Vẫn nên vô hiệu hóa nút nếu lỡ bật)
                btn_add.config(state="disabled")
                btn_edit.config(state="disabled")
                btn_delete.config(state="disabled")
                btn_thanh_toan.config(state="disabled")
                return

            # SỬA 3: HỎI XÁC NHẬN (logic cũ)
            if messagebox.askyesno("Xác nhận Thanh toán", f"Xác nhận thanh toán hóa đơn {mahd}?"):
                
                # SỬA 4: CẬP NHẬT TRẠNG THÁI HÓA ĐƠN
                if db.execute_query("UPDATE HoaDon SET TrangThai = N'Đã thanh toán' WHERE MaHD = ?", (mahd,)):
                    
                    # SỬA 5: GỌI HÀM CỘNG ĐIỂM MỚI (TRUYỀN DỮ LIỆU ĐÃ LẤY)
                    # Điều này giải quyết Lỗi Transaction (Lỗi 2)
                    update_customer_points(makh_to_update, tongtien_to_update)
                    
                    messagebox.showinfo("Thành công", "Hóa đơn đã được thanh toán.", parent=win)
                    parent_refresh() 
                    
                    # Tắt các nút
                    btn_add.config(state="disabled")
                    btn_edit.config(state="disabled")
                    btn_delete.config(state="disabled")
                    btn_thanh_toan.config(state="disabled")
                else:
                    messagebox.showerror("Lỗi", "Không thể cập nhật trạng thái hóa đơn.", parent=win)
                
        except Exception as e:
            messagebox.showerror("Lỗi nghiêm trọng", f"Đã xảy ra lỗi khi thanh toán: {e}", parent=win)

    # Nút Thanh toán
    btn_thanh_toan = ttk.Button(btnf, text="💳 Thanh toán", style="Add.TButton", command=perform_payment)
    btn_thanh_toan.pack(fill="x", pady=10)
    
    # Nút Đóng
    ttk.Button(btnf, text="Đóng", style="Close.TButton", command=win.destroy).pack(fill="x", pady=8)

    # Kiểm tra trạng thái và vô hiệu hóa nút
    is_read_only = (trang_thai_hoa_don == 'Đã thanh toán')
    if is_read_only:
        btn_add.config(state="disabled")
        btn_edit.config(state="disabled")
        btn_delete.config(state="disabled")
        btn_thanh_toan.config(state="disabled")
        
        ttk.Label(right, text="HÓA ĐƠN ĐÃ THANH TOÁN (CHỈ XEM)", 
                   font=("Segoe UI", 10, "bold"), foreground="red", background="#f5f5f5")\
                   .pack(anchor="w", pady=(10,2))

    # load initial
    load_items()

# ---------- OPEN INVOICE DETAIL (HELPER) ----------
# SỬA 2: Xóa 'role' khỏi chữ ký hàm (vì không dùng)
def open_invoice_detail(tree, parent_refresh):
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Chưa chọn", "Vui lòng chọn hóa đơn để xem chi tiết.")
        return
    mahd = sel[0] 
    
    # Lấy Trạng Thái của hóa đơn
    trang_thai = db.execute_scalar("SELECT TrangThai FROM HoaDon WHERE MaHD = ?", (mahd,))
    
    # (Hàm invoice_detail_window đã được định nghĩa ở trên)
    invoice_detail_window(tree.master, mahd, parent_refresh, trang_thai)

# ---------- CREATE A NEW INVOICE (HELPER) ----------
def add_invoice(root, username, refresh):
    """
    Thêm hóa đơn mới.
    'root' ở đây là cha của Toplevel (sẽ là parent_frame), 'username' dùng để điền sẵn.
    """
    win, form = create_form_window("➕ Tạo hóa đơn mới", size="500x430")
    entries = {}
    labels = ["Mã hóa đơn", "Mã NV (người lập)", "Khách hàng", "Ngày lập", "Ghi chú", "Trạng thái"]

    try:
        kh_rows = db.fetch_query("SELECT MaKH, TenKH FROM KhachHang ORDER BY TenKH")
        kh_map = {f"{r['MaKH'].strip()} - {r['TenKH']}": r['MaKH'].strip() for r in kh_rows}
        kh_list = [""] 
        kh_list.extend(list(kh_map.keys()))
    except Exception as e:
        kh_rows, kh_map, kh_list = [], {}, []
        messagebox.showwarning("Lỗi", f"Không thể tải danh sách khách hàng: {e}", parent=win)

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

            if db.execute_scalar("SELECT COUNT(*) FROM HoaDon WHERE MaHD=?", (mahd,)) > 0:
                messagebox.showwarning("Trùng mã", f"Hóa đơn {mahd} đã tồn tại.", parent=win)
                return

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
                # (Hàm invoice_detail_window đã được định nghĩa ở trên)
                invoice_detail_window(root, mahd, refresh, trangthai)

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm hóa đơn: {e}", parent=win)

# ---------- DELETE INVOICE (HELPER) ----------
def delete_invoice(tree, refresh):
    """Xóa hóa đơn (sử dụng helper safe_delete, có xử lý chi tiết hóa đơn)."""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn hóa đơn cần xóa!")
        return

    mahd = selected[0] # Lấy MaHD (iid)

    try:
        trang_thai = db.execute_scalar("SELECT TrangThai FROM HoaDon WHERE MaHD = ?", (mahd,))
        
        if trang_thai == 'Đã thanh toán': 
            messagebox.showwarning(
                "Không thể xóa", 
                f"Hóa đơn {mahd} đã được thanh toán và không thể xóa."
            )
            return

        count = db.execute_scalar("SELECT COUNT(*) FROM ChiTietHoaDon WHERE MaHD = ?", (mahd,)) or 0

        if count > 0:
            confirm = messagebox.askyesno(
                "Xác nhận",
                f"Hóa đơn {mahd} có {count} mặt hàng.\n"
                "Bạn có muốn xóa toàn bộ chi tiết trước khi xóa hóa đơn không?"
            )
            if not confirm:
                return
            
            if not db.execute_query("DELETE FROM ChiTietHoaDon WHERE MaHD = ?", (mahd,)):
                messagebox.showerror("Lỗi", "Không thể xóa chi tiết hóa đơn, thao tác đã hủy.")
                return

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

# =========================================================
# HÀM CHÍNH (MAIN MODULE)
# =========================================================

# SỬA 3: Thay đổi chữ ký hàm (bỏ role, thêm on_back_callback)
def create_invoices_module(parent_frame, username, on_back_callback):
    
    # SỬA 4: Xóa các lệnh điều khiển cửa sổ (root)
    # clear_window(root)
    setup_styles()
    # root.title("Quản lý Hóa đơn")
    # root.configure(bg="#f5e6ca")
    # center_window(root, 1200, 700, offset_y=-60)
    # root.minsize(1000, 550)

    # SỬA 6: Tạo frame chính của module
    module_frame = tk.Frame(parent_frame, bg="#f5e6ca")
    # KHÔNG PACK() ở đây, để mainmenu kiểm soát

    # SỬA 7: Gắn Header vào module_frame
    header = tk.Frame(module_frame, bg="#4b2e05", height=70)
    header.pack(fill="x")
    tk.Label(header, text="🧾 QUẢN LÝ HÓA ĐƠN", bg="#4b2e05", fg="white",
             font=("Segoe UI", 16, "bold")).pack(pady=12)

    # SỬA 8: Gắn Top frame vào module_frame
    top = tk.Frame(module_frame, bg="#f5e6ca")
    top.pack(fill="x", pady=6, padx=12)

    search_var = tk.StringVar()
    ttk.Label(top, text="🔎 Tìm:", background="#f5e6ca").pack(side="left", padx=(0,6))
    entry_search = ttk.Entry(top, textvariable=search_var, width=30)
    entry_search.pack(side="left", padx=(0,6))

    status_label_var = tk.StringVar(value="")
    status_label = ttk.Label(top, textvariable=status_label_var, font=("Arial", 10, "italic"), background="#f5e6ca", foreground="blue")
    status_label.pack(side="left", padx=10)

    # SỬA 9: Gắn Treeview vào module_frame
    cols = ("MaHD", "NgayLap", "MaNV", "TenKH", "TongTien", "TrangThai", "GhiChu")
    tree = ttk.Treeview(module_frame, columns=cols, show="headings", height=16)
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
            
            fill_treeview_chunked(
                tree_widget, 
                tree_data, 
                on_complete=lambda: status_var.set(f"Đã tải {len(rows)} hóa đơn.")
            )

        except Exception as e:
            status_var.set("Lỗi tải!")
            messagebox.showerror("Lỗi", f"Không thể tải danh sách hóa đơn: {e}")

    def refresh():
        load_data(tree, status_label_var, search_var.get().strip())

    ttk.Button(top, text="🔄 Tải lại", style="Close.TButton",
             command=refresh).pack(side="left", padx=5)

    # SỬA 10: Truyền 'parent_frame' (cha của Toplevel) và 'username' (nghiệp vụ)
    ttk.Button(top, text="➕ Thêm", style = "Add.TButton",
             command=lambda: add_invoice(parent_frame, username, refresh)).pack(side="left", padx=6)
    
    # SỬA 11: Xóa 'role' khỏi lệnh gọi (vì đã sửa hàm open_invoice_detail)
    ttk.Button(top, text="✏️ Sửa", style="Edit.TButton",
             command=lambda: open_invoice_detail(tree, refresh)).pack(side="left", padx=6)
    
    ttk.Button(top, text="🗑 Xóa", style="Delete.TButton",
             command=lambda: delete_invoice(tree, refresh)).pack(side="left", padx=6)

    # SỬA 12: Sử dụng on_back_callback
    ttk.Button(top, text="⬅ Quay lại", style="Close.TButton",
             command=on_back_callback).pack(side="right", padx=6)

    refresh()

    search_after = {"id": None}
    def on_search_change(event=None):
        if search_after["id"]:
            # SỬA 13: Dùng parent_frame (hoặc module_frame) để gọi .after()
            parent_frame.after_cancel(search_after["id"])
        search_after["id"] = parent_frame.after(250, refresh) 
    entry_search.bind("<KeyRelease>", on_search_change)

    def on_double_click(event):
        sel = tree.selection()
        if sel:
            # SỬA 14: Xóa 'role' khỏi lệnh gọi
            open_invoice_detail(tree, refresh)
    tree.bind("<Double-1>", on_double_click)
    
    # SỬA 15: Trả về frame chính của module
    return module_frame