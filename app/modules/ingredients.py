# app/modules/ingredients.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from decimal import Decimal, InvalidOperation
from app import db
from app.theme import setup_styles

# Import các helper chuẩn của dự án
from app.db import fetch_query, execute_query, execute_scalar
from app.utils.utils import clear_window, create_form_window, go_back, center_window
from app.utils.business_helpers import safe_delete
from app.utils.treeview_helpers import fill_treeview_chunked
from app.utils.id_helpers import generate_next_manl # Helper mới

# --- HÀM CHÍNH HIỂN THỊ MODULE ---
def show_ingredients_module(root, username=None, role=None):
    """Giao diện chính cho Module Quản lý Nguyên Liệu (Kho)"""
    clear_window(root)
    setup_styles()
    root.title("📦 Quản lý Kho (Nguyên Liệu)")
    root.configure(bg="#f5e6ca")

    center_window(root, 1000, 600, offset_y=-60)
    root.minsize(900, 500)

    # --- Header ---
    header = tk.Frame(root, bg="#4b2e05", height=70)
    header.pack(fill="x")
    tk.Label(header, text="📦 QUẢN LÝ KHO (NGUYÊN LIỆU)", bg="#4b2e05", fg="white",
             font=("Segoe UI", 16, "bold")).pack(pady=12)

    # --- Thanh điều khiển (Control Frame) ---
    top_frame = tk.Frame(root, bg="#f9fafb")
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
    ttk.Button(btn_frame, text="✏️ Sửa", style="Edit.TButton",
               command=lambda: edit_ingredient(tree, refresh_data)).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="🗑 Xóa", style="Delete.TButton",
               command=lambda: delete_ingredient(tree, refresh_data)).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="⬅ Quay lại", style="Close.TButton",
               command=lambda: go_back(root, username, role)).pack(side="left", padx=5)

    # --- Frame Lọc (Bên trái) ---
    filter_frame = tk.Frame(top_frame, bg="#f9fafb")
    filter_frame.pack(side="left", fill="x", expand=True)

    tk.Label(filter_frame, text="🔎 Tìm NL:", font=("Arial", 11),
             bg="#f9fafb").pack(side="left", padx=(5, 2))
    search_var = tk.StringVar()
    entry_search = ttk.Entry(filter_frame, textvariable=search_var, width=30) 
    entry_search.pack(side="left", padx=5, fill="x", expand=True) 

    status_label_var = tk.StringVar(value="")
    status_label = ttk.Label(filter_frame, textvariable=status_label_var, font=("Arial", 10, "italic"), background="#f9fafb", foreground="blue")
    status_label.pack(side="left", padx=10)

    # ===== TREEVIEW =====
    columns = ("MaNL", "TenNL", "DonVi", "SoLuongTon")
    headers = {
        "MaNL": "Mã NL",
        "TenNL": "Tên Nguyên Liệu",
        "DonVi": "Đơn vị tính",
        "SoLuongTon": "Số lượng tồn kho"
    }

    tree = ttk.Treeview(root, columns=columns, show="headings", height=15)
    for col, text in headers.items():
        tree.heading(col, text=text)
        tree.column(col, anchor="center", width=150)
    tree.column("TenNL", anchor="w", width=300) # Cột Tên NL rộng hơn
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    # ===== HÀM TẢI DỮ LIỆU (Đồng bộ) =====
    def load_data(tree_widget, status_var, keyword=None):
        status_var.set("Đang tải dữ liệu...")
        tree_widget.update_idletasks() 
        
        query = "SELECT MaNL, TenNL, DonVi, SoLuongTon FROM NguyenLieu"
        params = ()
        if keyword:
            kw = f"%{keyword.strip()}%"
            query += " WHERE MaNL LIKE ? OR TenNL LIKE ? OR DonVi LIKE ?"
            params = (kw, kw, kw)
        query += " ORDER BY TenNL"

        try:
            rows = db.fetch_query(query, params)
            tree_data = []
            for r in rows:
                values_tuple = (
                    r['MaNL'], 
                    r['TenNL'], 
                    r['DonVi'], 
                    # Định dạng số lượng tồn (hiển thị 3 số lẻ nếu cần)
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

    # ===== HÀM TIỆN ÍCH =====
    def refresh_data():
        keyword = search_var.get().strip()
        load_data(tree, status_label_var, keyword)
    
    def on_search_change(*args):
        refresh_data()
    search_var.trace_add("write", on_search_change)

    # Tải lần đầu
    refresh_data()

# ==============================================================
#  HÀM CRUD VÀ NGHIỆP VỤ (Định nghĩa bên ngoài)
# ==============================================================

def add_ingredient(refresh_func):
    """Thêm nguyên liệu mới (SoLuongTon = 0)"""
    win, form = create_form_window("➕ Thêm Nguyên Liệu Mới", "400x250")
    
    ttk.Label(form, text="Mã NL:", background="#f8f9fa").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    entry_manl = ttk.Entry(form)
    entry_manl.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    # Gợi ý mã
    manl_auto = generate_next_manl(db.cursor)
    entry_manl.insert(0, manl_auto)

    ttk.Label(form, text="Tên Nguyên Liệu:", background="#f8f9fa").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    entry_tennl = ttk.Entry(form)
    entry_tennl.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

    ttk.Label(form, text="Đơn vị (kg, g, ml):", background="#f8f9fa").grid(row=2, column=0, sticky="w", padx=5, pady=5)
    entry_donvi = ttk.Entry(form)
    entry_donvi.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

    form.grid_columnconfigure(1, weight=1)

    def submit():
        manl = entry_manl.get().strip().upper()
        tennl = entry_tennl.get().strip()
        donvi = entry_donvi.get().strip()
        
        if not manl or not tennl or not donvi:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập đầy đủ Mã, Tên và Đơn vị.", parent=win)
            return

        # Kiểm tra trùng
        if db.execute_scalar("SELECT COUNT(*) FROM NguyenLieu WHERE MaNL = ?", (manl,)):
            messagebox.showwarning("Trùng mã", f"Mã NL '{manl}' đã tồn tại.", parent=win)
            return

        query = "INSERT INTO NguyenLieu (MaNL, TenNL, DonVi, SoLuongTon) VALUES (?, ?, ?, 0)"
        if db.execute_query(query, (manl, tennl, donvi)):
            messagebox.showinfo("Thành công", f"Đã thêm nguyên liệu '{tennl}'.", parent=win)
            refresh_func()
            win.destroy()
        
    ttk.Button(form, text="💾 Lưu", style="Add.TButton", command=submit)\
        .grid(row=3, column=0, columnspan=2, pady=10)

def edit_ingredient(tree, refresh_func):
    """Sửa Tên và Đơn vị của nguyên liệu"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn nguyên liệu cần sửa!")
        return
    
    manl = selected[0]
    # Lấy dữ liệu từ DB (chính xác hơn TreeView)
    data = db.fetch_query("SELECT TenNL, DonVi FROM NguyenLieu WHERE MaNL = ?", (manl,))
    if not data:
        messagebox.showerror("Lỗi", "Không tìm thấy nguyên liệu.")
        return
    
    current = data[0]
    win, form = create_form_window(f"✏️ Sửa Nguyên Liệu [${manl}$]", "400x200")

    ttk.Label(form, text="Tên Nguyên Liệu:", background="#f8f9fa").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    entry_tennl = ttk.Entry(form)
    entry_tennl.insert(0, current['TenNL'])
    entry_tennl.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    ttk.Label(form, text="Đơn vị (kg, g, ml):", background="#f8f9fa").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    entry_donvi = ttk.Entry(form)
    entry_donvi.insert(0, current['DonVi'])
    entry_donvi.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

    form.grid_columnconfigure(1, weight=1)

    def submit():
        tennl = entry_tennl.get().strip()
        donvi = entry_donvi.get().strip()
        
        if not tennl or not donvi:
            messagebox.showwarning("Thiếu thông tin", "Tên và Đơn vị không được trống.", parent=win)
            return

        query = "UPDATE NguyenLieu SET TenNL = ?, DonVi = ? WHERE MaNL = ?"
        if db.execute_query(query, (tennl, donvi, manl)):
            messagebox.showinfo("Thành công", f"Đã cập nhật nguyên liệu '{tennl}'.", parent=win)
            refresh_func()
            win.destroy()
        
    ttk.Button(form, text="💾 Cập nhật", style="Add.TButton", command=submit)\
        .grid(row=2, column=0, columnspan=2, pady=10)

def restock_ingredient(tree, refresh_func):
    """Nhập kho (Tăng SoLuongTon)"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn nguyên liệu để nhập kho!")
        return
    
    manl = selected[0]
    tennl = tree.item(manl, "values")[1]
    
    try:
        # Dùng simpledialog để hỏi số lượng (float)
        qty = simpledialog.askfloat(
            "📦 Nhập kho", 
            f"Nhập số lượng THÊM VÀO KHO cho:\n\n{tennl} (Mã: {manl})",
            parent=tree.master,
            minvalue=0.001
        )
        
        if qty is None or qty <= 0:
            return # Người dùng hủy

        # 1. Cập nhật bảng NguyenLieu
        query_update = "UPDATE NguyenLieu SET SoLuongTon = SoLuongTon + ? WHERE MaNL = ?"
        
        # 2. Ghi lại lịch sử nhập
        query_log = "INSERT INTO InventoryMovements (MaNL, ChangeQty, MovementType) VALUES (?, ?, 'purchase')"
        
        if db.execute_query(query_update, (qty, manl)) and \
           db.execute_query(query_log, (manl, qty)):
            messagebox.showinfo("Thành công", f"Đã nhập thêm {qty} {tree.item(manl, 'values')[2]} vào kho.")
            refresh_func()
        else:
            messagebox.showerror("Lỗi", "Không thể cập nhật kho (lỗi SQL).")
            
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể nhập kho: {e}")

def delete_ingredient(tree, refresh_func):
    """Xóa nguyên liệu (dùng safe_delete)"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn nguyên liệu cần xóa!")
        return
    
    manl = selected[0]
    
    # safe_delete sẽ tự động bắt lỗi khóa ngoại (nếu NL đã dùng trong CongThuc)
    safe_delete(
        table_name="NguyenLieu",
        key_column="MaNL",
        key_value=manl,
        cursor=db.cursor,
        conn=db.conn,
        refresh_func=refresh_func,
        item_label="nguyên liệu"
    )