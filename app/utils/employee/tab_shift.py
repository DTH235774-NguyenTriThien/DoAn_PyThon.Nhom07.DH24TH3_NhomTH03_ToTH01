# app/utils/employee/tab_shift.py
import tkinter as tk
from tkinter import ttk, messagebox
from app import db
from app.theme import setup_styles
from datetime import datetime, time

# Import helpers
from app.db import fetch_query, execute_query
from app.utils.business_helpers import safe_delete, validate_shift_time
from app.utils.time_helpers import parse_time
from app.utils.id_helpers import generate_next_maca
from app.utils.treeview_helpers import fill_treeview_chunked
# Sửa lỗi Căn giữa: Import helper
from app.utils.utils import center_window_relative

def build_tab(parent, on_back_callback=None):
    """Tab 2 - Xây dựng giao diện Ca làm việc"""
    setup_styles()
    parent.configure(bg="#f5e6ca")

    # --- Thanh chức năng ---
    top_frame = tk.Frame(parent, bg="#f9fafb")
    top_frame.pack(fill="x", pady=10, padx=10)

    btn_frame = tk.Frame(top_frame, bg="#f9fafb")
    btn_frame.pack(side="right", anchor="n", padx=(10, 0))

    filter_frame = tk.Frame(top_frame, bg="#f9fafb")
    filter_frame.pack(side="left", fill="x", expand=True)

    tk.Label(filter_frame, text="🔎 Tìm ca làm:", font=("Arial", 11),
             bg="#f9fafb").pack(side="left", padx=5)
    search_var = tk.StringVar()
    entry_search = ttk.Entry(filter_frame, textvariable=search_var, width=30)
    entry_search.pack(side="left", padx=5, fill="x", expand=True)
    
    status_label_var = tk.StringVar(value="")
    status_label = ttk.Label(filter_frame, textvariable=status_label_var, font=("Arial", 10, "italic"), background="#f9fafb", foreground="blue")
    status_label.pack(side="left", padx=10)

    # --- Treeview ---
    tree_frame = tk.Frame(parent, bg="#f5e6ca")
    tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    columns = ["MaCa", "TenCa", "GioBatDau", "GioKetThuc"]
    headers = {"MaCa": "Mã Ca", "TenCa": "Tên Ca", "GioBatDau": "Giờ Bắt đầu", "GioKetThuc": "Giờ Kết thúc"}

    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
    for col in columns:
        tree.heading(col, text=headers[col])
        tree.column(col, anchor="center", width=180)
    tree.pack(fill="both", expand=True)

    def load_data(tree_widget, status_var, keyword=None):
        """Tải và hiển thị dữ liệu Ca làm."""
        status_var.set("Đang tải dữ liệu...")
        tree_widget.update_idletasks() 
        query = "SELECT MaCa, TenCa, GioBatDau, GioKetThuc FROM CaLam"
        params = ()
        if keyword and keyword.strip() != "":
            kw = f"%{keyword.strip()}%"
            query += " WHERE CAST(MaCa AS NVARCHAR(10)) LIKE ? OR TenCa LIKE ? OR FORMAT(GioBatDau, 'HH:mm') LIKE ? OR FORMAT(GioKetThuc, 'HH:mm') LIKE ?"
            params = (kw, kw, kw, kw)
        query += " ORDER BY MaCa"
        try:
            rows = db.fetch_query(query, params)
            tree_data = []
            for row in rows:
                giobd_obj = row["GioBatDau"]
                giobd = giobd_obj.strftime("%H:%M") if giobd_obj else ""
                giokt_obj = row["GioKetThuc"]
                giokt = giokt_obj.strftime("%H:%M") if giokt_obj else ""
                values_tuple = (row["MaCa"], row["TenCa"] or "", giobd, giokt)
                tree_data.append({"iid": row["MaCa"], "values": values_tuple})

            def on_load_complete():
                status_var.set(f"Đã tải {len(rows)} ca làm.")
            fill_treeview_chunked(
                tree=tree_widget, 
                rows=tree_data, 
                on_complete=on_load_complete
            )
        except Exception as e:
            status_var.set("Lỗi tải dữ liệu!")
            messagebox.showerror("Lỗi", f"Không thể tải dữ liệu ca làm: {e}")

    # --- Nút chức năng ---
    def refresh_data():
        load_data(tree, status_label_var, search_var.get().strip())

    ttk.Button(btn_frame, text="🔄 Tải lại", style="Close.TButton",
               command=refresh_data).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="➕ Thêm", style="Add.TButton",
               command=lambda: add_shift(tree, refresh_data)).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="✏️ Sửa", style="Edit.TButton",
               command=lambda: edit_shift(tree, refresh_data)).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="🗑 Xóa", style="Delete.TButton",
               command=lambda: delete_shift(tree, refresh_data)).pack(side="left", padx=5)
    
    if on_back_callback:
        ttk.Button(btn_frame, text="⬅ Quay lại Dashboard", style="Close.TButton",
                   command=on_back_callback).pack(side="left", padx=5)

    # --- Gán sự kiện ---
    def on_search_change(event=None):
        keyword = search_var.get().strip()
        load_data(tree, status_label_var, keyword)
    entry_search.bind("<KeyRelease>", on_search_change)

    def on_double_click(_):
        sel = tree.selection()
        if sel:
            edit_shift(tree, refresh_data)
    tree.bind("<Double-1>", on_double_click)
    
    refresh_data()

