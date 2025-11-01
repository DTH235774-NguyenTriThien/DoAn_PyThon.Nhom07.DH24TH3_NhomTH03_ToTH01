# app/modules/pos.py
import tkinter as tk
from tkinter import ttk, messagebox
from app import db
from app.db import fetch_query
from app.theme import setup_styles
from decimal import Decimal, InvalidOperation

# --- HÀM CHÍNH (GIAI ĐOẠN 2: LOGIC GIỎ HÀNG) ---
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
    
    main_content_frame.grid_rowconfigure(0, weight=1)
    main_content_frame.grid_columnconfigure(0, weight=2, uniform="group1") 
    main_content_frame.grid_columnconfigure(1, weight=3, uniform="group1") 
    main_content_frame.grid_columnconfigure(2, weight=2, uniform="group1") 

    # =========================================================
    # CỘT 2: GIỎ HÀNG (ĐỊNH NGHĨA TRƯỚC VÌ CỘT 1 VÀ 3 SẼ GỌI NÓ)
    # =========================================================
    cart_frame = ttk.LabelFrame(main_content_frame, text=" 2. Giỏ Hàng ")
    cart_frame.grid(row=0, column=1, sticky="nsew", padx=5)
    cart_frame.grid_rowconfigure(0, weight=1)
    cart_frame.grid_columnconfigure(0, weight=1)

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
    total_frame.grid_columnconfigure(1, weight=1) 

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
    # SỬA 4: VIẾT HÀM CẬP NHẬT TỔNG TIỀN
    # =========================================================
    def update_totals():
        """Tính toán và cập nhật 3 nhãn tổng tiền dựa trên tree_cart."""
        total = Decimal(0.0)
        
        for item_id in tree_cart.get_children():
            values = tree_cart.item(item_id, "values")
            # Cột 4 là "ThanhTien"
            try:
                # Loại bỏ dấu phẩy (,) và chữ 'đ' nếu có
                thanh_tien_str = str(values[4]).replace(",", "").split(" ")[0]
                total += Decimal(thanh_tien_str)
            except (IndexError, InvalidOperation, TypeError):
                pass # Bỏ qua nếu dòng không hợp lệ
        
        # (Giai đoạn 2: Giảm giá luôn bằng 0)
        discount = Decimal(0.0) 
        final_total = total - discount

        # Cập nhật các biến StringVar (Label)
        total_var.set(f"{int(total):,} đ")
        discount_var.set(f"{int(discount):,} đ")
        final_total_var.set(f"{int(final_total):,} đ")


    # =========================================================
    # SỬA 2: VIẾT CÁC HÀM XỬ LÝ GIỎ HÀNG
    # =========================================================
    def add_item_to_cart(product_info):
        """Thêm 1 sản phẩm vào giỏ hàng hoặc tăng số lượng nếu đã tồn tại."""
        masp = product_info['MaSP']
        tensp = product_info['TenSP']
        dongia = Decimal(product_info['DonGia'])
        
        # Kiểm tra xem MaSP đã có trong giỏ hàng (Treeview) chưa
        item = tree_cart.exists(masp)
        
        if item:
            # Nếu có, tăng số lượng
            tree_cart.selection_set(masp) # Chọn dòng đó
            tree_cart.focus(masp) # Đặt focus vào trước khi gọi hàm tăng số lượng
            increment_quantity() # Gọi hàm tăng SL
        else:
            # Nếu chưa, thêm dòng mới
            sl = 1
            thanh_tien = sl * dongia
            values = (
                masp, 
                tensp, 
                sl, 
                f"{int(dongia):,}", 
                f"{int(thanh_tien):,}"
            )
            # Dùng MaSP làm ID (iid) của dòng
            tree_cart.insert("", "end", iid=masp, values=values)
        
        update_totals() # Cập nhật tổng tiền

    def increment_quantity():
        """Tăng số lượng của món đang chọn lên 1."""
        selected_iid = tree_cart.focus()
        if not selected_iid:
            return

        values = tree_cart.item(selected_iid, "values")
        masp, tensp = values[0], values[1]
        sl = int(values[2])
        dongia_str = str(values[3]).replace(",", "")
        dongia = Decimal(dongia_str)

        sl_moi = sl + 1
        thanh_tien_moi = sl_moi * dongia
        
        new_values = (
            masp, 
            tensp, 
            sl_moi, 
            f"{int(dongia):,}", 
            f"{int(thanh_tien_moi):,}"
        )
        tree_cart.item(selected_iid, values=new_values)
        update_totals()

    def decrement_quantity():
        """Giảm số lượng của món đang chọn đi 1. Nếu về 0 thì xóa."""
        selected_iid = tree_cart.focus()
        if not selected_iid:
            return

        values = tree_cart.item(selected_iid, "values")
        masp, tensp = values[0], values[1]
        sl = int(values[2])
        dongia_str = str(values[3]).replace(",", "")
        dongia = Decimal(dongia_str)

        sl_moi = sl - 1
        
        if sl_moi <= 0:
            # Nếu về 0, xóa luôn
            remove_item_from_cart()
        else:
            thanh_tien_moi = sl_moi * dongia
            new_values = (
                masp, 
                tensp, 
                sl_moi, 
                f"{int(dongia):,}", 
                f"{int(thanh_tien_moi):,}"
            )
            tree_cart.item(selected_iid, values=new_values)
            update_totals()

    def remove_item_from_cart():
        """Xóa món đang chọn khỏi giỏ hàng."""
        selected_iid = tree_cart.focus()
        if not selected_iid:
            return
        
        tree_cart.delete(selected_iid)
        update_totals()

    def clear_cart():
        """Xóa tất cả các món khỏi giỏ hàng và reset."""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn hủy hóa đơn này?"):
            tree_cart.delete(*tree_cart.get_children())
            
            # (Giai đoạn 2: Tạm thời reset luôn khách hàng)
            lbl_cust_info.config(text="Khách: [Vãng lai]")
            entry_cust_search.delete(0, tk.END)
            
            update_totals()

    # =========================================================
    # CỘT 1: DANH SÁCH SẢN PHẨM (MENU)
    # =========================================================
    product_frame = ttk.LabelFrame(main_content_frame, text=" 1. Chọn Món ")
    product_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
    product_frame.grid_rowconfigure(0, weight=1)
    product_frame.grid_columnconfigure(0, weight=1)

    canvas_frame = tk.Frame(product_frame, bg="white")
    canvas_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    canvas_frame.grid_rowconfigure(0, weight=1)
    canvas_frame.grid_columnconfigure(0, weight=1)

    scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical")
    scrollbar.grid(row=0, column=1, sticky="ns")

    canvas = tk.Canvas(canvas_frame, yscrollcommand=scrollbar.set, bg="white", highlightthickness=0)
    canvas.grid(row=0, column=0, sticky="nsew")

    scrollbar.config(command=canvas.yview)

    scrollable_frame = tk.Frame(canvas, bg="white")
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    def configure_scrollregion(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    scrollable_frame.bind("<Configure>", configure_scrollregion)

    def load_product_buttons(parent):
        """Tải các nút sản phẩm từ CSDL và hiển thị"""
        try:
            products = fetch_query("SELECT MaSP, TenSP, DonGia FROM SanPham WHERE TrangThai = N'Còn bán' ORDER BY TenSP")
            
            row, col = 0, 0
            for prod in products:
                gia = f"{int(prod['DonGia']):,}"
                btn_text = f"{prod['TenSP']}\n({gia} đ)"
                
                # SỬA 1: GÁN LỆNH (COMMAND) CHO NÚT
                # Dùng lambda để truyền thông tin sản phẩm vào hàm
                prod_info = prod # Tạo bản sao
                btn = ttk.Button(parent, text=btn_text, style="Product.TButton", 
                                 command=lambda p=prod_info: add_item_to_cart(p)) 
                
                btn.grid(row=row, column=col, sticky="nsew", padx=4, pady=4, ipady=15)
                
                col += 1
                if col > 1:
                    col = 0
                    row += 1
            
            parent.grid_columnconfigure(0, weight=1)
            parent.grid_columnconfigure(1, weight=1)

        except Exception as e:
            ttk.Label(parent, text=f"Lỗi tải sản phẩm: {e}").pack()

    load_product_buttons(scrollable_frame)

    # =========================================================
    # CỘT 3: ĐIỀU KHIỂN & THANH TOÁN
    # =========================================================
    controls_frame = tk.Frame(main_content_frame, bg="#f5e6ca")
    controls_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
    controls_frame.grid_columnconfigure(0, weight=1) 

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
    
    # SỬA 3: GÁN LỆNH CHO CÁC NÚT ĐIỀU KHIỂN
    ttk.Button(cart_adj_group, text="Tăng SL (+)", style="Edit.TButton", 
               command=increment_quantity).grid(row=0, column=0, sticky="ew", padx=5, pady=5)
    ttk.Button(cart_adj_group, text="Giảm SL (-)", style="Edit.TButton",
               command=decrement_quantity).grid(row=0, column=1, sticky="ew", padx=5, pady=5)
    ttk.Button(cart_adj_group, text="Xóa Món", style="Delete.TButton",
               command=remove_item_from_cart).grid(row=0, column=2, sticky="ew", padx=5, pady=5)

    # --- Khung Thanh toán ---
    payment_group = ttk.LabelFrame(controls_frame, text=" 5. Hoàn tất ")
    payment_group.grid(row=2, column=0, sticky="new", pady=10)
    payment_group.grid_columnconfigure(0, weight=1)
    payment_group.grid_columnconfigure(1, weight=1)

    ttk.Button(payment_group, text="✅ THANH TOÁN", style="Add.TButton",
               command=None).grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5, ipady=15)
    
    ttk.Button(payment_group, text="❌ Hủy Bỏ", style="Delete.TButton",
               command=clear_cart).grid(row=1, column=0, sticky="ew", padx=5, pady=5, ipady=8)
    
    # Nút Tạm tính cũng gọi update_totals để đảm bảo
    ttk.Button(payment_group, text="💰 Tạm tính", style="Close.TButton",
               command=update_totals).grid(row=1, column=1, sticky="ew", padx=5, pady=5, ipady=8)
    
    # --- Trả về frame chính ---
    return module_frame