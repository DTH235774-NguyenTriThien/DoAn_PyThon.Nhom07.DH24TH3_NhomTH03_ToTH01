# app/modules/customers.py
import tkinter as tk
from tkinter import ttk, messagebox
from app import db
from app.utils import clear_window, generate_next_makh, safe_delete
from app.theme import setup_styles

def show_customers_module(root, username=None, role=None):

    """Giao diện quản lý khách hàng (phiên bản đồng bộ cấu trúc employee.py)"""
    clear_window(root)
    setup_styles()

    # ====== CẤU HÌNH FORM CHÍNH ======
    root.title("Quản lý khách hàng")
    window_width = 1200
    window_height = 600
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width / 2) - (window_width / 2))
    y = int((screen_height / 2) - (window_height / 2))
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    root.minsize(1000, 550)

    # ====== THANH TIÊU ĐỀ ======
    header = tk.Frame(root, bg="#4b2e05", height=70)
    header.pack(fill="x")
    tk.Label(header, text="👥 QUẢN LÝ KHÁCH HÀNG", bg="#4b2e05", fg="white",
             font=("Segoe UI", 18, "bold")).pack(pady=15)

    # ====== KHUNG CHỨC NĂNG ======
    top_frame = tk.Frame(root, bg="#f5e6ca")
    top_frame.pack(fill="x", pady=10)

    search_var = tk.StringVar()
    tk.Label(top_frame, text="🔎 Tìm khách hàng:", font=("Arial", 11), bg="#f5e6ca").pack(side="left", padx=5)
    entry_search = ttk.Entry(top_frame, textvariable=search_var, width=40)
    entry_search.pack(side="left", padx=5)

    # ====== BẢNG HIỂN THỊ ======
    headers_vn = {
        "MaKH": "Mã KH",
        "TenKH": "Tên khách hàng",
        "SDT": "Số điện thoại",
        "DiemTichLuy": "Điểm tích lũy"
    }
    columns = list(headers_vn.keys())
    tree = ttk.Treeview(root, columns=columns, show="headings", height=15)

    for col in columns:
        tree.heading(col, text=headers_vn[col])
        tree.column(col, anchor="center", width=180 if col != "TenKH" else 300)

    tree.pack(fill="both", expand=True, padx=10, pady=10)

    # ====== LOAD DATA ======
    def load_data(keyword=None):
        """Tải danh sách khách hàng, hỗ trợ tìm kiếm theo nhiều cột"""
        for item in tree.get_children():
            tree.delete(item)

        query = """
            SELECT MaKH, TenKH, SDT, DiemTichLuy
            FROM KhachHang
        """
        params = ()
        if keyword:
            keyword = f"%{keyword.strip()}%"
            query += """
                WHERE MaKH LIKE ? OR
                      TenKH LIKE ? OR
                      SDT LIKE ?
            """
            params = (keyword, keyword, keyword)

        try:
            db.cursor.execute(query, params)
            rows = db.cursor.fetchall()
            keyword_lower = keyword.lower().strip("%") if keyword else ""
            for row in rows:
                makh = row.MaKH.strip()
                ten = row.TenKH or ""
                sdt = row.SDT or ""
                diem = row.DiemTichLuy or 0

                item_id = tree.insert("", "end", values=[makh, ten, sdt, diem])

                # highlight từ khóa tìm kiếm
                if keyword_lower and (
                    keyword_lower in makh.lower()
                    or keyword_lower in ten.lower()
                    or keyword_lower in sdt.lower()
                ):
                    tree.item(item_id, tags=("highlight",))

            tree.tag_configure("highlight", background="#fff3cd", font=("Arial", 11, "bold"))

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách khách hàng: {e}")

    # ====== NÚT CHỨC NĂNG ======
    ttk.Button(top_frame, text="🔄 Tải lại", style="Close.TButton",
               command=load_data).pack(side="left", padx=5)
    
    ttk.Button(top_frame, text="➕ Thêm", style="Add.TButton",
               command=lambda: add_customer(load_data)).pack(side="left", padx=5)
    
    ttk.Button(top_frame, text="✏️ Sửa", style="Edit.TButton",
               command=lambda: edit_customer(tree, load_data)).pack(side="left", padx=5)
    
    ttk.Button(top_frame, text="🗑 Xóa", style="Delete.TButton",
               command=lambda: delete_customer(tree, load_data)).pack(side="left", padx=5)
    
    ttk.Button(top_frame, text="⬅ Quay lại", style="Close.TButton",
               command=lambda: go_back(root, username, role)).pack(side="right", padx=5)

    # ====== SỰ KIỆN TÌM KIẾM REALTIME ======
    def on_search_change(*args):
        keyword = search_var.get().strip()
        load_data(keyword)
    search_var.trace_add("write", on_search_change)

    load_data()


# =========================================================
# ===============  CRUD KHÁCH HÀNG  =======================
# =========================================================

