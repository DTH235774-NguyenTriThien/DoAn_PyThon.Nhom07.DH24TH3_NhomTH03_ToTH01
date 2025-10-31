# app/modules/recipes.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from decimal import Decimal, InvalidOperation
from app import db
from app.theme import setup_styles

# Import các helper chuẩn của dự án
from app.db import fetch_query, execute_query, execute_scalar
# SỬA 1: Xóa các import không cần thiết (go_back, clear_window, v.v...)
# from app.utils.utils import clear_window, create_form_window, go_back, center_window
from app.utils.business_helpers import safe_delete
from app.utils.treeview_helpers import fill_treeview_chunked

# =========================================================
# TỪ ĐIỂN VÀ CACHE NGUYÊN LIỆU (Giữ nguyên)
# =========================================================

RECIPE_FOOD_MAP = {
    # Cà phê
    "Cà phê hạt": "g", "Cà phê bột": "g",
    # Sữa
    "Sữa đặc": "ml", "Sữa tươi": "ml", "Kem béo (Rich)": "ml",
    "Kem (Whipping Cream)": "ml", "Sữa chua": "g",
    # Đường / Siro
    "Đường cát": "g", "Đường nước": "ml", "Siro Caramel": "ml", "Siro Vani": "ml",
    "Siro Bạc hà": "ml", "Siro Dâu": "ml", "Mật ong": "ml", "Sốt Chocolate": "g",
    # Trà
    "Trà đen": "g", "Trà lài": "g", "Trà ô long": "g",
    "Bột Matcha": "g", "Bột Cacao": "g", "Bột Frappe (Base)": "g",
    # Trái cây (đã chuẩn hóa 'g')
    "Cam": "g", 
    "Chanh": "g", 
    "Dâu tây": "g", 
    "Dâu tây (tươi)": "g", 
    "Bơ": "g", 
    "Xoài": "g", 
    # Trái cây (ngâm)
    "Đào (ngâm)": "hộp", 
    "Vải (ngâm)": "hộp",
    # Khác
    "Trân châu": "g", 
    "Đá viên": "kg",
    "Muối": "g",
    "Đường": "g",
    "Đường phèn": "g",
    "Nước lọc": "ml",
}

# Biến cache tổng (chỉ chứa key)
_master_ingredient_keys = [] 
_ingredient_map = {} 

def load_ingredient_cache():
    """Tải và cache danh sách NGUYÊN LIỆU THỰC PHẨM (lọc bỏ Vật tư VÀ đơn vị cũ)"""
    global _ingredient_map, _master_ingredient_keys
    if not _ingredient_map:
        try:
            rows = db.fetch_query("SELECT MaNL, TenNL, DonVi FROM NguyenLieu ORDER BY TenNL")
            
            _ingredient_map = {}
            
            # Lọc nghiêm ngặt: Phải khớp cả Tên VÀ Đơn vị
            for r in rows:
                ten_nl = r['TenNL']
                don_vi = r['DonVi']
                
                # 1. Kiểm tra xem Tên có trong MAP chuẩn không
                if ten_nl in RECIPE_FOOD_MAP:
                    # 2. Kiểm tra xem Đơn vị có khớp với MAP chuẩn không
                    if RECIPE_FOOD_MAP[ten_nl] == don_vi:
                        # CHỈ KHI KHỚP CẢ 2, MỚI THÊM VÀO COMBOBOX
                        key = f"{r['MaNL'].strip()} - {ten_nl} ({don_vi})"
                        _ingredient_map[key] = r['MaNL'].strip()
            
            _master_ingredient_keys = sorted(_ingredient_map.keys())
            
        except Exception as e:
            print(f"Lỗi tải cache nguyên liệu: {e}")
            _ingredient_map = {}
            _master_ingredient_keys = []

