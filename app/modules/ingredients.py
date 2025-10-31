# app/modules/ingredients.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from decimal import Decimal, InvalidOperation
from app import db
from app.theme import setup_styles

# Import các helper chuẩn của dự án
from app.db import fetch_query, execute_query, execute_scalar
# SỬA 1: Xóa go_back, clear_window, center_window
from app.utils.utils import create_form_window
from app.utils.business_helpers import safe_delete
from app.utils.treeview_helpers import fill_treeview_chunked
from app.utils.id_helpers import generate_next_manl 

# --- TỪ ĐIỂN NGUYÊN LIỆU (Giữ nguyên) ---
INGREDIENT_MAP = {
    "Cà phê hạt": "kg", "Cà phê bột": "kg", "Cà phê (phin giấy)": "gói",
    "Sữa đặc": "lon", "Sữa tươi": "l", "Sữa (ml)": "ml", "Kem béo (Rich)": "l",
    "Kem (Whipping Cream)": "l", "Sữa chua": "kg", "Đường cát": "kg",
    "Đường nước": "ml", "Đường phèn": "kg", "Siro Caramel": "ml", "Siro Vani": "ml",
    "Siro Bạc hà": "ml", "Siro Dâu": "ml", "Mật ong": "ml", "Sốt Chocolate": "kg",
    "Trà đen": "kg", "Trà lài": "kg", "Trà ô long": "kg", "Trà túi lọc": "gói",
    "Bột Matcha": "g", "Bột Cacao": "g", "Bột Frappe (Base)": "kg", "Cam": "kg",
    "Chanh": "kg", "Dâu tây": "kg", "Đào (ngâm)": "hộp", "Vải (ngâm)": "hộp",
    "Bơ": "kg", "Xoài": "kg", "Đá viên": "kg", "Nước lọc": "l", "Trân châu": "kg",
    "Bánh Croissant": "cái", "Bánh (khác)": "cái", "Ống hút": "hộp", "Ly (nhựa)": "cái",
}
INGREDIENT_NAMES_LIST = sorted(list(INGREDIENT_MAP.keys()))
UNITS_LIST = sorted(list(set(INGREDIENT_MAP.values())))


