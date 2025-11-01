# app/modules/invoices.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from decimal import Decimal, InvalidOperation
from datetime import datetime
from app import db

# SỬA: Xóa create_form_window và generate_next_mahd (vì không còn dùng)
from app.db import fetch_query, execute_query, execute_scalar
from app.theme import setup_styles
# from app.utils.utils import create_form_window
# SỬA: Xóa recalc_invoice_total (vì không còn sửa chi tiết)
from app.utils.business_helpers import safe_delete
# from app.utils.id_helpers import generate_next_mahd
from app.utils.treeview_helpers import fill_treeview_chunked

# =========================================================
# CÁC HÀM HELPER
# =========================================================

# ---------- UPDATE CUSTOMER POINTS (HELPER) ----------
# (Hàm này giữ nguyên vì pos.py đang import và sử dụng nó)
def update_customer_points(makh, tongtien):
    """
    Cập nhật điểm tích lũy cho khách hàng.
    Hàm này CHỈ NÊN được gọi SAU KHI thanh toán thành công.
    """
    try:
        config = db.configparser.ConfigParser()
        config.read('config.ini', encoding='utf-8')
        vnd_per_point = config.getint('BusinessLogic', 'VND_PER_POINT', fallback=10000)
        
        if vnd_per_point <= 0:
            vnd_per_point = 10000 

        if makh and tongtien > 0:
            diem_cong = int(float(tongtien) // vnd_per_point)
            
            if diem_cong > 0:
                query = "UPDATE KhachHang SET DiemTichLuy = DiemTichLuy + ? WHERE MaKH = ?"
                db.execute_query(query, (diem_cong, makh))
                
    except Exception as e:
        print(f"Lỗi cập nhật điểm khách hàng: {e}")

# ---------- INVOICE DETAIL WINDOW (SỬA LẠI THÀNH READ-ONLY) ----------
def invoice_detail_window(root, mahd, parent_refresh=None, trang_thai_hoa_don='Chưa thanh toán'):
    """
    SỬA: Cửa sổ CHỈ XEM chi tiết các mặt hàng trong hóa đơn.
    """
    win = tk.Toplevel(root)
    win.title(f"Chi tiết Hóa đơn {mahd}")
    # SỬA: Giao diện 1 cột, rộng hơn
    win.geometry("1000x520") 
    win.configure(bg="#f5f5f5")
    win.state('zoomed') 

    # SỬA: Chỉ còn 1 frame (frame Treeview)
    left = tk.Frame(win, bg="#f5f5f5")
    left.pack(side="left", fill="both", expand=True, padx=8, pady=8)

    status_label_var_detail = tk.StringVar(value="")
    status_label_detail = ttk.Label(left, textvariable=status_label_var_detail, font=("Arial", 10, "italic"), background="#f5f5f5", foreground="blue")
    status_label_detail.pack(anchor="w")

    # SỬA: Thêm cột GhiChu
    cols = ("MaSP", "TenSP", "SoLuong", "DonGia", "ThanhTien", "GhiChu")
    tree = ttk.Treeview(left, columns=cols, show="headings", height=20)
    headers = {
        "MaSP":"Mã SP", "TenSP":"Tên SP", "SoLuong":"SL", 
        "DonGia":"Đơn giá", "ThanhTien":"Thành tiền", "GhiChu": "Ghi chú (Tùy chọn)"
    }
    
    for c in cols:
        tree.heading(c, text=headers[c])
        # SỬA: Căn lề cho cột mới
        if c == 'TenSP':
            tree.column(c, anchor="center", width=260)
        elif c == 'GhiChu':
            tree.column(c, anchor="center", width=200)
        else:
            tree.column(c, anchor="center", width=120)
            
    tree.pack(fill="both", expand=True)
    
    # SỬA: XÓA TOÀN BỘ KHUNG BÊN PHẢI (RIGHT FRAME)
    # (right = tk.Frame(...) đã bị xóa)

    # SỬA: XÓA TẤT CẢ CÁC HÀM LOGIC CỦA KHUNG PHẢI
    # (on_product_select, calc_total_preview, add_item, delete_item, edit_qty, perform_payment đã bị xóa)

    def load_items():
        status_label_var_detail.set("Đang tải chi tiết...")
        tree.update_idletasks()
        try:
            # SỬA: Thêm c.GhiChu và c.ChiTietID (PK mới)
            query = """
                SELECT c.ChiTietID, c.MaSP, s.TenSP, c.SoLuong, c.DonGia, c.ThanhTien, c.GhiChu 
                FROM ChiTietHoaDon c 
                JOIN SANPHAM s ON c.MaSP = s.MaSP 
                WHERE c.MaHD=?
            """
            rows = db.fetch_query(query, (mahd,))
            
            tree_data = []
            for r in rows:
                ghichu = r["GhiChu"] or ""
                # SỬA: Thêm GhiChu vào tuple
                values_tuple = (
                    r["MaSP"].strip(), 
                    r["TenSP"], 
                    r["SoLuong"], 
                    f"{int(r['DonGia']):,}", 
                    f"{int(r['ThanhTien']):,}",
                    ghichu 
                )
                # SỬA: Dùng ChiTietID (PK mới) làm iid
                tree_data.append({"iid": r['ChiTietID'], "values": values_tuple}) 

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

    # SỬA: XÓA KHUNG NÚT BẤM (btnf) VÀ CÁC NÚT (Add, Edit, Delete, Thanh toán)
    # (btnf = tk.Frame(right, ...) đã bị xóa)
    
    # SỬA: Chỉ thêm nút "Đóng" vào frame 'left'
    ttk.Button(left, text="Đóng", style="Close.TButton", command=win.destroy).pack(side="bottom", pady=10, ipadx=10)

    # (Khối "is_read_only" đã bị xóa)

    # Tải chi tiết
    load_items()

# ---------- OPEN INVOICE DETAIL (HELPER) ----------
# (Hàm này giữ nguyên, không cần sửa)
def open_invoice_detail(tree, parent_refresh):
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Chưa chọn", "Vui lòng chọn hóa đơn để xem chi tiết.")
        return
    mahd = sel[0] 
    
    trang_thai = db.execute_scalar("SELECT TrangThai FROM HoaDon WHERE MaHD = ?", (mahd,))
    
    invoice_detail_window(tree.master, mahd, parent_refresh, trang_thai)

# ---------- SỬA: XÓA TOÀN BỘ HÀM add_invoice ----------
# (def add_invoice(...) đã bị xóa)

# ---------- DELETE INVOICE (HELPER) ----------
# (Hàm này giữ nguyên, Admin vẫn cần quyền xóa)
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

def create_invoices_module(parent_frame, employee_id, on_back_callback):
    
    setup_styles()
    module_frame = tk.Frame(parent_frame, bg="#f5e6ca")

    header = tk.Frame(module_frame, bg="#4b2e05", height=70)
    header.pack(fill="x")
    tk.Label(header, text="🧾 QUẢN LÝ HÓA ĐƠN", bg="#4b2e05", fg="white",
             font=("Segoe UI", 16, "bold")).pack(pady=12)

    top = tk.Frame(module_frame, bg="#f5e6ca")
    top.pack(fill="x", pady=6, padx=12)

    search_var = tk.StringVar()
    ttk.Label(top, text="🔎 Tìm:", background="#f5e6ca").pack(side="left", padx=(0,6))
    entry_search = ttk.Entry(top, textvariable=search_var, width=30)
    entry_search.pack(side="left", padx=(0,6))

    status_label_var = tk.StringVar(value="")
    status_label = ttk.Label(top, textvariable=status_label_var, font=("Arial", 10, "italic"), background="#f5e6ca", foreground="blue")
    status_label.pack(side="left", padx=10)

    # SỬA: Cập nhật Treeview chính, thêm GhiChu
    cols = ("MaHD", "NgayLap", "MaNV", "TenKH", "TongTien", "GiamGia", "ThanhTien", "TrangThai", "GhiChu")
    tree = ttk.Treeview(module_frame, columns=cols, show="headings", height=16)
    headers = {
        "MaHD": "Mã HD",
        "NgayLap": "Ngày lập",
        "MaNV": "Mã NV",
        "TenKH": "Khách hàng",
        "TongTien": "Tổng tiền (đ)",
        "GiamGia": "Giảm giá (đ)", # Thêm cột
        "ThanhTien": "Thực thu (đ)", # Thêm cột
        "TrangThai": "Trạng thái",
        "GhiChu": "Ghi Chú (HD)"
    }
    for c in cols:
        tree.heading(c, text=headers[c])
        tree.column(c, anchor="center", width=120)
        
    tree.column("NgayLap", width=140)
    tree.column("TenKH", width=150, anchor="center")
    
    tree.pack(fill="both", expand=True, padx=12, pady=(6,12))

    def load_data(tree_widget, status_var, keyword=None):
        status_var.set("Đang tải...")
        tree_widget.update_idletasks()
        try:
            # SỬA: Cập nhật Query, lấy GiamGia, ThanhTien
            sql = """
            SELECT 
                h.MaHD, h.NgayLap, h.MaNV, k.TenKH, 
                h.TongTien, h.GiamGia, h.ThanhTien, 
                h.TrangThai, h.GhiChu
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
                giam = f"{int(r['GiamGia']):,}" if r['GiamGia'] is not None else "0"
                thu = f"{int(r['ThanhTien']):,}" if r['ThanhTien'] is not None else "0"
                
                # SỬA: Cập nhật Tuple
                values_tuple = (
                    r["MaHD"].strip(),
                    ngay,
                    r["MaNV"].strip(),
                    r["TenKH"] if r["TenKH"] else "",
                    tong,
                    giam,
                    thu,
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

    # SỬA: XÓA NÚT "Thêm"
    # ttk.Button(top, text="➕ Thêm", ...).pack(...)
    
    # SỬA: ĐỔI TÊN NÚT "Sửa"
    ttk.Button(top, text="🔍 Xem Chi tiết", style="Edit.TButton",
             command=lambda: open_invoice_detail(tree, refresh)).pack(side="left", padx=6)
    
    ttk.Button(top, text="🗑 Xóa", style="Delete.TButton",
             command=lambda: delete_invoice(tree, refresh)).pack(side="left", padx=6)

    ttk.Button(top, text="⬅ Quay lại", style="Close.TButton",
             command=on_back_callback).pack(side="right", padx=6)

    refresh()

    search_after = {"id": None}
    def on_search_change(event=None):
        if search_after["id"]:
            parent_frame.after_cancel(search_after["id"])
        search_after["id"] = parent_frame.after(250, refresh) 
    entry_search.bind("<KeyRelease>", on_search_change)

    def on_double_click(event):
        sel = tree.selection()
        if sel:
            open_invoice_detail(tree, refresh)
    tree.bind("<Double-1>", on_double_click)
    
    return module_frame