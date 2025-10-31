# app/modules/settings.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import bcrypt 
import configparser 
import os 

# Import các helper chuẩn của dự án
from app import db
from app.db import fetch_query, execute_query, execute_scalar
from app.theme import setup_styles
from app.utils.utils import create_form_window
from app.utils.business_helpers import safe_delete
from app.utils.treeview_helpers import fill_treeview_chunked

CONFIG_FILE = 'config.ini'

# --- HÀM CHÍNH HIỂN THỊ MODULE ---
def create_settings_module(parent_frame, on_back_callback):
    """Giao diện chính cho Module Cấu hình & Quản lý Tài khoản"""
    
    setup_styles()

    # --- Frame chính của module ---
    module_frame = tk.Frame(parent_frame, bg="#f5e6ca")

    # --- Header ---
    header = tk.Frame(module_frame, bg="#4b2e05", height=70)
    header.pack(fill="x")
    tk.Label(header, text="🔧 CẤU HÌNH HỆ THỐNG & TÀI KHOẢN", bg="#4b2e05", fg="white",
             font=("Segoe UI", 16, "bold")).pack(pady=12)

    # --- Thanh điều khiển (chỉ chứa nút Quay lại) ---
    top_frame = tk.Frame(module_frame, bg="#f9fafb")
    top_frame.pack(fill="x", pady=10, padx=10) 
    ttk.Button(top_frame, text="⬅ Quay lại", style="Close.TButton",
             command=on_back_callback).pack(side="right", padx=5)
    
    # SỬA 1: Khởi tạo status_label_var ở cấp cao nhất
    status_label_var = tk.StringVar(value="")
    
    # Nhãn trạng thái (sẽ được Tab 1 sử dụng)
    status_label = ttk.Label(top_frame, textvariable=status_label_var, 
                             font=("Arial", 10, "italic"), background="#f9fafb", 
                             foreground="blue")
    status_label.pack(side="left", padx=10)


    # --- TẠO NOTEBOOK (Tabs) ---
    notebook = ttk.Notebook(module_frame)
    notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    tab1_accounts = ttk.Frame(notebook, style="TFrame")
    tab2_config = ttk.Frame(notebook, style="TFrame")
    
    notebook.add(tab1_accounts, text="  Quản lý Tài khoản  ")
    notebook.add(tab2_config, text="  Cấu hình Nghiệp vụ  ")

    # SỬA 2: Truyền status_label_var vào cả hai hàm build tab
    
    # =========================================================
    # TAB 1: QUẢN LÝ TÀI KHOẢN
    # =========================================================
    build_account_tab(tab1_accounts, status_label_var)

    # =========================================================
    # TAB 2: CẤU HÌNH NGHIỆP VỤ
    # =========================================================
    build_config_tab(tab2_config, status_label_var) # Truyền vào đây

    # Trả về frame chính
    return module_frame