# --- HÀM CHÍNH HIỂN THỊ MODULE ---
# SỬA 2: Đổi tên hàm và chữ ký hàm (bỏ username, role)
def create_ingredients_module(parent_frame, on_back_callback):
    """Giao diện chính cho Module Quản lý Nguyên Liệu (Kho)"""
    
    # SỬA 3: Xóa các lệnh điều khiển cửa sổ (root)
    # clear_window(root)
    setup_styles()
    # root.title("📦 Quản lý Kho (Nguyên Liệu)")
    # root.configure(bg="#f5e6ca")
    # center_window(root, 1300, 600, offset_y=-60)
    # root.minsize(1200, 600)

    # SỬA 4: Tạo frame chính bên trong parent_frame
    module_frame = tk.Frame(parent_frame, bg="#f5e6ca")
    # KHÔNG PACK() ở đây, để mainmenu kiểm soát

    # SỬA 5: Gắn các widget con vào 'module_frame'
    
    # --- Header ---
    header = tk.Frame(module_frame, bg="#4b2e05", height=70)
    header.pack(fill="x")
    tk.Label(header, text="📦 QUẢN LÝ KHO (NGUYÊN LIỆU)", bg="#4b2e05", fg="white",
             font=("Segoe UI", 16, "bold")).pack(pady=12)

    # --- Thanh điều khiển (Control Frame) ---
    top_frame = tk.Frame(module_frame, bg="#f9fafb")
    top_frame.pack(fill="x", pady=10, padx=10) 

    # --- Frame Nút (Bên phải) - Đồng bộ layout ---
    btn_frame = tk.Frame(top_frame, bg="#f9fafb")
    btn_frame.pack(side="right", anchor="n", padx=(10, 0))
    
    ttk.Button(btn_frame, text="🔄 Tải lại", style="Close.TButton",
             command=lambda: refresh_data()).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="➕ Thêm Mới", style="Add.TButton",
             command=lambda: add_ingredient(refresh_data)).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="📦 Nhập kho", style="Add.TButton",
             command=lambda: restock_ingredient(tree, refresh_data)).pack(side="left", padx=5)
    
    ttk.Button(btn_frame, text="🔧 Điều chỉnh", style="Edit.TButton",
             command=lambda: adjust_inventory(tree, refresh_data)).pack(side="left", padx=5)
    
    ttk.Button(btn_frame, text="✏️ Sửa", style="Edit.TButton",
             command=lambda: edit_ingredient(tree, refresh_data)).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="🗑 Xóa", style="Delete.TButton",
             command=lambda: delete_ingredient(tree, refresh_data)).pack(side="left", padx=5)
    
    # SỬA 6: Cập nhật nút "Quay lại"
    ttk.Button(btn_frame, text="⬅ Quay lại", style="Close.TButton",
             command=on_back_callback).pack(side="left", padx=5)

    # --- Frame Lọc (Bên trái) ---
    filter_frame = tk.Frame(top_frame, bg="#f9fafb")
    filter_frame.pack(side="left", fill="x", expand=True)
    # (Code Frame Lọc giữ nguyên)
    tk.Label(filter_frame, text="🔎 Tìm NL:", font=("Arial", 11),
           bg="#f9fafb").pack(side="left", padx=(5, 2))
    search_var = tk.StringVar()
    entry_search = ttk.Entry(filter_frame, textvariable=search_var, width=30) 
    entry_search.pack(side="left", padx=5, fill="x", expand=True) 
    status_label_var = tk.StringVar(value="")
    status_label = ttk.Label(filter_frame, textvariable=status_label_var, font=("Arial", 10, "italic"), background="#f9fafb", foreground="blue")
    status_label.pack(side="left", padx=10)

    # ===== TREEVIEW (Gắn vào module_frame) =====
    columns = ("MaNL", "TenNL", "DonVi", "SoLuongTon")
    headers = {
        "MaNL": "Mã NL", "TenNL": "Tên Nguyên Liệu",
        "DonVi": "Đơn vị tính", "SoLuongTon": "Số lượng tồn kho"
    }
    tree = ttk.Treeview(module_frame, columns=columns, show="headings", height=15)
    for col, text in headers.items():
        tree.heading(col, text=text)
        tree.column(col, anchor="center", width=150)
    tree.column("TenNL", anchor="center", width=300) 
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    # ===== HÀM TẢI DỮ LIỆU (Giữ nguyên) =====
    def load_data(tree_widget, status_var, keyword=None):
        status_var.set("Đang tải dữ liệu...")
        tree_widget.update_idletasks() 
        query = "SELECT MaNL, TenNL, DonVi, SoLuongTon FROM NguyenLieu"
        params = ()
        if keyword:
            kw = f"%{keyword.strip()}%"
            query += " WHERE MaNL LIKE ? OR TenNL LIKE ? OR DonVi LIKE ?"
            params = (kw, kw, kw)
        query += " ORDER BY MaNL" # Sắp xếp theo MaNL
        try:
            rows = db.fetch_query(query, params)
            tree_data = []
            for r in rows:
                values_tuple = (
                    r['MaNL'], 
                    r['TenNL'], 
                    r['DonVi'], 
                    f"{Decimal(r['SoLuongTon']):.3f}".rstrip('0').rstrip('.')
                )
                tree_data.append({"iid": r['MaNL'], "values": values_tuple})
            fill_treeview_chunked(
                tree_widget, 
                tree_data, 
                on_complete=lambda: status_var.set(f"Đã tải {len(rows)} nguyên liệu.")
            )
        except Exception as e:
            status_var.set("Lỗi tải!")
            messagebox.showerror("Lỗi", f"Không thể tải dữ liệu nguyên liệu: {e}")

    # ===== HÀM TIỆN ÍCH (Giữ nguyên) =====
    def refresh_data():
        keyword = search_var.get().strip()
        load_data(tree, status_label_var, keyword)
    
    def on_search_change(*args):
        refresh_data()
    search_var.trace_add("write", on_search_change)
    refresh_data() # Tải lần đầu

    # SỬA 7: Trả về frame chính
    return module_frame

# ==============================================================
#  HÀM CRUD VÀ NGHIỆP VỤ (KHÔNG CẦN THAY ĐỔI)
#  (Các hàm này đều dùng Toplevel hoặc tree.master, 
#  chúng độc lập với logic 'root' nên giữ nguyên)
# ==============================================================

