# app/modules/pos.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog 
from app import db
from app.db import fetch_query, execute_query, execute_scalar
from app.theme import setup_styles
from decimal import Decimal, InvalidOperation
from datetime import datetime
from app.utils.report_helpers import print_pos_receipt
import configparser
import os 

# SỬA 1: Import hàm căn giữa (từ bước trước)
from app.utils.utils import center_window_relative

try:
    from PIL import Image, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

from app.utils.id_helpers import generate_next_mahd
from app.utils.business_helpers import recalc_invoice_total, deduct_inventory_from_recipe
from app.modules.invoices import update_customer_points 

def create_pos_module(parent_frame, employee_id, on_back_callback):
    
    setup_styles()
    
    style = ttk.Style()
    style.configure("Product.TButton",
                    font=("Segoe UI", 10),
                    padding=(5, 5),
                    anchor="center",
                    compound="top") 
    
    current_customer_info = {}
    vnd_per_point_ratio = 100 

    # --- Frame chính của module ---
    module_frame = tk.Frame(parent_frame, bg="#f5e6ca")
    
    # --- Header ---
    header = tk.Frame(module_frame, bg="#4b2e05", height=70)
    header.pack(fill="x")
    tk.Label(header, text="🛒 BÁN HÀNG TẠI QUẦY (POS)", bg="#4b2e05", fg="white",
             font=("Segoe UI", 16, "bold")).pack(side="left", padx=15, pady=12)
    
    btn_back = ttk.Button(header, text="⬅ Quay lại", style="Close.TButton")
    btn_back.pack(side="right", padx=15)

    # --- Khung Giao diện 2 Cột (dùng GRID) ---
    main_content_frame = tk.Frame(module_frame, bg="#f5e6ca")
    main_content_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    main_content_frame.grid_rowconfigure(0, weight=1)
    main_content_frame.grid_columnconfigure(0, weight=3) # Cột 1: Menu
    main_content_frame.grid_columnconfigure(1, weight=2) # Cột 2: Giỏ hàng/Thanh toán

    # =========================================================
    # CỘT 2: GIỎ HÀNG & ĐIỀU KHIỂN (Xếp chồng)
    # =========================================================
    
    controls_frame = tk.Frame(main_content_frame, bg="#f5e6ca")
    controls_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
    controls_frame.grid_columnconfigure(0, weight=1) 
    controls_frame.grid_rowconfigure(0, weight=1, minsize=200) # Hàng 0: Giỏ hàng
    controls_frame.grid_rowconfigure(1, weight=0) # Hàng 1: Khách hàng
    controls_frame.grid_rowconfigure(2, weight=0) # Hàng 2: Hành động

    # --- Khung Giỏ hàng (Cột 2, Hàng 0) ---
    cart_frame = ttk.LabelFrame(controls_frame, text=" 2. Giỏ Hàng (Nhấn +, -, Delete hoặc Double-click) ")
    cart_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
    cart_frame.grid_rowconfigure(0, weight=1) 
    cart_frame.grid_rowconfigure(1, weight=0) 
    cart_frame.grid_columnconfigure(0, weight=1)

    cart_cols = ("TenSP", "SL", "DonGia", "GhiChu")
    tree_cart = ttk.Treeview(cart_frame, columns=cart_cols, show="headings", height=10) 
    tree_cart.heading("TenSP", text="Tên Sản Phẩm"); tree_cart.column("TenSP", width=150, anchor="w")
    tree_cart.heading("SL", text="SL"); tree_cart.column("SL", width=30, anchor="center")
    tree_cart.heading("DonGia", text="Đơn Giá"); tree_cart.column("DonGia", width=70, anchor="e")
    tree_cart.heading("GhiChu", text="Ghi chú"); tree_cart.column("GhiChu", width=100, anchor="w")
    tree_cart.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    cart_scroll = ttk.Scrollbar(cart_frame, orient="vertical", command=tree_cart.yview)
    cart_scroll.grid(row=0, column=1, sticky="ns")
    tree_cart.configure(yscrollcommand=cart_scroll.set)
    tree_cart.counter = 0

    # --- Khung Tổng tiền ---
    total_frame = tk.Frame(cart_frame, bg="#f5e6ca")
    total_frame.grid(row=1, column=0, columnspan=2, sticky="sew", padx=5, pady=5) 
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

    # --- Khung Khách hàng (Cột 2, Hàng 1) ---
    cust_group = ttk.LabelFrame(controls_frame, text=" 3. Khách hàng (Tìm theo SĐT/Tên) ")
    cust_group.grid(row=1, column=0, sticky="new", pady=5) 
    cust_group.grid_columnconfigure(0, weight=1)
    cust_search_var = tk.StringVar()
    entry_cust_search = ttk.Entry(cust_group, textvariable=cust_search_var, font=("Arial", 11), width=15)
    entry_cust_search.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5) 
    lbl_cust_info = ttk.Label(cust_group, text="Khách: [Vãng lai]", font=("Arial", 10, "italic"))
    lbl_cust_info.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=5)
    use_points_var = tk.BooleanVar(value=False)
    chk_use_points = ttk.Checkbutton(cust_group, text="Sử dụng điểm", 
                                     variable=use_points_var, state="disabled",
                                     command=lambda: update_totals())
    chk_use_points.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)

    # --- Khung Hành động (Cột 2, Hàng 2) ---
    action_group = ttk.LabelFrame(controls_frame, text=" 4. Hành động ")
    action_group.grid(row=2, column=0, sticky="new", pady=10) 
    action_group.grid_columnconfigure(0, weight=1)
    action_group.grid_columnconfigure(1, weight=1)
    action_group.grid_columnconfigure(2, weight=1)
    btn_payment = ttk.Button(action_group, text="✅ THANH TOÁN (F9)", style="Add.TButton")
    btn_payment.grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=5, ipady=15)
    btn_clear_cart = ttk.Button(action_group, text="❌ Hủy Bỏ (F12)", style="Delete.TButton")
    btn_clear_cart.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5, ipady=8) 
    btn_recalc = ttk.Button(action_group, text="💰 Tạm tính", style="Close.TButton")
    btn_recalc.grid(row=1, column=2, sticky="ew", padx=5, pady=5, ipady=8) 


    # (Toàn bộ các hàm logic bên dưới không thay đổi)
    # =========================================================
    # HÀM CẬP NHẬT TỔNG TIỀN (Giữ nguyên)
    # =========================================================
    def update_totals():
        nonlocal current_customer_info, vnd_per_point_ratio
        total = Decimal(0.0)
        for item_id in tree_cart.get_children():
            values = tree_cart.item(item_id, "values")
            try:
                sl = Decimal(values[1])
                dongia_str = str(values[2]).replace(",", "").split(" ")[0]
                dongia = Decimal(dongia_str)
                total += (sl * dongia) 
            except (IndexError, InvalidOperation, TypeError):
                pass 
        discount = Decimal(0.0)
        if use_points_var.get() and current_customer_info:
            diem_hien_tai = int(current_customer_info.get("DiemTichLuy", 0))
            gia_tri_diem = Decimal(diem_hien_tai * vnd_per_point_ratio)
            discount = min(gia_tri_diem, total)
        final_total = total - discount
        total_var.set(f"{int(total):,} đ")
        discount_var.set(f"{int(discount):,} đ")
        final_total_var.set(f"{int(final_total):,} đ")

    # =========================================================
    # CÁC HÀM XỬ LÝ GIỎ HÀNG (Giữ nguyên)
    # =========================================================
    def add_item_to_cart(product_info, notes):
        tree_cart.counter += 1
        new_iid = f"item_{tree_cart.counter}" 
        masp = product_info['MaSP']
        tensp = product_info['TenSP']
        dongia = Decimal(product_info['DonGia'])
        item_to_increment = None
        if not notes: 
            for iid in tree_cart.get_children():
                tags = tree_cart.item(iid, 'tags')
                if tags and tags[0] == masp and tags[1] == "":
                    item_to_increment = iid
                    break
        if item_to_increment:
            tree_cart.selection_set(item_to_increment) 
            tree_cart.focus(item_to_increment)         
            increment_quantity()          
        else:
            sl = 1
            tensp_display = tensp
            if notes:
                tensp_display = f"{tensp} ({notes})" 
            values = (tensp_display, sl, f"{int(dongia):,}", notes)
            tags = (masp, notes)
            tree_cart.insert("", "end", iid=new_iid, values=values, tags=tags)
        update_totals() 

    def increment_quantity():
        selected_iid = tree_cart.focus()
        if not selected_iid:
            return
        values = tree_cart.item(selected_iid, "values")
        tensp_display, sl, dongia_str, notes = values
        sl = int(sl)
        sl_moi = sl + 1
        new_values = (tensp_display, sl_moi, dongia_str, notes)
        tree_cart.item(selected_iid, values=new_values)
        update_totals()

    def decrement_quantity():
        selected_iid = tree_cart.focus()
        if not selected_iid:
            return
        values = tree_cart.item(selected_iid, "values")
        tensp_display, sl, dongia_str, notes = values
        sl = int(sl)
        sl_moi = sl - 1
        if sl_moi <= 0:
            remove_item_from_cart()
        else:
            new_values = (tensp_display, sl_moi, dongia_str, notes)
            tree_cart.item(selected_iid, values=new_values)
            update_totals()

    def remove_item_from_cart():
        selected_iid = tree_cart.focus()
        if not selected_iid:
            return
        tree_cart.delete(selected_iid)
        update_totals()

    def clear_cart():
        nonlocal current_customer_info
        if not tree_cart.get_children():
             return
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn hủy hóa đơn này?"):
            tree_cart.delete(*tree_cart.get_children())
            current_customer_info = {}
            lbl_cust_info.config(text="Khách: [Vãng lai]")
            cust_search_var.set("") 
            use_points_var.set(False)
            chk_use_points.config(state="disabled")
            update_totals()

    # =========================================================
    # HÀM TÙY CHỌN (MODIFIERS) (SỬA: Đã căn giữa)
    # =========================================================
    def show_options_window(product_info):
        win = tk.Toplevel(module_frame)
        win.title(f"Tùy chọn cho: {product_info['TenSP']}")
        win.configure(bg="#f8f9fa")
        
        # SỬA: Gọi hàm căn giữa
        center_window_relative(win, module_frame, 350, 200)
        
        form = tk.Frame(win, bg="#f8f9fa", padx=15, pady=10)
        form.pack(fill="both", expand=True)
        
        ttk.Label(form, text="Ghi chú (ví dụ: ít đường, nhiều đá):", 
                  font=("Arial", 11)).pack(anchor="w", pady=(5,5))
        
        notes_var = tk.StringVar()
        entry_notes = ttk.Entry(form, textvariable=notes_var, font=("Arial", 11))
        entry_notes.pack(fill="x", pady=5)
        entry_notes.focus_set() 

        quick_notes_frame = tk.Frame(form, bg="#f8f9fa")
        quick_notes_frame.pack(fill="x", pady=5)
        
        def add_quick_note(note_text):
            current_notes = notes_var.get()
            if current_notes:
                notes_var.set(f"{current_notes}, {note_text}")
            else:
                notes_var.set(note_text)
        
        ttk.Button(quick_notes_frame, text="Ít đường", 
                   command=lambda: add_quick_note("Ít đường")).pack(side="left", padx=2)
        ttk.Button(quick_notes_frame, text="Ít đá", 
                   command=lambda: add_quick_note("Ít đá")).pack(side="left", padx=2)
        ttk.Button(quick_notes_frame, text="Nhiều đá", 
                   command=lambda: add_quick_note("Nhiều đá")).pack(side="left", padx=2)
        
        btn_frame = tk.Frame(form, bg="#f8f9fa")
        btn_frame.pack(fill="x", pady=15)

        def on_confirm():
            notes = notes_var.get().strip()
            add_item_to_cart(product_info, notes)
            win.destroy()

        ttk.Button(btn_frame, text="✅ Xác nhận", style="Add.TButton", 
                 command=on_confirm).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Hủy", style="Close.TButton", 
                 command=win.destroy).pack(side="right", padx=5)
        
        win.bind("<Return>", lambda e: on_confirm())
        win.bind("<Escape>", lambda e: win.destroy())


    # =========================================================
    # SỰ KIỆN (DOUBLE-CLICK VÀ KEYPRESS) (Giữ nguyên)
    # =========================================================
    def on_cart_double_click(event):
        selected_iid = tree_cart.focus()
        if not selected_iid:
            return
        values = tree_cart.item(selected_iid, "values")
        tensp_display, sl_hien_tai, dongia_str, notes = values
        sl_hien_tai = int(sl_hien_tai)
        new_qty = simpledialog.askinteger(
            "Sửa Số Lượng", f"Nhập số lượng mới cho:\n{tensp_display}",
            parent=module_frame, initialvalue=sl_hien_tai, minvalue=0 
        )
        if new_qty is None: return
        if new_qty == 0:
            remove_item_from_cart()
        elif new_qty > 0:
            new_values = (tensp_display, new_qty, dongia_str, notes)
            tree_cart.item(selected_iid, values=new_values)
            update_totals()

    def on_cart_keypress(event):
        if event.keysym == 'plus' or event.keysym == 'equal':
            increment_quantity()
        elif event.keysym == 'minus':
            decrement_quantity()
        elif event.keysym == 'Delete' or event.keysym == 'BackSpace':
            remove_item_from_cart()

    tree_cart.bind("<Double-1>", on_cart_double_click)
    tree_cart.bind("<KeyRelease>", on_cart_keypress)

    def on_f9_press(event):
        process_payment()
    def on_f12_press(event):
        clear_cart()

    module_frame.bind_all("<F9>", on_f9_press)
    module_frame.bind_all("<F12>", on_f12_press)
    
    def _cleanup_hotkeys(event=None):
        module_frame.unbind_all("<F9>")
        module_frame.unbind_all("<F12>")
        module_frame.unbind("<Destroy>")
        
    def _on_back_pressed_wrapper():
        _cleanup_hotkeys()
        on_back_callback()
        
    btn_back.config(command=_on_back_pressed_wrapper)
    module_frame.bind("<Destroy>", _cleanup_hotkeys)
    

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
    scrollable_frame.image_references = [] 
    
    def configure_scrollregion(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    scrollable_frame.bind("<Configure>", configure_scrollregion)


    # SỬA 3: THÊM CÁC HÀM HỖ TRỢ LĂN CHUỘT (MOUSEWHEEL)
    def _on_mousewheel(event):
        """Hàm xử lý sự kiện lăn chuột, cuộn canvas."""
        # Logic cho Windows/macOS (dùng event.delta)
        if event.delta:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        # Logic cho Linux (dùng event.num)
        else:
            if event.num == 5:
                canvas.yview_scroll(1, "units")
            elif event.num == 4:
                canvas.yview_scroll(-1, "units")

    def _bind_mousewheel_all(event):
        """Gán sự kiện lăn chuột cho toàn bộ cửa sổ khi chuột đi vào menu"""
        # (Dùng bind_all để bắt sự kiện ngay cả khi trỏ chuột lên nút bấm)
        module_frame.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind_mousewheel_all(event):
        """Hủy gán sự kiện lăn chuột khi chuột rời khỏi menu"""
        module_frame.unbind_all("<MouseWheel>")
    
    # Gán sự kiện <Enter> (vào) và <Leave> (ra) cho toàn bộ Cột 1
    # (bao gồm cả Canvas, Scrollbar, và Frame)
    product_frame.bind("<Enter>", _bind_mousewheel_all)
    product_frame.bind("<Leave>", _unbind_mousewheel_all)


    def load_product_buttons(parent):
        parent.image_references.clear()
        for widget in parent.winfo_children():
            widget.destroy()
        if not PILLOW_AVAILABLE:
            ttk.Label(parent, text="Lỗi: Vui lòng cài đặt 'Pillow' để xem ảnh.").grid() 
            return
        try:
            products = fetch_query("""
                SELECT MaSP, TenSP, DonGia, ImagePath 
                FROM SanPham WHERE TrangThai = N'Còn bán' ORDER BY TenSP
            """)
            
            placeholder_path = os.path.join('app', 'assets', 'products', 'placeholder.png')
            
            row, col = 0, 0
            NUM_COLUMNS = 5 
            
            for prod in products:
                gia = f"{int(prod['DonGia']):,}"
                btn_text = f"{prod['TenSP']}\n({gia} đ)"
                
                img_path = prod.get('ImagePath') 
                
                if not img_path or not os.path.exists(img_path):
                    img_path = placeholder_path 
                
                try:
                    img = Image.open(img_path)
                    img_resized = img.resize((100, 100), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img_resized)
                except Exception as e:
                    print(f"Lỗi xử lý ảnh {img_path}: {e}")
                    img = Image.open(placeholder_path) 
                    img_resized = img.resize((100, 100), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img_resized)
                
                parent.image_references.append(photo)
                prod_info = prod 
                
                btn = ttk.Button(parent, text=btn_text, style="Product.TButton", 
                                 image=photo, 
                                 command=lambda p=prod_info: show_options_window(p)) 
                
                btn.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
                
                col += 1
                if col >= NUM_COLUMNS: 
                    col = 0
                    row += 1
            
            for c in range(NUM_COLUMNS):
                parent.grid_columnconfigure(c, weight=1)
                
        except Exception as e:
            ttk.Label(parent, text=f"Lỗi tải sản phẩm: {e}").grid(row=0, column=0, padx=10, pady=10)
    
    load_product_buttons(scrollable_frame)

    # =========================================================
    # GÁN LỆNH CHO CÁC NÚT (Giai đoạn 3)
    # =========================================================
    
    _search_after_id = None
    
    def find_customer_realtime(*args):
        nonlocal current_customer_info, _search_after_id
        if _search_after_id:
            module_frame.after_cancel(_search_after_id)
        _search_after_id = module_frame.after(300, perform_customer_search)

    def perform_customer_search():
        nonlocal current_customer_info
        keyword = cust_search_var.get().strip()
        if not keyword:
            current_customer_info = {}
            lbl_cust_info.config(text="Khách: [Vãng lai]")
            chk_use_points.config(state="disabled")
            use_points_var.set(False)
            update_totals()
            return
        query = """
            SELECT MaKH, TenKH, DiemTichLuy 
            FROM KhachHang 
            WHERE MaKH LIKE ? OR SDT LIKE ? OR TenKH LIKE ?
        """
        kw = f"%{keyword}%"
        result = fetch_query(query, (kw, kw, kw))
        if result:
            current_customer_info = result[0] 
            diem = current_customer_info.get("DiemTichLuy", 0)
            ten = current_customer_info.get("TenKH", "N/A")
            lbl_cust_info.config(text=f"Khách: {ten} ({diem} điểm)")
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
        update_totals()

    cust_search_var.trace_add("write", find_customer_realtime)
    
    def process_payment():
        nonlocal current_customer_info
        if not tree_cart.get_children():
            messagebox.showwarning("Giỏ hàng trống", "Vui lòng thêm sản phẩm vào hóa đơn.", parent=module_frame)
            return

        mahd = generate_next_mahd(db.cursor)
        manv = employee_id 
        makh = current_customer_info.get("MaKH") 
        
        tong_truoc_giam_gia_str = total_var.get().replace(",", "").split(" ")[0]
        giam_gia_str = discount_var.get().replace(",", "").split(" ")[0]
        tong_sau_giam_gia_str = final_total_var.get().replace(",", "").split(" ")[0]
        
        tong_truoc_giam_gia = Decimal(tong_truoc_giam_gia_str)
        giam_gia = Decimal(giam_gia_str)
        tong_sau_giam_gia = Decimal(tong_sau_giam_gia_str)
        
        diem_su_dung = 0
        if use_points_var.get() and makh:
             diem_su_dung = int(giam_gia / vnd_per_point_ratio)

        confirm_msg = f"Tổng tiền: {int(tong_sau_giam_gia):,} đ\n\nXác nhận thanh toán?"
        if not messagebox.askyesno("Xác nhận Thanh toán", confirm_msg, parent=module_frame):
            return

        try:
            if not manv:
                messagebox.showerror("Lỗi Tài khoản", "Không tìm thấy Mã Nhân viên (MaNV) liên kết với tài khoản này.\nKhông thể tạo hóa đơn.", parent=module_frame)
                return

            query_hd = """
                INSERT INTO HoaDon (MaHD, NgayLap, MaNV, MaKH, TongTien, GiamGia, ThanhTien, TrangThai, DiemSuDung)
                VALUES (?, ?, ?, ?, ?, ?, ?, N'Đã thanh toán', ?)
            """
            params_hd = (mahd, datetime.now(), manv, makh, 
                         tong_truoc_giam_gia, giam_gia, tong_sau_giam_gia, 
                         diem_su_dung)
            
            if not execute_query(query_hd, params_hd):
                raise Exception("Không thể tạo Hóa đơn.")

            for item_id in tree_cart.get_children():
                values = tree_cart.item(item_id, "values")
                tags = tree_cart.item(item_id, "tags")

                masp = tags[0]
                notes = tags[1]
                
                tensp_display, sl, dongia_str, _ = values
                sl = int(sl)
                dongia = Decimal(dongia_str.replace(",", ""))
                
                query_cthd = """
                    INSERT INTO ChiTietHoaDon (MaHD, MaSP, SoLuong, DonGia, GhiChu)
                    VALUES (?, ?, ?, ?, ?)
                """
                params_cthd = (mahd, masp, sl, dongia, notes)
                
                if not execute_query(query_cthd, params_cthd):
                    raise Exception(f"Không thể lưu chi tiết món {masp}.")
            
            recalc_invoice_total(db.cursor, db.conn, mahd)
            deduct_inventory_from_recipe(mahd)
            
            if makh:
                if diem_su_dung > 0:
                    execute_query("UPDATE KhachHang SET DiemTichLuy = DiemTichLuy - ? WHERE MaKH = ?", 
                                  (diem_su_dung, makh))
                update_customer_points(makh, tong_truoc_giam_gia)

            messagebox.showinfo("Thành công", f"Đã thanh toán thành công hóa đơn {mahd}.", parent=module_frame)
            
            if messagebox.askyesno("In hóa đơn", "Bạn có muốn in hóa đơn không?", parent=module_frame):
                try:
                    print_pos_receipt(mahd) 
                except Exception as print_e:
                    messagebox.showerror("Lỗi In", f"Không thể in hóa đơn:\n{print_e}", parent=module_frame)
            
            clear_cart() 

        except Exception as e:
            messagebox.showerror("Lỗi Thanh toán", f"Không thể hoàn tất hóa đơn:\n{e}", parent=module_frame)

    # --- Gán lệnh cho các nút ---
    btn_payment.config(command=process_payment)
    btn_clear_cart.config(command=clear_cart)
    btn_recalc.config(command=update_totals)
    
    # --- Trả về frame chính ---
    return module_frame