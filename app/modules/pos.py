# app/modules/pos.py
import tkinter as tk
from tkinter import ttk, messagebox
from app import db
from app.db import fetch_query
from app.theme import setup_styles
from decimal import Decimal

# --- HÀM CHÍNH (GIAI ĐOẠN 1: DỰNG GIAO DIỆN) ---
def create_pos_module(parent_frame, username, on_back_callback):
    """Giao diện chính cho Module Bán hàng (POS)"""
    
    setup_styles()

    # --- Frame chính của module ---
    module_frame = tk.Frame(parent_frame, bg="#f5e6ca")
    
    # --- Header ---
    header = tk.Frame(module_frame, bg="#4b2e05", height=70)
    header.pack(fill="x")
    
    tk.Label(header, text="🛒 BÁN HÀNG TẠI QUẦY (POS)", bg="#4b2e05", fg="white",
             font=("Segoe UI", 16, "bold")).pack(side="left", padx=15, pady=12)
    
    ttk.Button(header, text="⬅ Quay lại", style="Close.TButton",
             command=on_back_callback).pack(side="right", padx=15)

    # --- Khung Giao diện 3 Cột (dùng GRID) ---
    main_content_frame = tk.Frame(module_frame, bg="#f5e6ca")
    main_content_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Cấu hình grid co giãn
    main_content_frame.grid_rowconfigure(0, weight=1)
    main_content_frame.grid_columnconfigure(0, weight=2, uniform="group1") # Cột 1: Menu
    main_content_frame.grid_columnconfigure(1, weight=3, uniform="group1") # Cột 2: Giỏ hàng
    main_content_frame.grid_columnconfigure(2, weight=2, uniform="group1") # Cột 3: Điều khiển

    # =========================================================
    # CỘT 1: DANH SÁCH SẢN PHẨM (MENU)
    # =========================================================
    product_frame = ttk.LabelFrame(main_content_frame, text=" 1. Chọn Món ")
    product_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
    product_frame.grid_rowconfigure(0, weight=1) # Cho phép canvas co giãn
    product_frame.grid_columnconfigure(0, weight=1)

    # --- Tạo Canvas và Scrollbar cho menu ---
    canvas_frame = tk.Frame(product_frame, bg="white")
    canvas_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    canvas_frame.grid_rowconfigure(0, weight=1)
    canvas_frame.grid_columnconfigure(0, weight=1)

    scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical")
    scrollbar.grid(row=0, column=1, sticky="ns")

    canvas = tk.Canvas(canvas_frame, yscrollcommand=scrollbar.set, bg="white", highlightthickness=0)
    canvas.grid(row=0, column=0, sticky="nsew")

    scrollbar.config(command=canvas.yview)

    # --- Frame chứa các nút sản phẩm (bên trong canvas) ---
    scrollable_frame = tk.Frame(canvas, bg="white")
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    def configure_scrollregion(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    scrollable_frame.bind("<Configure>", configure_scrollregion)

    def load_product_buttons(parent):
        """Tải các nút sản phẩm từ CSDL và hiển thị"""
        try:
            products = fetch_query("SELECT MaSP, TenSP, DonGia FROM SanPham WHERE TrangThai = N'Còn bán' ORDER BY TenSP")
            
            # Hiển thị 2 cột
            row, col = 0, 0
            for prod in products:
                gia = f"{int(prod['DonGia']):,}"
                btn_text = f"{prod['TenSP']}\n({gia} đ)"
                
                # GIAI ĐOẠN 1: Nút chưa cần command
                btn = ttk.Button(parent, text=btn_text, style="Product.TButton", 
                                 command=None) 
                btn.grid(row=row, column=col, sticky="nsew", padx=4, pady=4, ipady=15)
                
                col += 1
                if col > 1:
                    col = 0
                    row += 1
            
            parent.grid_columnconfigure(0, weight=1)
            parent.grid_columnconfigure(1, weight=1)

        except Exception as e:
            ttk.Label(parent, text=f"Lỗi tải sản phẩm: {e}").pack()

    # (Tải các nút sản phẩm vào frame)
    load_product_buttons(scrollable_frame)

    # =========================================================
    # CỘT 2: GIỎ HÀNG (HÓA ĐƠN TẠM)
    # =========================================================
    cart_frame = ttk.LabelFrame(main_content_frame, text=" 2. Giỏ Hàng ")
    cart_frame.grid(row=0, column=1, sticky="nsew", padx=5)
    cart_frame.grid_rowconfigure(0, weight=1)
    cart_frame.grid_columnconfigure(0, weight=1)

    # --- Treeview Giỏ hàng ---
    cart_cols = ("MaSP", "TenSP", "SL", "DonGia", "ThanhTien")
    tree_cart = ttk.Treeview(cart_frame, columns=cart_cols, show="headings", height=15)
    tree_cart.heading("MaSP", text="Mã SP"); tree_cart.column("MaSP", width=60, anchor="center")
    tree_cart.heading("TenSP", text="Tên Sản Phẩm"); tree_cart.column("TenSP", width=180, anchor="w")
    tree_cart.heading("SL", text="SL"); tree_cart.column("SL", width=40, anchor="center")
    tree_cart.heading("DonGia", text="Đơn Giá"); tree_cart.column("DonGia", width=80, anchor="e")
    tree_cart.heading("ThanhTien", text="Thành Tiền"); tree_cart.column("ThanhTien", width=100, anchor="e")
    tree_cart.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    # --- Khung Tổng tiền ---
    total_frame = tk.Frame(cart_frame, bg="#f5e6ca")
    total_frame.grid(row=1, column=0, sticky="sew", padx=5, pady=5)
    total_frame.grid_columnconfigure(1, weight=1) # Cho phép ô giá trị co giãn

    # (StringVars để cập nhật giá ở Giai đoạn 2)
    total_var = tk.StringVar(value="0 đ")
    discount_var = tk.StringVar(value="0 đ")
    final_total_var = tk.StringVar(value="0 đ")

    ttk.Label(total_frame, text="Tổng cộng:", font=("Segoe UI", 12)).grid(row=0, column=0, sticky="w", padx=5)
    ttk.Label(total_frame, textvariable=total_var, font=("Segoe UI", 12)).grid(row=0, column=1, sticky="e", padx=5)
    
    ttk.Label(total_frame, text="Giảm giá (Điểm):", font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", padx=5)
    ttk.Label(total_frame, textvariable=discount_var, font=("Segoe UI", 12)).grid(row=1, column=1, sticky="e", padx=5)
    
    ttk.Label(total_frame, text="KHÁCH CẦN TRẢ:", font=("Segoe UI", 16, "bold"), foreground="#d32f2f").grid(row=2, column=0, sticky="w", padx=5, pady=5)
    ttk.Label(total_frame, textvariable=final_total_var, font=("Segoe UI", 16, "bold"), foreground="#d32f2f").grid(row=2, column=1, sticky="e", padx=5, pady=5)

    # =========================================================
    # CỘT 3: ĐIỀU KHIỂN & THANH TOÁN
    # =========================================================
    controls_frame = tk.Frame(main_content_frame, bg="#f5e6ca")
    controls_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
    controls_frame.grid_columnconfigure(0, weight=1) # Cho phép các group co giãn

    # --- Khung Khách hàng ---
    cust_group = ttk.LabelFrame(controls_frame, text=" 3. Khách hàng (Tùy chọn) ")
    cust_group.grid(row=0, column=0, sticky="new", pady=(0, 10))
    cust_group.grid_columnconfigure(0, weight=1)
    
    entry_cust_search = ttk.Entry(cust_group, font=("Arial", 11), width=15)
    entry_cust_search.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
    ttk.Button(cust_group, text="Tìm SĐT/Mã").grid(row=0, column=1, padx=5, pady=5)
    
    lbl_cust_info = ttk.Label(cust_group, text="Khách: [Vãng lai]", font=("Arial", 10, "italic"))
    lbl_cust_info.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=5)

    # --- Khung Điều chỉnh Giỏ hàng ---
    cart_adj_group = ttk.LabelFrame(controls_frame, text=" 4. Điều chỉnh Giỏ hàng ")
    cart_adj_group.grid(row=1, column=0, sticky="new", pady=5)
    cart_adj_group.grid_columnconfigure(0, weight=1)
    cart_adj_group.grid_columnconfigure(1, weight=1)
    cart_adj_group.grid_columnconfigure(2, weight=1)
    
    ttk.Button(cart_adj_group, text="Tăng SL (+)", style="Edit.TButton").grid(row=0, column=0, sticky="ew", padx=5, pady=5)
    ttk.Button(cart_adj_group, text="Giảm SL (-)", style="Edit.TButton").grid(row=0, column=1, sticky="ew", padx=5, pady=5)
    ttk.Button(cart_adj_group, text="Xóa Món", style="Delete.TButton").grid(row=0, column=2, sticky="ew", padx=5, pady=5)

    # --- Khung Thanh toán ---
    payment_group = ttk.LabelFrame(controls_frame, text=" 5. Hoàn tất ")
    payment_group.grid(row=2, column=0, sticky="new", pady=10)
    payment_group.grid_columnconfigure(0, weight=1)
    payment_group.grid_columnconfigure(1, weight=1)

    ttk.Button(payment_group, text="✅ THANH TOÁN", style="Add.TButton",
               command=None).grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5, ipady=15)
    
    ttk.Button(payment_group, text="❌ Hủy Bỏ", style="Delete.TButton",
               command=None).grid(row=1, column=0, sticky="ew", padx=5, pady=5, ipady=8)
    
    ttk.Button(payment_group, text="💰 Tạm tính", style="Close.TButton",
               command=None).grid(row=1, column=1, sticky="ew", padx=5, pady=5, ipady=8)
    
    # --- Trả về frame chính ---
    return module_frame