# --- HÀM ADD_INGREDIENT (Giữ nguyên) ---
def add_ingredient(refresh_func):
    win, form = create_form_window("➕ Thêm Nguyên Liệu Mới", "400x250")
    
    ttk.Label(form, text="Mã NL:", background="#f8f9fa").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    entry_manl = ttk.Entry(form)
    entry_manl.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    manl_auto = generate_next_manl(db.cursor)
    entry_manl.insert(0, manl_auto)

    ttk.Label(form, text="Tên Nguyên Liệu:", background="#f8f9fa").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    cb_tennl = ttk.Combobox(form, values=INGREDIENT_NAMES_LIST, font=("Arial", 11))
    cb_tennl.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

    ttk.Label(form, text="Đơn vị tính:", background="#f8f9fa").grid(row=2, column=0, sticky="w", padx=5, pady=5)
    cb_donvi = ttk.Combobox(form, values=UNITS_LIST, font=("Arial", 11))
    cb_donvi.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
    form.grid_columnconfigure(1, weight=1)

    def on_name_change(event=None):
        ten = cb_tennl.get().strip()
        default_unit = None
        for key, unit in INGREDIENT_MAP.items():
            if key.lower() == ten.lower():
                default_unit = unit
                break
        if default_unit:
            cb_donvi.set(default_unit)

    cb_tennl.bind("<KeyRelease>", on_name_change)
    cb_tennl.bind("<<ComboboxSelected>>", on_name_change)

    def submit():
        manl = entry_manl.get().strip().upper()
        tennl = cb_tennl.get().strip() 
        donvi = cb_donvi.get().strip() 
        if not manl or not tennl or not donvi:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập đầy đủ Mã, Tên và Đơn vị.", parent=win)
            return
        if db.execute_scalar("SELECT COUNT(*) FROM NguyenLieu WHERE MaNL = ?", (manl,)):
            messagebox.showwarning("Trùng mã", f"Mã NL '{manl}' đã tồn tại.", parent=win)
            return
        query = "INSERT INTO NguyenLieu (MaNL, TenNL, DonVi, SoLuongTon) VALUES (?, ?, ?, 0)"
        if db.execute_query(query, (manl, tennl, donvi)):
            messagebox.showinfo("Thành công", f"Đã thêm nguyên liệu '{tennl}'.", parent=win)
            refresh_func()
            win.destroy()
        
    btn_frame = tk.Frame(win, bg="#f8f9fa")
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="💾 Lưu sản phẩm", style="Add.TButton",
             command=lambda: submit()).pack(ipadx=10, ipady=6)

# --- HÀM EDIT_INGREDIENT (Giữ nguyên) ---
def edit_ingredient(tree, refresh_func):
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn nguyên liệu cần sửa!")
        return
    manl = selected[0]
    data = db.fetch_query("SELECT TenNL, DonVi FROM NguyenLieu WHERE MaNL = ?", (manl,))
    if not data:
        messagebox.showerror("Lỗi", "Không tìm thấy nguyên liệu.")
        return
    
    current = data[0]
    win, form = create_form_window(f"✏️ Sửa Nguyên Liệu [{manl}]", "400x200")

    ttk.Label(form, text="Tên Nguyên Liệu:", background="#f8f9fa").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    cb_tennl = ttk.Combobox(form, values=INGREDIENT_NAMES_LIST, font=("Arial", 11))
    cb_tennl.set(current['TenNL'])
    cb_tennl.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    ttk.Label(form, text="Đơn vị tính:", background="#f8f9fa").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    cb_donvi = ttk.Combobox(form, values=UNITS_LIST, font=("Arial", 11))
    cb_donvi.set(current['DonVi']) 
    cb_donvi.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
    form.grid_columnconfigure(1, weight=1)

    def on_name_change(event=None):
        ten = cb_tennl.get().strip()
        default_unit = None
        for key, unit in INGREDIENT_MAP.items():
            if key.lower() == ten.lower():
                default_unit = unit
                break
        if default_unit:
            cb_donvi.set(default_unit)
    cb_tennl.bind("<KeyRelease>", on_name_change)
    cb_tennl.bind("<<ComboboxSelected>>", on_name_change)

    def save():
        tennl = cb_tennl.get().strip() 
        donvi = cb_donvi.get().strip() 
        if not tennl or not donvi:
            messagebox.showwarning("Thiếu thông tin", "Tên và Đơn vị không được trống.", parent=win)
            return
        query = "UPDATE NguyenLieu SET TenNL = ?, DonVi = ? WHERE MaNL = ?"
        if db.execute_query(query, (tennl, donvi, manl)):
            messagebox.showinfo("Thành công", f"Đã cập nhật nguyên liệu '{tennl}'.", parent=win)
            refresh_func()
            win.destroy()
        
    btn_frame = tk.Frame(win, bg="#f8f9fa")
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="💾 Lưu sản phẩm", style="Add.TButton",
             command=lambda: save()).pack(ipadx=10, ipady=6)