def add_customer(refresh):
    """Thêm khách hàng mới"""
    win = tk.Toplevel()
    win.title("➕ Thêm khách hàng mới")
    win.geometry("420x320")
    win.resizable(False, False)
    win.configure(bg="#f8f9fa")

    frame = tk.Frame(win, bg="#f8f9fa", padx=20, pady=15)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Mã KH:", background="#f8f9fa").grid(row=0, column=0, sticky="w", pady=6)
    ent_ma = ttk.Entry(frame)
    ent_ma.grid(row=0, column=1, sticky="ew", pady=6)

    ttk.Label(frame, text="Tên KH:", background="#f8f9fa").grid(row=1, column=0, sticky="w", pady=6)
    ent_ten = ttk.Entry(frame)
    ent_ten.grid(row=1, column=1, sticky="ew", pady=6)

    ttk.Label(frame, text="SĐT:", background="#f8f9fa").grid(row=2, column=0, sticky="w", pady=6)
    ent_sdt = ttk.Entry(frame)
    ent_sdt.grid(row=2, column=1, sticky="ew", pady=6)

    ttk.Label(frame, text="Điểm tích lũy:", background="#f8f9fa").grid(row=3, column=0, sticky="w", pady=6)
    spin_diem = ttk.Spinbox(frame, from_=0, to=9999, width=10)
    spin_diem.set(0)
    spin_diem.grid(row=3, column=1, sticky="w", pady=6)

    frame.grid_columnconfigure(1, weight=1)

    def submit():
        ma = ent_ma.get().strip().upper()
        ten = ent_ten.get().strip()
        sdt = ent_sdt.get().strip()
        try:
            diem = int(spin_diem.get() or 0)
        except ValueError:
            messagebox.showwarning("Lỗi", "Điểm tích lũy phải là số nguyên!", parent=win)
            return

        try:
            if not ma:
                ma = generate_next_makh(db.cursor)

            db.cursor.execute("SELECT COUNT(*) AS cnt FROM KhachHang WHERE MaKH=?", (ma,))
            if db.cursor.fetchone().cnt > 0:
                messagebox.showwarning("Trùng mã", f"Mã {ma} đã tồn tại.", parent=win)
                return

            db.cursor.execute(
                "INSERT INTO KhachHang (MaKH, TenKH, SDT, DiemTichLuy) VALUES (?, ?, ?, ?)",
                (ma, ten, sdt, diem)
            )
            db.conn.commit()
            messagebox.showinfo("✅ Thành công", f"Đã thêm khách hàng {ma}", parent=win)
            refresh()
            win.destroy()
        except Exception as e:
            db.conn.rollback()
            messagebox.showerror("Lỗi", f"Không thể thêm khách hàng: {e}", parent=win)

    ttk.Button(frame, text="💾 Lưu khách hàng", style="Add.TButton", command=submit).grid(row=5, column=0, columnspan=2, pady=10)


def edit_customer(tree, refresh):
    """Sửa thông tin khách hàng"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn khách hàng cần sửa!")
        return

    values = tree.item(selected[0])["values"]
    makh = values[0]

    win = tk.Toplevel()
    win.title(f"✏️ Sửa khách hàng {makh}")
    win.geometry("420x300")
    win.resizable(False, False)
    win.configure(bg="#f8f9fa")

    frame = tk.Frame(win, bg="#f8f9fa", padx=20, pady=15)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Mã KH:", background="#f8f9fa").grid(row=0, column=0, sticky="w", pady=6)
    ttk.Label(frame, text=makh, background="#f8f9fa").grid(row=0, column=1, sticky="w", pady=6)

    ttk.Label(frame, text="Tên KH:", background="#f8f9fa").grid(row=1, column=0, sticky="w", pady=6)
    ent_ten = ttk.Entry(frame)
    ent_ten.insert(0, values[1])
    ent_ten.grid(row=1, column=1, sticky="ew", pady=6)

    ttk.Label(frame, text="SĐT:", background="#f8f9fa").grid(row=2, column=0, sticky="w", pady=6)
    ent_sdt = ttk.Entry(frame)
    ent_sdt.insert(0, values[2])
    ent_sdt.grid(row=2, column=1, sticky="ew", pady=6)

    ttk.Label(frame, text="Điểm tích lũy:", background="#f8f9fa").grid(row=3, column=0, sticky="w", pady=6)
    spin_diem = ttk.Spinbox(frame, from_=0, to=9999, width=10)
    spin_diem.set(values[3])
    spin_diem.grid(row=3, column=1, sticky="w", pady=6)

    frame.grid_columnconfigure(1, weight=1)

    def save():
        try:
            ten = ent_ten.get().strip()
            sdt = ent_sdt.get().strip()
            diem = int(spin_diem.get() or 0)

            db.cursor.execute("""
                UPDATE KhachHang
                SET TenKH=?, SDT=?, DiemTichLuy=?
                WHERE MaKH=?
            """, (ten, sdt, diem, makh))
            db.conn.commit()

            messagebox.showinfo("✅ Thành công", f"Đã cập nhật khách hàng {makh}.")
            refresh()
            win.destroy()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể cập nhật khách hàng: {e}")

    ttk.Button(frame, text="💾 Lưu thay đổi", style="Edit.TButton", command=save).grid(row=5, column=0, columnspan=2, pady=10)


def delete_customer(tree, refresh):
    """Xóa khách hàng"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn khách hàng cần xóa!")
        return

    values = tree.item(selected[0])["values"]
    makh = values[0]

    confirm = messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa khách hàng {makh}?")
    if not confirm:
        return

    safe_delete(
        table_name="KhachHang",
        key_column="MaKH",
        key_value=makh,
        cursor=db.cursor,
        conn=db.conn,
        refresh_func=refresh,
        item_label="khách hàng"
    )


def go_back(root, username, role):
    """Quay lại main menu"""
    from app.ui.mainmenu_frame import show_main_menu
    show_main_menu(root, username, role)