# --- HÀM CHÍNH HIỂN THỊ MODULE ---
# SỬA 2: Đổi tên hàm
# SỬA 3: Thay đổi chữ ký hàm (bỏ username, role, on_exit_callback)
def create_recipes_module(parent_frame, on_back_callback):
    
    # SỬA 4: Xóa các lệnh điều khiển cửa sổ (root)
    # clear_window(root)
    setup_styles()
    # root.title("📜 Quản lý Công thức Sản phẩm")
    # root.configure(bg="#f5e6ca")
    # center_window(root, 1200, 700, offset_y=-60)
    # root.minsize(1000, 600)

    # SỬA 5: Tạo frame chính bên trong parent_frame
    module_frame = tk.Frame(parent_frame, bg="#f5e6ca")
    # KHÔNG PACK() ở đây, để mainmenu kiểm soát

    # SỬA 6: Gắn các widget con vào 'module_frame'

    # --- Header & Nút Quay lại ---
    header = tk.Frame(module_frame, bg="#4b2e05", height=70)
    header.pack(fill="x")
    tk.Label(header, text="📜 QUẢN LÝ CÔNG THỨC SẢN PHẨM", bg="#4b2e05", fg="white",
             font=("Segoe UI", 16, "bold")).pack(pady=12)
    
    top_frame = tk.Frame(module_frame, bg="#f9fafb")
    top_frame.pack(fill="x", pady=10, padx=10)
    
    # SỬA 7: Cập nhật nút "Quay lại"
    ttk.Button(top_frame, text="⬅ Quay lại", style="Close.TButton",
             command=on_back_callback).pack(side="right", padx=5)

    # --- Khung chứa 2 panel chính ---
    main_frame = tk.Frame(module_frame, bg="#f5e6ca")
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # --- KHUNG BÊN TRÁI (DANH SÁCH SẢN PHẨM) ---
    left_panel = tk.Frame(main_frame, bg="#f9fafb", relief="solid", borderwidth=1)
    left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))
    tk.Label(left_panel, text="1. Chọn Sản phẩm để xem/sửa công thức", 
             font=("Segoe UI", 12, "bold"), bg="#f9fafb", fg="#4b2e05").pack(pady=10)
    status_label_products = tk.StringVar(value="Đang tải sản phẩm...")
    ttk.Label(left_panel, textvariable=status_label_products, font=("Arial", 10, "italic"), 
              background="#f9fafb", foreground="blue").pack(anchor="w", padx=10)
    tree_products = ttk.Treeview(left_panel, columns=("MaSP", "TenSP", "DonGia"), show="headings", height=20)
    tree_products.heading("MaSP", text="Mã SP"); tree_products.heading("TenSP", text="Tên Sản Phẩm"); tree_products.heading("DonGia", text="Đơn giá")
    tree_products.column("MaSP", width=80, anchor="center"); tree_products.column("TenSP", width=250, anchor="w"); tree_products.column("DonGia", width=100, anchor="e")
    tree_products.pack(fill="both", expand=True, padx=10, pady=10)
    
    # --- KHUNG BÊN PHẢI (CÔNG THỨC CHI TIẾT) ---
    right_panel = tk.Frame(main_frame, bg="#f9fafb", relief="solid", borderwidth=1)
    right_panel.pack(side="right", fill="both", expand=True, padx=(5, 0))
    lbl_recipe_title = tk.Label(right_panel, text="2. Công thức cho: [Chưa chọn]", 
                                 font=("Segoe UI", 12, "bold"), bg="#f9fafb", fg="#4b2e05")
    lbl_recipe_title.pack(pady=10)
    status_label_recipe = tk.StringVar(value="")
    ttk.Label(right_panel, textvariable=status_label_recipe, font=("Arial", 10, "italic"), 
              background="#f9fafb", foreground="blue").pack(anchor="w", padx=10)
    tree_recipe = ttk.Treeview(right_panel, columns=("MaNL", "TenNL", "SoLuong", "DonVi"), show="headings", height=15)
    tree_recipe.heading("MaNL", text="Mã NL"); tree_recipe.heading("TenNL", text="Tên Nguyên Liệu"); tree_recipe.heading("SoLuong", text="Số lượng"); tree_recipe.heading("DonVi", text="Đơn vị")
    tree_recipe.column("MaNL", width=80, anchor="center"); tree_recipe.column("TenNL", width=200, anchor="w"); tree_recipe.column("SoLuong", width=80, anchor="e"); tree_recipe.column("DonVi", width=80, anchor="center")
    tree_recipe.pack(fill="both", expand=True, padx=10, pady=(5, 10))

    # --- Khung Thêm/Xóa Nguyên liệu (Cải tiến 2) ---
    controls_frame = tk.Frame(right_panel, bg="#f9fafb")
    controls_frame.pack(fill="x", padx=10, pady=5)
    
    load_ingredient_cache()
    
    ttk.Label(controls_frame, text="Tìm/Chọn Nguyên liệu:", background="#f9fafb").grid(row=0, column=0, columnspan=2, padx=5, sticky="w")
    entry_search_nl_var = tk.StringVar()
    entry_search_nl = ttk.Entry(controls_frame, textvariable=entry_search_nl_var, width=40, font=("Arial", 10))
    entry_search_nl.grid(row=1, column=0, padx=5, pady=5, sticky="we")

    cb_ingredients_var = tk.StringVar()
    cb_ingredients = ttk.Combobox(controls_frame, textvariable=cb_ingredients_var, 
                                  values=_master_ingredient_keys, state="readonly", width=40)
    cb_ingredients.grid(row=2, column=0, padx=5, pady=5, sticky="we")
    
    ttk.Label(controls_frame, text="Số lượng:", background="#f9fafb").grid(row=1, column=1, padx=5, sticky="w")
    entry_qty_var = tk.StringVar()
    entry_qty = ttk.Entry(controls_frame, textvariable=entry_qty_var, width=10)
    entry_qty.grid(row=2, column=1, padx=5, pady=5, sticky="w")
    
    btn_add_to_recipe = ttk.Button(controls_frame, text="➕ Thêm/Cập nhật", style="Add.TButton",
                                   command=lambda: add_ingredient_to_recipe())
    btn_add_to_recipe.grid(row=2, column=2, padx=5, pady=5)
    
    btn_remove_from_recipe = ttk.Button(controls_frame, text="🗑 Xóa", style="Delete.TButton",
                                        command=lambda: remove_ingredient_from_recipe())
    btn_remove_from_recipe.grid(row=2, column=3, padx=5, pady=5)
    
    controls_frame.grid_columnconfigure(0, weight=1)

    def _filter_ingredient_combobox(*args):
        keyword = entry_search_nl_var.get().lower()
        if not keyword:
            cb_ingredients['values'] = _master_ingredient_keys
        else:
            filtered_list = [key for key in _master_ingredient_keys if keyword in key.lower()]
            cb_ingredients['values'] = filtered_list
            if filtered_list:
                cb_ingredients_var.set(filtered_list[0]) 
            else:
                cb_ingredients_var.set("")
                
    entry_search_nl_var.trace_add("write", _filter_ingredient_combobox)

    # --- LOGIC & HÀM XỬ LÝ (Giữ nguyên) ---
    def load_all_products():
        status_label_products.set("Đang tải sản phẩm...")
        tree_products.update_idletasks()
        query = "SELECT MaSP, TenSP, DonGia FROM SanPham ORDER BY MaSP"
        try:
            rows = db.fetch_query(query)
            tree_data = []
            for r in rows:
                values_tuple = (r['MaSP'], r['TenSP'], f"{int(r['DonGia']):,}")
                tree_data.append({"iid": r['MaSP'], "values": values_tuple})
            fill_treeview_chunked(
                tree_products, 
                tree_data, 
                on_complete=lambda: status_label_products.set(f"Đã tải {len(rows)} sản phẩm.")
            )
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách sản phẩm: {e}")
            status_label_products.set("Lỗi tải sản phẩm!")
            
    def load_recipe_for_product(masp, tensp):
        lbl_recipe_title.config(text=f"2. Công thức cho: {tensp} ({masp})")
        status_label_recipe.set("Đang tải công thức...")
        tree_recipe.update_idletasks()
        query = """
            SELECT ct.MaNL, nl.TenNL, ct.SoLuong, nl.DonVi
            FROM CongThuc ct
            JOIN NguyenLieu nl ON ct.MaNL = nl.MaNL
            WHERE ct.MaSP = ?
            ORDER BY nl.TenNL
        """
        try:
            rows = db.fetch_query(query, (masp,))
            tree_data = []
            for r in rows:
                soluong_f = f"{Decimal(r['SoLuong']):.3f}".rstrip('0').rstrip('.')
                values_tuple = (r['MaNL'], r['TenNL'], soluong_f, r['DonVi'])
                tree_data.append({"iid": r['MaNL'], "values": values_tuple})
            fill_treeview_chunked(
                tree_recipe, 
                tree_data, 
                on_complete=lambda: status_label_recipe.set(f"Công thức có {len(rows)} nguyên liệu.")
            )
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải công thức: {e}")
            status_label_recipe.set("Lỗi tải công thức!")
            
    def on_product_select(event=None):
        selected = tree_products.selection()
        if not selected:
            return
        masp = selected[0]
        tensp = tree_products.item(masp, "values")[1]
        load_recipe_for_product(masp, tensp)
    tree_products.bind("<<TreeviewSelect>>", on_product_select)

    def add_ingredient_to_recipe():
        selected_product = tree_products.selection()
        if not selected_product:
            # SỬA 8: Thay parent=root thành parent=parent_frame
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một SẢN PHẨM ở cây bên trái trước.", parent=parent_frame)
            return
        masp = selected_product[0]
        nl_key = cb_ingredients_var.get()
        if not nl_key:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một NGUYÊN LIỆU để thêm.", parent=parent_frame)
            return
        manl = _ingredient_map.get(nl_key)
        try:
            qty = Decimal(entry_qty_var.get())
            if qty <= 0: raise ValueError
        except (InvalidOperation, ValueError):
            messagebox.showwarning("Lỗi", "Số lượng phải là một số > 0.", parent=parent_frame)
            return
        try:
            exists = db.execute_scalar("SELECT COUNT(*) FROM CongThuc WHERE MaSP = ? AND MaNL = ?", (masp, manl))
            if exists > 0:
                query = "UPDATE CongThuc SET SoLuong = ? WHERE MaSP = ? AND MaNL = ?"
                params = (qty, masp, manl)
                action = "cập nhật"
            else:
                query = "INSERT INTO CongThuc (MaSP, MaNL, SoLuong) VALUES (?, ?, ?)"
                params = (masp, manl, qty)
                action = "thêm"
            if db.execute_query(query, params):
                messagebox.showinfo("Thành công", f"Đã {action} nguyên liệu vào công thức.", parent=parent_frame)
                tensp = tree_products.item(masp, "values")[1]
                load_recipe_for_product(masp, tensp)
                entry_qty_var.set("")
                cb_ingredients_var.set("")
                entry_search_nl_var.set("")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể {action} nguyên liệu: {e}", parent=parent_frame)

    def remove_ingredient_from_recipe():
        selected_product = tree_products.selection()
        selected_ingredient = tree_recipe.selection()
        if not selected_product:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một SẢN PHẨM ở cây bên trái.", parent=parent_frame)
            return
        if not selected_ingredient:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một NGUYÊN LIỆU ở cây bên phải để xóa.", parent=parent_frame)
            return
        masp = selected_product[0]
        manl = selected_ingredient[0]
        tennl = tree_recipe.item(manl, "values")[1]
        
        # SỬA 8: Thêm parent=parent_frame
        if messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc muốn xóa '{tennl}' khỏi công thức này?", parent=parent_frame):
            query = "DELETE FROM CongThuc WHERE MaSP = ? AND MaNL = ?"
            if db.execute_query(query, (masp, manl)):
                messagebox.showinfo("Thành công", "Đã xóa nguyên liệu khỏi công thức.", parent=parent_frame)
                tensp = tree_products.item(masp, "values")[1]
                load_recipe_for_product(masp, tensp)

    # Tải danh sách sản phẩm (cây bên trái) khi mở
    load_all_products()
    
    # SỬA 9: Trả về frame chính
    return module_frame