# --- HÀM RESTOCK_INGREDIENT (Giữ nguyên) ---
def restock_ingredient(tree, refresh_func):
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn nguyên liệu để nhập kho!")
        return
    manl = selected[0]
    values = tree.item(manl, "values")
    tennl = values[1]
    donvi = values[2]
    
    try:
        qty = simpledialog.askfloat(
            "📦 Nhập kho", 
            f"Nhập số lượng THÊM VÀO KHO cho:\n\n{tennl} (Mã: {manl})",
            parent=tree.master,
            minvalue=0.001
        )
        if qty is None or qty <= 0:
            return 
        query_update = "UPDATE NguyenLieu SET SoLuongTon = SoLuongTon + ? WHERE MaNL = ?"
        query_log = "INSERT INTO InventoryMovements (MaNL, ChangeQty, MovementType) VALUES (?, ?, 'purchase')"
        
        if db.execute_query(query_update, (qty, manl)) and \
           db.execute_query(query_log, (manl, qty)):
            messagebox.showinfo("Thành công", f"Đã nhập thêm {qty} {donvi} {tennl} vào kho.")
            refresh_func()
        else:
            messagebox.showerror("Lỗi", "Không thể cập nhật kho (lỗi SQL).")
            
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể nhập kho: {e}")

# --- HÀM ADJUST_INVENTORY (Giữ nguyên) ---
def adjust_inventory(tree, refresh_func):
    """Điều chỉnh tồn kho (Hủy, hỏng, kiểm kê sai)"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn nguyên liệu để điều chỉnh!")
        return
    
    manl = selected[0]
    values = tree.item(manl, "values")
    tennl = values[1]
    donvi = values[2]

    try:
        # 1. Lấy số lượng tồn kho CŨ (chính xác từ DB)
        current_qty_decimal = db.execute_scalar("SELECT SoLuongTon FROM NguyenLieu WHERE MaNL = ?", (manl,))
        if current_qty_decimal is None:
            messagebox.showerror("Lỗi", "Không tìm thấy nguyên liệu trong CSDL.")
            return
        
        current_qty = float(current_qty_decimal)

        # 2. Hỏi số lượng MỚI
        new_qty = simpledialog.askfloat(
            "🔧 Điều chỉnh kho", 
            f"Nhập số lượng TỒN KHO THỰC TẾ cho:\n\n{tennl} (Hiện tại: {current_qty} {donvi})",
            parent=tree.master,
            minvalue=0.0 # Cho phép đặt về 0
        )
        
        if new_qty is None:
            return # Người dùng hủy
        
        # 3. Tính toán chênh lệch
        change_qty = new_qty - current_qty # Sẽ là số âm nếu hủy kho
        
        if change_qty == 0:
            messagebox.showinfo("Thông báo", "Không có thay đổi.", parent=tree.master)
            return

        # 4. Cập nhật CSDL
        query_update = "UPDATE NguyenLieu SET SoLuongTon = ? WHERE MaNL = ?"
        query_log = "INSERT INTO InventoryMovements (MaNL, ChangeQty, MovementType) VALUES (?, ?, 'adjust')"
        
        if db.execute_query(query_update, (new_qty, manl)) and \
           db.execute_query(query_log, (manl, change_qty)):
            
            messagebox.showinfo("Thành công", f"Đã điều chỉnh kho {tennl}.\n"
                                          f"Tồn kho cũ: {current_qty} {donvi}\n"
                                          f"Tồn kho mới: {new_qty} {donvi}\n"
                                          f"Chênh lệch: {change_qty:.3f} {donvi}")
            refresh_func()
        else:
            messagebox.showerror("Lỗi", "Không thể điều chỉnh kho (lỗi SQL).")

    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể điều chỉnh kho: {e}")

# --- HÀM DELETE_INGREDIENT (Giữ nguyên) ---
def delete_ingredient(tree, refresh_func):
    """Xóa nguyên liệu (dùng safe_delete)"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn nguyên liệu cần xóa!")
        return
    
    manl = selected[0]
    
    safe_delete(
        table_name="NguyenLieu",
        key_column="MaNL",
        key_value=manl,
        cursor=db.cursor,
        conn=db.conn,
        refresh_func=refresh_func,
        item_label="nguyên liệu"
    )