# ==============================================================
#  HÀM CRUD (POP-UP)
# ==============================================================
def add_shift(parent_tree, refresh):
    """Mở cửa sổ pop-up để thêm Ca làm mới."""
    win = tk.Toplevel()
    win.title("➕ Thêm ca làm")
    win.configure(bg="#f8f9fa")
    
    # Sửa lỗi Căn giữa
    center_window_relative(win, parent_tree.master, 420, 320)

    form = tk.Frame(win, bg="#f8f9fa")
    form.pack(padx=20, pady=15, fill="both", expand=True)

    ttk.Label(form, text="Tên Ca", font=("Arial", 11), background="#f8f9fa").grid(row=0, column=0, sticky="w", padx=8, pady=6)
    ca_options = ["Sáng", "Chiều", "Tối", "Khác"]
    ca_var = tk.StringVar(value="Sáng")
    cb_tenca = ttk.Combobox(form, values=ca_options, textvariable=ca_var, font=("Arial", 11))
    cb_tenca.grid(row=0, column=1, padx=8, pady=6, sticky="ew")
    ttk.Label(form, text="Giờ Bắt đầu", font=("Arial", 11), background="#f8f9fa").grid(row=1, column=0, sticky="w", padx=8, pady=6)
    ttk.Label(form, text="Giờ Kết thúc", font=("Arial", 11), background="#f8f9fa").grid(row=2, column=0, sticky="w", padx=8, pady=6)
    time_options = [f"{h:02d}:00" for h in range(0, 24)]
    cb_batdau = ttk.Combobox(form, values=time_options, font=("Arial", 11))
    cb_ketthuc = ttk.Combobox(form, values=time_options, font=("Arial", 11))
    cb_batdau.grid(row=1, column=1, padx=8, pady=6, sticky="ew")
    cb_ketthuc.grid(row=2, column=1, padx=8, pady=6, sticky="ew")
    
    def auto_fill_time(event=None):
        ca = ca_var.get().lower()
        if ca == "sáng": cb_batdau.set("07:00"); cb_ketthuc.set("11:00")
        elif ca == "chiều": cb_batdau.set("13:00"); cb_ketthuc.set("17:00")
        elif ca == "tối": cb_batdau.set("17:00"); cb_ketthuc.set("22:00")
        else: cb_batdau.set(""); cb_ketthuc.set("")
        
    cb_tenca.bind("<<ComboboxSelected>>", auto_fill_time)
    auto_fill_time() 

    def submit():
        try:
            ten = cb_tenca.get().strip()
            bd = cb_batdau.get().strip()
            kt = cb_ketthuc.get().strip()
            maca = generate_next_maca(db.cursor)
            if not ten: messagebox.showwarning("Thiếu thông tin", "⚠️ Tên ca không được để trống.", parent=win); return
            if not bd or not kt: messagebox.showwarning("Thiếu thông tin", "⚠️ Giờ bắt đầu và kết thúc không được để trống.", parent=win); return
            if not validate_shift_time(bd, kt, exclude_maca=maca, parent=win, allow_partial_overlap=True): return
            
            query = "INSERT INTO CaLam (MaCa, TenCa, GioBatDau, GioKetThuc) VALUES (?, ?, ?, ?)"
            if db.execute_query(query, (maca, ten, bd, kt)):
                messagebox.showinfo("✅ Thành công", f"Đã thêm ca làm '{ten}'.", parent=win)
                win.destroy()
                refresh()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm ca làm: {e}", parent=win)

    btn_frame = tk.Frame(win, bg="#f8f9fa")
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="💾 Lưu thay đổi", command=lambda: submit()).pack(ipadx=10, ipady=5)