# ==============================================================
#  BUILD TAB 1: QUẢN LÝ TÀI KHOẢN
# ==============================================================
# SỬA 3: Chấp nhận status_label_var
def build_account_tab(parent, status_label_var):
    """Xây dựng giao diện cho tab Quản lý Tài khoản"""
    
    # --- Thanh điều khiển (Control Frame) ---
    top_frame = tk.Frame(parent, bg="#f9fafb")
    top_frame.pack(fill="x", pady=10, padx=10) 

    # --- Frame Nút (Bên phải) ---
    btn_frame = tk.Frame(top_frame, bg="#f9fafb")
    btn_frame.pack(side="right", anchor="center", padx=(10, 0))
    
    ttk.Button(btn_frame, text="🔄 Tải lại", style="Close.TButton",
             command=lambda: refresh_data()).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="➕ Thêm Tài khoản", style="Add.TButton",
             command=lambda: add_account(refresh_data)).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="🔑 Reset Mật khẩu", style="Edit.TButton",
             command=lambda: reset_password(tree, refresh_data)).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="🗑 Xóa Tài khoản", style="Delete.TButton",
             command=lambda: delete_account(tree, refresh_data)).pack(side="left", padx=5)

    # --- Frame Lọc (Bên trái) ---
    filter_frame = tk.Frame(top_frame, bg="#f9fafb")
    filter_frame.pack(side="left", fill="x", expand=True)
    
    tk.Label(filter_frame, text="🔎 Tìm Tên ĐN:", font=("Arial", 11),
           bg="#f9fafb").pack(side="left", padx=(5, 2))
    search_var = tk.StringVar()
    entry_search = ttk.Entry(filter_frame, textvariable=search_var, width=30) 
    entry_search.pack(side="left", padx=5, fill="x", expand=True) 
    
    # SỬA 4: Xóa dòng khởi tạo status_label_var (vì nó đã được truyền vào)
    # status_label_var = tk.StringVar(value="")
    
    # (Nhãn status_label đã được chuyển lên hàm create_settings_module)
    # status_label = ttk.Label(filter_frame, ...)
    # status_label.pack(side="left", padx=10)

    # ===== TREEVIEW (Danh sách tài khoản) =====
    tree_frame = tk.Frame(parent) 
    tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    columns = ("TenDangNhap", "MaNV", "HoTen", "Role")
    headers = {
        "TenDangNhap": "Tên Đăng nhập", "MaNV": "Mã NV",
        "HoTen": "Tên Nhân viên", "Role": "Vai trò (Role)"
    }
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
    for col, text in headers.items():
        tree.heading(col, text=text)
        tree.column(col, anchor="center", width=150)
    tree.column("MaNV", anchor="center", width=100) 
    tree.column("Role", anchor="center", width=120) 
    tree.pack(fill="both", expand=True)

    # ===== HÀM TẢI DỮ LIỆU =====
    def load_data(tree_widget, status_var, keyword=None):
        status_var.set("Đang tải danh sách tài khoản...")
        tree_widget.update_idletasks() 
        query = """
            SELECT tk.TenDangNhap, tk.MaNV, nv.HoTen, tk.Role 
            FROM TaiKhoan tk
            LEFT JOIN NhanVien nv ON tk.MaNV = nv.MaNV
        """
        params = ()
        if keyword:
            kw = f"%{keyword.strip()}%"
            query += " WHERE tk.TenDangNhap LIKE ? OR nv.HoTen LIKE ? OR tk.Role LIKE ?"
            params = (kw, kw, kw)
        query += " ORDER BY tk.Role, tk.TenDangNhap"
        
        try:
            rows = db.fetch_query(query, params)
            tree_data = []
            for r in rows:
                values_tuple = (
                    r['TenDangNhap'], 
                    r['MaNV'] or "N/A", 
                    r['HoTen'] or "N/A", 
                    r['Role']
                )
                tree_data.append({"iid": r['TenDangNhap'], "values": values_tuple})
            
            fill_treeview_chunked(
                tree_widget, 
                tree_data, 
                on_complete=lambda: status_var.set(f"Đã tải {len(rows)} tài khoản.")
            )
        except Exception as e:
            status_var.set("Lỗi tải tài khoản!")
            messagebox.showerror("Lỗi", f"Không thể tải dữ liệu tài khoản: {e}")

    # ===== HÀM TIỆN ÍCH =====
    def refresh_data():
        keyword = search_var.get().strip()
        load_data(tree, status_label_var, keyword)
    
    search_var.trace_add("write", lambda *args: refresh_data())
    refresh_data() # Tải lần đầu

