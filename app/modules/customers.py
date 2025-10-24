# app/modules/customers.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from app import db
from app.utils import clear_window, generate_next_makh, safe_delete, normalize_date_input 
from app.theme import setup_styles

def show_customers_module(root, username=None, role=None):
    clear_window(root)
    from app.theme import setup_styles
    setup_styles()

    root.title("Quản lý Khách hàng")
    root.configure(bg="#f5e6ca")

    # --- Header ---
    header = tk.Frame(root, bg="#4b2e05", height=70)
    header.pack(fill="x")
    tk.Label(header, text="👥 QUẢN LÝ KHÁCH HÀNG", bg="#4b2e05", fg="white",
             font=("Segoe UI", 16, "bold")).pack(pady=12)

    # --- Top bar (Tìm kiếm + CRUD + Quay lại) ---
    top_frame = tk.Frame(root, bg="#f5e6ca")
    top_frame.pack(fill="x", pady=6, padx=12)

    left_frame = tk.Frame(top_frame, bg="#f5e6ca")
    left_frame.pack(side="left", fill="x", expand=True)

    search_var = tk.StringVar()
    ttk.Label(left_frame, text="🔍 Tìm:", background="#f5e6ca").pack(side="left", padx=(0,6))
    search_entry = ttk.Entry(left_frame, textvariable=search_var, width=30)
    search_entry.pack(side="left", padx=(0,6))

    # Treeview
    cols = ("MaKH", "TenKH", "SDT", "DiemTichLuy")
    tree = ttk.Treeview(root, columns=cols, show="headings", height=16)
    headers = {"MaKH":"Mã KH", "TenKH":"Tên KH", "SDT":"SĐT", "DiemTichLuy":"Điểm tích lũy"}
    for c in cols:
        tree.heading(c, text=headers[c])
        tree.column(c, anchor="center", width=140 if c!='TenKH' else 300)
    tree.pack(fill="both", expand=True, padx=12, pady=(6,12))

    # Load data
    def load_data(keyword=None):
        try:
            for it in tree.get_children():
                tree.delete(it)
            sql = "SELECT MaKH, TenKH, SDT, DiemTichLuy FROM KhachHang"
            params = ()
            if keyword:
                kw = f"%{keyword}%"
                sql += " WHERE MaKH LIKE ? OR TenKH LIKE ? OR SDT LIKE ?"
                params = (kw, kw, kw)
                db.cursor.execute(sql, params)
            else:
                db.cursor.execute(sql)
            rows = db.cursor.fetchall()
            for r in rows:
                tree.insert("", "end", values=(r.MaKH.strip(), r.TenKH or "", r.SDT or "", r.DiemTichLuy or 0))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách khách hàng: {e}")

    # Search debounce
    search_after = {"id": None}
    def schedule_search(event=None):
        if search_after["id"]:
            root.after_cancel(search_after["id"])
        search_after["id"] = root.after(300, lambda: load_data(search_var.get().strip()))
    search_entry.bind("<KeyRelease>", schedule_search)  # ✅ sửa ở đây

    # Buttons
    ttk.Button(left_frame, text="Tải lại", style="Close.TButton", command=lambda: load_data()).pack(side="left", padx=5)
    ttk.Button(left_frame, text="➕ Thêm", style="Add.TButton", command=lambda: add_customer(load_data)).pack(side="left", padx=5)
    ttk.Button(left_frame, text="✏️ Sửa", style="Edit.TButton", command=lambda: edit_customer(tree, load_data)).pack(side="left", padx=5)
    ttk.Button(left_frame, text="🗑️ Xóa", style="Delete.TButton", command=lambda: delete_customer(tree, load_data)).pack(side="left", padx=5)

    right_frame = tk.Frame(top_frame, bg="#f5e6ca")
    right_frame.pack(side="right")
    ttk.Button(right_frame, text="⬅ Quay lại", style="Close.TButton",
               command=lambda: go_back(root, username, role)).pack(side="right", padx=8)

    load_data()

