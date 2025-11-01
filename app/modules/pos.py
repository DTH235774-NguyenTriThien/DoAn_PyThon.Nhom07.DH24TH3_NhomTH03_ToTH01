# app/modules/pos.py
import tkinter as tk
from tkinter import ttk, messagebox
from app import db
# SỬA 1: Import thêm các helper cần thiết
from app.db import fetch_query, execute_query, execute_scalar
from app.theme import setup_styles
from decimal import Decimal, InvalidOperation
from datetime import datetime
import configparser
from app.utils.business_helpers import recalc_invoice_total, deduct_inventory_from_recipe

# Import các helper nghiệp vụ và ID
from app.utils.id_helpers import generate_next_mahd
from app.utils.business_helpers import recalc_invoice_total # Sẽ import hàm trừ kho sau
# Import hàm cộng điểm từ module invoices
from app.modules.invoices import update_customer_points 

# --- HÀM CHÍNH (GIAI ĐOẠN 3: LOGIC BACKEND) ---
def create_pos_module(parent_frame, employee_id, on_back_callback):
    """Giao diện chính cho Module Bán hàng (POS)"""
    
    setup_styles()

    # SỬA 2: Biến toàn cục (trong phạm vi hàm) để lưu thông tin
    # Biến lưu thông tin khách hàng hiện tại (MaKH, TenKH, DiemTichLuy)
    current_customer_info = {}
    # Biến lưu giá trị (VND) của 1 điểm
    vnd_per_point_ratio = 100 # Mặc định: 1 điểm = 100đ

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
    # CỘT 2: GIỎ HÀNG (HÓA ĐƠN TẠM)
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
    # HÀM CẬP NHẬT TỔNG TIỀN (NÂNG CẤP)
    # =========================================================
    def update_totals():
        """Tính toán và cập nhật 3 nhãn tổng tiền (bao gồm cả giảm giá)."""
        nonlocal current_customer_info, vnd_per_point_ratio
        
        total = Decimal(0.0)
        for item_id in tree_cart.get_children():
            values = tree_cart.item(item_id, "values")
            try:
                thanh_tien_str = str(values[4]).replace(",", "").split(" ")[0]
                total += Decimal(thanh_tien_str)
            except (IndexError, InvalidOperation, TypeError):
                pass 
        
        discount = Decimal(0.0)
        
        # SỬA 3: Logic tính giảm giá
        if use_points_var.get() and current_customer_info:
            # Lấy số điểm khách có
            diem_hien_tai = int(current_customer_info.get("DiemTichLuy", 0))
            
            # Tính giá trị điểm (VND)
            gia_tri_diem = Decimal(diem_hien_tai * vnd_per_point_ratio)
            
            # Giảm giá không thể vượt quá tổng tiền
            if gia_tri_diem > total:
                discount = total
            else:
                discount = gia_tri_diem
        
        final_total = total - discount

        total_var.set(f"{int(total):,} đ")
        discount_var.set(f"{int(discount):,} đ")
        final_total_var.set(f"{int(final_total):,} đ")

    # =========================================================
    # CÁC HÀM XỬ LÝ GIỎ HÀNG (Giữ nguyên từ GĐ 2)
    # =========================================================
    def add_item_to_cart(product_info):
        masp = product_info['MaSP']
        tensp = product_info['TenSP']
        dongia = Decimal(product_info['DonGia'])
        
        item = tree_cart.exists(masp)
        
        if item:
            tree_cart.selection_set(masp) 
            tree_cart.focus(masp)         
            increment_quantity()          
        else:
            sl = 1
            thanh_tien = sl * dongia
            values = (masp, tensp, sl, f"{int(dongia):,}", f"{int(thanh_tien):,}")
            tree_cart.insert("", "end", iid=masp, values=values)
        
        update_totals() 

    def increment_quantity():
        selected_iid = tree_cart.focus()
        if not selected_iid:
            return
        values = tree_cart.item(selected_iid, "values")
        masp, tensp, sl, dongia_str, _ = values
        sl = int(sl)
        dongia = Decimal(dongia_str.replace(",", ""))
        sl_moi = sl + 1
        thanh_tien_moi = sl_moi * dongia
        new_values = (masp, tensp, sl_moi, f"{int(dongia):,}", f"{int(thanh_tien_moi):,}")
        tree_cart.item(selected_iid, values=new_values)
        update_totals()

    def decrement_quantity():
        selected_iid = tree_cart.focus()
        if not selected_iid:
            return
        values = tree_cart.item(selected_iid, "values")
        masp, tensp, sl, dongia_str, _ = values
        sl = int(sl)
        dongia = Decimal(dongia_str.replace(",", ""))
        sl_moi = sl - 1
        
        if sl_moi <= 0:
            remove_item_from_cart()
        else:
            thanh_tien_moi = sl_moi * dongia
            new_values = (masp, tensp, sl_moi, f"{int(dongia):,}", f"{int(thanh_tien_moi):,}")
            tree_cart.item(selected_iid, values=new_values)
            update_totals()

    def remove_item_from_cart():
        selected_iid = tree_cart.focus()
        if not selected_iid:
            return
        tree_cart.delete(selected_iid)
        update_totals()

    def clear_cart():
        """Xóa tất cả các món khỏi giỏ hàng và reset."""
        nonlocal current_customer_info
        
        if not tree_cart.get_children():
             return

        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn hủy hóa đơn này?"):
            tree_cart.delete(*tree_cart.get_children())
            
            # Reset khách hàng
            current_customer_info = {}
            lbl_cust_info.config(text="Khách: [Vãng lai]")
            entry_cust_search.delete(0, tk.END)
            use_points_var.set(False)
            chk_use_points.config(state="disabled")
            
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
                prod_info = prod 
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
    
    lbl_cust_info = ttk.Label(cust_group, text="Khách: [Vãng lai]", font=("Arial", 10, "italic"))
    lbl_cust_info.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=5)
    
    # SỬA 5: Thêm Checkbox "Sử dụng điểm"
    use_points_var = tk.BooleanVar(value=False)
    chk_use_points = ttk.Checkbutton(cust_group, text="Sử dụng điểm", 
                                     variable=use_points_var, state="disabled",
                                     command=update_totals) # Gọi update_totals khi check
    chk_use_points.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)

    # --- Khung Điều chỉnh Giỏ hàng ---
    cart_adj_group = ttk.LabelFrame(controls_frame, text=" 4. Điều chỉnh Giỏ hàng ")
    cart_adj_group.grid(row=1, column=0, sticky="new", pady=5)
    cart_adj_group.grid_columnconfigure(0, weight=1)
    cart_adj_group.grid_columnconfigure(1, weight=1)
    cart_adj_group.grid_columnconfigure(2, weight=1)
    
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

    ttk.Button(payment_group, text="💰 Tạm tính", style="Close.TButton",
               command=update_totals).grid(row=1, column=1, sticky="ew", padx=5, pady=5, ipady=8)
    
    ttk.Button(payment_group, text="❌ Hủy Bỏ", style="Delete.TButton",
               command=clear_cart).grid(row=1, column=0, sticky="ew", padx=5, pady=5, ipady=8)

    # =========================================================
    # SỬA 6: VIẾT HÀM TÌM KHÁCH HÀNG VÀ THANH TOÁN
    # =========================================================
    
    def find_customer():
        """Tìm khách hàng bằng SĐT hoặc MaKH"""
        nonlocal current_customer_info # Chỉ định sử dụng biến bên ngoài
        
        keyword = entry_cust_search.get().strip()
        if not keyword:
            # Nếu xóa trống, reset về vãng lai
            current_customer_info = {}
            lbl_cust_info.config(text="Khách: [Vãng lai]")
            chk_use_points.config(state="disabled")
            use_points_var.set(False)
            update_totals()
            return

        query = "SELECT MaKH, TenKH, DiemTichLuy FROM KhachHang WHERE MaKH = ? OR SDT = ?"
        result = fetch_query(query, (keyword, keyword))
        
        if result:
            current_customer_info = result[0] # Lưu lại thông tin
            diem = current_customer_info.get("DiemTichLuy", 0)
            ten = current_customer_info.get("TenKH", "N/A")
            
            lbl_cust_info.config(text=f"Khách: {ten} ({diem} điểm)")
            
            # Cho phép sử dụng điểm nếu có
            if diem > 0:
                chk_use_points.config(state="normal")
            else:
                chk_use_points.config(state="disabled")
                use_points_var.set(False)
        else:
            current_customer_info = {}
            lbl_cust_info.config(text="[Không tìm thấy khách hàng]")
            chk_use_points.config(state="disabled")
            use_points_var.set(False)
        
        update_totals() # Tính lại tổng tiền (nếu lỡ check "dùng điểm")

    # Gán lệnh cho nút "Tìm SĐT/Mã"
    ttk.Button(cust_group, text="Tìm SĐT/Mã", 
               command=find_customer).grid(row=0, column=1, padx=5, pady=5)
    
    
    def process_payment():
        """Hàm xử lý thanh toán cuối cùng (Giai đoạn 3)"""
        nonlocal current_customer_info
        
        # 1. Kiểm tra giỏ hàng
        if not tree_cart.get_children():
            messagebox.showwarning("Giỏ hàng trống", "Vui lòng thêm sản phẩm vào hóa đơn.", parent=module_frame)
            return

        # 2. Lấy thông tin thanh toán từ các biến
        mahd = generate_next_mahd(db.cursor)
        # SỬA LỖI: Dùng 'login_username' (vd: 'nv004')
        manv = employee_id
        makh = current_customer_info.get("MaKH") # Sẽ là None nếu là khách vãng lai
        
        # Lấy tổng tiền (đã loại bỏ ký tự)
        tong_truoc_giam_gia_str = total_var.get().replace(",", "").split(" ")[0]
        giam_gia_str = discount_var.get().replace(",", "").split(" ")[0]
        tong_sau_giam_gia_str = final_total_var.get().replace(",", "").split(" ")[0]
        
        tong_truoc_giam_gia = Decimal(tong_truoc_giam_gia_str)
        giam_gia = Decimal(giam_gia_str)
        tong_sau_giam_gia = Decimal(tong_sau_giam_gia_str)
        
        diem_su_dung = 0
        if use_points_var.get() and makh:
             # Tính số điểm đã dùng (ngược lại với VND)
             diem_su_dung = int(giam_gia / vnd_per_point_ratio)

        # 3. Xác nhận thanh toán
        confirm_msg = f"Tổng tiền: {int(tong_sau_giam_gia):,} đ\n\nXác nhận thanh toán?"
        if not messagebox.askyesno("Xác nhận Thanh toán", confirm_msg, parent=module_frame):
            return

        try:
            # BẮT ĐẦU TRANSACTION (Tưởng tượng)
            if not manv:
                messagebox.showerror("Lỗi Tài khoản", "Không tìm thấy Mã Nhân viên liên kết với tài khoản này.\nKhông thể tạo hóa đơn.", parent=module_frame)
                return

            # 4. GHI VÀO HOADON
            query_hd = """
                INSERT INTO HoaDon (MaHD, NgayLap, MaNV, MaKH, TongTien, GiamGia, ThanhTien, TrangThai, DiemSuDung)
                VALUES (?, ?, ?, ?, ?, ?, ?, N'Đã thanh toán', ?)
            """
            params_hd = (mahd, datetime.now(), manv, makh, 
                         tong_truoc_giam_gia, giam_gia, tong_sau_giam_gia, 
                         diem_su_dung)
            
            if not execute_query(query_hd, params_hd):
                raise Exception("Không thể tạo Hóa đơn.")

            # 5. GHI VÀO CHITIETHOADON
            for item_id in tree_cart.get_children():
                values = tree_cart.item(item_id, "values")
                masp = values[0]
                sl = int(values[2])
                dongia = Decimal(str(values[3]).replace(",", ""))
                
                query_cthd = """
                    INSERT INTO ChiTietHoaDon (MaHD, MaSP, SoLuong, DonGia)
                    VALUES (?, ?, ?, ?)
                """
                if not execute_query(query_cthd, (mahd, masp, sl, dongia)):
                    # (Lưu ý: Trong thực tế, bạn sẽ rollback giao dịch ở đây)
                    raise Exception(f"Không thể lưu chi tiết món {masp}.")
            
            # (Hàm recalc_invoice_total không thực sự cần thiết ở đây nữa
            #  vì chúng ta đã tự tính toán, nhưng gọi nó để đảm bảo trigger (nếu có))
            recalc_invoice_total(db.cursor, db.conn, mahd)

            # 6. TRỪ KHO (Sẽ làm ở bước tiếp theo)
            deduct_inventory_from_recipe(mahd)
            
            # 7. CẬP NHẬT ĐIỂM KHÁCH HÀNG
            if makh:
                # Trừ điểm đã dùng
                if diem_su_dung > 0:
                    execute_query("UPDATE KhachHang SET DiemTichLuy = DiemTichLuy - ? WHERE MaKH = ?", 
                                  (diem_su_dung, makh))
                
                # Cộng điểm cho hóa đơn này (dựa trên TỔNG TIỀN TRƯỚC GIẢM GIÁ)
                update_customer_points(makh, tong_truoc_giam_gia)

            # 8. Hoàn tất
            messagebox.showinfo("Thành công", f"Đã thanh toán thành công hóa đơn {mahd}.", parent=module_frame)
            clear_cart() # Xóa giỏ hàng để chuẩn bị cho lần tiếp theo

        except Exception as e:
            messagebox.showerror("Lỗi Thanh toán", f"Không thể hoàn tất hóa đơn:\n{e}", parent=module_frame)
            # (Trong thực tế, bạn sẽ rollback toàn bộ giao dịch)


    # Gán lệnh cho nút "THANH TOÁN"
    ttk.Button(payment_group, text="✅ THANH TOÁN", style="Add.TButton",
               command=process_payment).grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5, ipady=15)
    
    # --- Trả về frame chính ---
    return module_frame