# ==============================================================
#  BUILD TAB 2: CẤU HÌNH NGHIỆP VỤ
# ==============================================================
# SỬA 5: Chấp nhận status_label_var
def build_config_tab(parent, status_label_var):
    """Xây dựng giao diện cho tab Cấu hình Nghiệp vụ"""
    
    config_group = ttk.LabelFrame(parent, text="  Cấu hình Tích điểm Khách hàng  ", padding=(20, 10))
    config_group.pack(fill="x", expand=False, padx=20, pady=20)

    config_group.grid_columnconfigure(1, weight=1)

    ttk.Label(config_group, text="Số tiền (VNĐ) để được 1 điểm:", font=("Arial", 11))\
        .grid(row=0, column=0, padx=5, pady=10, sticky="w")
    
    vnd_per_point_var = tk.StringVar()
    entry_points = ttk.Entry(config_group, textvariable=vnd_per_point_var, font=("Arial", 11), width=20)
    entry_points.grid(row=0, column=1, padx=5, pady=10, sticky="w")

    btn_bar = tk.Frame(parent) 
    btn_bar.pack(fill="x", padx=20, pady=10)

    ttk.Button(btn_bar, text="💾 Lưu Cấu hình", style="Add.TButton",
             command=lambda: save_config()).pack(side="left", padx=5)
    ttk.Button(btn_bar, text="🔄 Tải lại Cấu hình", style="Close.TButton",
             command=lambda: load_config()).pack(side="left", padx=5)

    def load_config():
        """Đọc từ config.ini và điền vào form"""
        config = configparser.ConfigParser()
        if not os.path.exists(CONFIG_FILE):
             vnd_per_point_var.set("10000") 
             return 

        config.read(CONFIG_FILE, encoding='utf-8')
        vnd_value = config.get('BusinessLogic', 'VND_PER_POINT', fallback='10000')
        vnd_per_point_var.set(vnd_value)
        
        # SỬA 6: Hàm này giờ đã có thể truy cập status_label_var
        status_label_var.set("Đã tải cấu hình.") 

    def save_config():
        """Lấy giá trị từ form và ghi đè vào config.ini"""
        config = configparser.ConfigParser()
        
        if os.path.exists(CONFIG_FILE):
            config.read(CONFIG_FILE, encoding='utf-8')

        try:
            vnd_value = int(vnd_per_point_var.get())
            if vnd_value <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Lỗi", "Số tiền phải là một số nguyên dương.", parent=parent)
            return

        if not config.has_section('BusinessLogic'):
            config.add_section('BusinessLogic')
            
        config.set('BusinessLogic', 'VND_PER_POINT', str(vnd_value))
        
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            messagebox.showinfo("Thành công", "Đã lưu cấu hình thành công.", parent=parent)
            # SỬA 6: Hàm này giờ đã có thể truy cập status_label_var
            status_label_var.set("Đã lưu cấu hình.")
        except Exception as e:
            messagebox.showerror("Lỗi Lưu file", f"Không thể ghi file config.ini:\n{e}", parent=parent)

    load_config()


# ==============================================================
#  HÀM CRUD TÀI KHOẢN (Giữ nguyên)
# ==============================================================