def add_customer(refresh):
    win = tk.Toplevel()
    win.title("➕ Thêm khách hàng")
    win.geometry("420x320")
    win.resizable(False, False)

    frame = tk.Frame(win, padx=12, pady=12)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Mã KH:").grid(row=0, column=0, sticky="w", pady=6)
    ent_ma = ttk.Entry(frame)
    ent_ma.grid(row=0, column=1, sticky="ew", pady=6)

    ttk.Label(frame, text="Tên KH:").grid(row=1, column=0, sticky="w", pady=6)
    ent_ten = ttk.Entry(frame)
    ent_ten.grid(row=1, column=1, sticky="ew", pady=6)

    ttk.Label(frame, text="SĐT:").grid(row=2, column=0, sticky="w", pady=6)
    ent_sdt = ttk.Entry(frame)
    ent_sdt.grid(row=2, column=1, sticky="ew", pady=6)

    ttk.Label(frame, text="Điểm tích lũy:").grid(row=3, column=0, sticky="w", pady=6)
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
            messagebox.showinfo("OK", f"Đã thêm khách hàng {ma}", parent=win)
            refresh()
            win.destroy()
        except Exception as e:
            db.conn.rollback()
            messagebox.showerror("Lỗi", f"Không thể thêm khách hàng: {e}", parent=win)

    ttk.Button(frame, text="💾 Lưu", style="Add.TButton", command=submit).grid(row=5, column=0, columnspan=2, pady=10)

def edit_customer(tree, refresh):
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Chưa chọn", "Vui lòng chọn khách hàng.", parent=tree.master)
        return
    values = tree.item(sel[0])["values"]
    ma = values[0]
    # fetch data
    db.cursor.execute("SELECT TenKH, SDT FROM KhachHang WHERE MaKH=?", (ma,))
    row = db.cursor.fetchone()
    if not row:
        messagebox.showerror("Lỗi", "Không tìm thấy khách hàng.", parent=tree.master)
        return
    win = tk.Toplevel(tree.master)
    win.title(f"Sửa khách hàng {ma}")
    frame = tk.Frame(win, padx=12, pady=12)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="Mã KH:").grid(row=0, column=0, sticky="w")
    ttk.Label(frame, text=ma).grid(row=0, column=1, sticky="w")
    ttk.Label(frame, text="Tên KH:").grid(row=1, column=0, sticky="w")
    ent_ten = ttk.Entry(frame); ent_ten.grid(row=1, column=1, sticky="ew")
    ent_ten.insert(0, row.TenKH or "")
    ttk.Label(frame, text="SĐT:").grid(row=2, column=0, sticky="w")
    ent_sdt = ttk.Entry(frame); ent_sdt.grid(row=2, column=1, sticky="ew")
    ent_sdt.insert(0, row.SDT or "")
    frame.grid_columnconfigure(1, weight=1)
    def submit():
        try:
            db.cursor.execute("UPDATE KhachHang SET TenKH=?, SDT=? WHERE MaKH=?", (ent_ten.get().strip(), ent_sdt.get().strip(), ma))
            db.conn.commit()
            messagebox.showinfo("OK", "Cập nhật thành công", parent=win)
            refresh()
            win.destroy()
        except Exception as e:
            db.conn.rollback()
            messagebox.showerror("Lỗi", str(e), parent=win)
    ttk.Button(frame, text="Lưu", command=submit).grid(row=4, column=0, columnspan=2, pady=10)

def delete_customer(tree, refresh):
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Chưa chọn", "Vui lòng chọn khách hàng.", parent=tree.master)
        return
    ma = tree.item(sel[0])["values"][0]
    # Use safe_delete to handle FK
    confirm = messagebox.askyesno("Xác nhận", f"Xóa khách hàng {ma}?", parent=tree.master)
    if not confirm:
        return
    try:
        from app.utils import safe_delete
        safe_delete("KhachHang", "MaKH", ma, db.cursor, db.conn, refresh, "khách hàng")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể xóa: {e}", parent=tree.master)

def go_back(root, username, role):
    from app.ui.mainmenu_frame import show_main_menu
    show_main_menu(root, username, role)