def edit_shift(tree, refresh):
    """Mở cửa sổ pop-up để sửa Ca làm."""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn ca làm cần sửa!"); return
    maca = selected[0]; values = tree.item(maca)["values"]
    _, tenca, giobd, giokt = values 
    win = tk.Toplevel()
    win.title(f"✏️ Sửa ca làm {maca}")
    win.configure(bg="#f8f9fa")
    
    # Sửa lỗi Căn giữa
    center_window_relative(win, tree.master, 420, 320)

    form = tk.Frame(win, bg="#f8f9fa")
    form.pack(padx=20, pady=15, fill="both", expand=True)

    ttk.Label(form, text=f"Mã Ca: {maca}", background="#f8f9fa", font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=6)
    ttk.Label(form, text="Tên Ca", font=("Arial", 11), background="#f8f9fa").grid(row=1, column=0, sticky="w", padx=8, pady=6)
    ca_options = ["Sáng", "Chiều", "Tối", "Khác"]
    ca_var = tk.StringVar(value=tenca)
    cb_tenca = ttk.Combobox(form, values=ca_options, textvariable=ca_var, font=("Arial", 11))
    cb_tenca.grid(row=1, column=1, padx=8, pady=6, sticky="ew")
    ttk.Label(form, text="Giờ Bắt đầu", font=("Arial", 11), background="#f8f9fa").grid(row=2, column=0, sticky="w", padx=8, pady=6)
    ttk.Label(form, text="Giờ Kết thúc", font=("Arial", 11), background="#f8f9fa").grid(row=3, column=0, sticky="w", padx=8, pady=6)
    time_options = [f"{h:02d}:00" for h in range(0, 24)]
    cb_batdau = ttk.Combobox(form, values=time_options, font=("Arial", 11)); cb_batdau.set(giobd)
    cb_ketthuc = ttk.Combobox(form, values=time_options, font=("Arial", 11)); cb_ketthuc.set(giokt)
    cb_batdau.grid(row=2, column=1, padx=8, pady=6, sticky="ew")
    cb_ketthuc.grid(row=3, column=1, padx=8, pady=6, sticky="ew")
    
    def auto_fill_time(event=None):
        ca = ca_var.get().lower()
        if ca == "sáng": cb_batdau.set("07:00"); cb_ketthuc.set("11:00")
        elif ca == "chiều": cb_batdau.set("13:00"); cb_ketthuc.set("17:00")
        elif ca == "tối": cb_batdau.set("17:00"); cb_ketthuc.set("22:00")
        
    cb_tenca.bind("<<ComboboxSelected>>", auto_fill_time)

    def save():
        try:
            ten = cb_tenca.get().strip()
            bd = cb_batdau.get().strip()
            kt = cb_ketthuc.get().strip()
            if not ten: messagebox.showwarning("Thiếu thông tin", "⚠️ Tên ca không được để trống.", parent=win); return
            if not bd or not kt: messagebox.showwarning("Thiếu thông tin", "⚠️ Giờ bắt đầu và kết thúc không được để trống.", parent=win); return
            if not validate_shift_time(bd, kt, exclude_maca=maca, parent=win, allow_partial_overlap=True): return
            
            query = "UPDATE CaLam SET TenCa=?, GioBatDau=?, GioKetThuc=? WHERE MaCa=?"
            if db.execute_query(query, (ten, bd, kt, maca)):
                messagebox.showinfo("✅ Thành công", f"Đã cập nhật ca làm {maca}.", parent=win)
                refresh()
                win.destroy()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể cập nhật ca làm: {e}", parent=win)
    
    btn_frame = tk.Frame(win, bg="#f8f9fa")
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="💾 Lưu thay đổi", command=lambda: save()).pack(ipadx=10, ipady=5)

def delete_shift(tree, refresh):
    """Xóa Ca làm."""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn bản ghi cần xóa!"); return
    maca = selected[0] 
    try:
        safe_delete(
            table_name="CaLam",
            key_column="MaCa",
            key_value=maca,
            cursor=db.cursor,
            conn=db.conn,
            refresh_func=refresh,
            item_label="ca làm"
        )
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể xóa Ca làm: {e}")