def add_account(refresh_func):
    """Mở cửa sổ Toplevel để thêm tài khoản mới"""
    win, form = create_form_window("➕ Thêm Tài khoản Mới", "450x300")
    entries = {}

    try:
        nv_rows = db.fetch_query("""
            SELECT MaNV, HoTen FROM NhanVien 
            WHERE MaNV NOT IN (SELECT MaNV FROM TaiKhoan WHERE MaNV IS NOT NULL)
            AND TrangThai = N'Đang làm'
        """)
        nv_map = {f"{r['MaNV'].strip()} - {r['HoTen']}": r['MaNV'].strip() for r in nv_rows}
        nv_list = [""] 
        nv_list.extend(list(nv_map.keys()))
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể tải danh sách nhân viên: {e}", parent=win)
        nv_list = [""]
        nv_map = {}

    role_list = ["Admin", "Nhân viên", "Pha chế", "Thu ngân"] 

    labels = ["Tên Đăng nhập", "Mật khẩu", "Liên kết với NV", "Vai trò (Role)"]
    for i, text in enumerate(labels):
        ttk.Label(form, text=text, font=("Arial", 11), background="#f8f9fa")\
            .grid(row=i, column=0, sticky="w", padx=8, pady=8)

        if text == "Mật khẩu":
            ent = ttk.Entry(form, font=("Arial", 11), show="*")
        elif text == "Liên kết với NV":
            ent = ttk.Combobox(form, values=nv_list, state="readonly", font=("Arial", 11))
        elif text == "Vai trò (Role)":
            ent = ttk.Combobox(form, values=role_list, state="readonly", font=("Arial", 11))
            ent.set(role_list[1]) 
        else:
            ent = ttk.Entry(form, font=("Arial", 11))
        
        ent.grid(row=i, column=1, padx=8, pady=8, sticky="ew")
        entries[text] = ent

    form.grid_columnconfigure(1, weight=1)

    def submit():
        try:
            username = entries["Tên Đăng nhập"].get().strip()
            password = entries["Mật khẩu"].get().strip()
            nv_display = entries["Liên kết với NV"].get()
            role = entries["Vai trò (Role)"].get()
            
            manv = nv_map.get(nv_display) 

            if not username or not password or not role:
                messagebox.showwarning("Thiếu thông tin", "Tên đăng nhập, Mật khẩu và Vai trò là bắt buộc.", parent=win)
                return

            if db.execute_scalar("SELECT COUNT(*) FROM TaiKhoan WHERE TenDangNhap = ?", (username,)):
                messagebox.showwarning("Trùng lặp", f"Tên đăng nhập '{username}' đã tồn tại.", parent=win)
                return

            pw_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            hash_bytes = bcrypt.hashpw(pw_bytes, salt)
            hash_str = hash_bytes.decode('utf-8') 

            query = """
                INSERT INTO TaiKhoan (TenDangNhap, MatKhauHash, MaNV, Role)
                VALUES (?, ?, ?, ?)
            """
            params = (username, hash_str, manv, role)
            
            if db.execute_query(query, params):
                messagebox.showinfo("Thành công", f"Đã tạo tài khoản '{username}' thành công.", parent=win)
                refresh_func()
                win.destroy()

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tạo tài khoản: {e}", parent=win)

    btn_frame = tk.Frame(win, bg="#f8f9fa")
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="💾 Lưu Tài khoản", style="Add.TButton",
             command=submit).pack(ipadx=10, ipady=6)


def reset_password(tree, refresh_func):
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn một tài khoản để reset mật khẩu!")
        return
    
    username = selected[0] 
    
    new_pass = simpledialog.askstring(
        "Reset Mật khẩu", 
        f"Nhập mật khẩu MỚI cho tài khoản:\n{username}",
        parent=tree.master,
        show='*'
    )

    if not new_pass:
        return 

    try:
        pw_bytes = new_pass.encode('utf-8')
        salt = bcrypt.gensalt()
        hash_bytes = bcrypt.hashpw(pw_bytes, salt)
        hash_str = hash_bytes.decode('utf-8') 

        query = "UPDATE TaiKhoan SET MatKhauHash = ? WHERE TenDangNhap = ?"
        if db.execute_query(query, (hash_str, username)):
            messagebox.showinfo("Thành công", f"Đã cập nhật mật khẩu cho '{username}'.")
        else:
            messagebox.showerror("Lỗi", "Không thể cập nhật mật khẩu (lỗi SQL).")

    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể hash hoặc lưu mật khẩu: {e}")


def delete_account(tree, refresh_func):
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn tài khoản cần xóa!")
        return
    
    username = selected[0] 
    
    if username.lower() == 'admin':
        messagebox.showerror("Không thể xóa", "Không thể xóa tài khoản 'admin' gốc.")
        return

    safe_delete(
        table_name="TaiKhoan",
        key_column="TenDangNhap",
        key_value=username,
        cursor=db.cursor,
        conn=db.conn,
        refresh_func=refresh_func,
        item_label="tài khoản"
    )