# app/modules/customers.py
import tkinter as tk
from tkinter import ttk, messagebox
from app import db
from app.db import execute_query
from app.theme import setup_styles
# SỬA 1: Xóa 'clear_window' và 'center_window'
from app.utils.utils import create_form_window
# Hàm nghiệp vụ
from app.utils.business_helpers import safe_delete
# Hàm sinh mã
from app.utils.id_helpers import generate_next_makh

# SỬA 2: Thay đổi chữ ký hàm, nhận 'parent_frame' thay vì 'root'
def create_customers_module(parent_frame, on_back_callback):

    """Giao diện quản lý khách hàng (phiên bản "nhúng")"""
    
    # SỬA 3: Xóa các lệnh điều khiển cửa sổ (root)
    # clear_window(root)
    setup_styles()
    # root.title("Quản lý Khách hàng")
    # root.configure(bg="#f5e6ca")
    # center_window(root, 1200, 600)
    # root.minsize(1000, 550)

    # SỬA 4: Tạo frame chính bên trong parent_frame
    module_frame = tk.Frame(parent_frame, bg="#f5e6ca")
    # KHÔNG PACK() ở đây, để mainmenu kiểm soát

    # SỬA 5: Gắn các widget con vào 'module_frame'
    
    # ====== THANH TIÊU ĐỀ ======
    header = tk.Frame(module_frame, bg="#4b2e05", height=70)
    header.pack(fill="x")
    tk.Label(header, text="👥 QUẢN LÝ KHÁCH HÀNG", bg="#4b2e05", fg="white",
             font=("Segoe UI", 18, "bold")).pack(pady=15)

    # ====== KHUNG CHỨC NĂNG ======
    top_frame = tk.Frame(module_frame, bg="#f5e6ca")
    top_frame.pack(fill="x", pady=10)

    search_var = tk.StringVar()
    tk.Label(top_frame, text="🔎 Tìm khách hàng:", font=("Arial", 11), bg="#f5e6ca").pack(side="left", padx=5)
    entry_search = ttk.Entry(top_frame, textvariable=search_var, width=40)
    entry_search.pack(side="left", padx=5)

     #   THÊM NHÃN TRẠNG THÁI (STATUS LABEL)
    status_label_var = tk.StringVar(value="")
    status_label = ttk.Label(top_frame, textvariable=status_label_var, 
                             font=("Arial", 10, "italic"), 
                             background="#f5e6ca", foreground="blue")
    status_label.pack(side="left", padx=10, pady=5)

    # ====== BẢNG HIỂN THỊ ======
    headers_vn = {
        "MaKH": "Mã KH",
        "TenKH": "Tên khách hàng",
        "SDT": "Số điện thoại",
        "DiemTichLuy": "Điểm tích lũy"
    }
    columns = list(headers_vn.keys())
    # Gắn tree vào module_frame
    tree = ttk.Treeview(module_frame, columns=columns, show="headings", height=15) 

    for col in columns:
        tree.heading(col, text=headers_vn[col])
        tree.column(col, anchor="center", width=180 if col != "TenKH" else 300)

    tree.pack(fill="both", expand=True, padx=10, pady=10)

    # ====== LOAD DATA ======
    def load_data(keyword=None):

        # Cập nhật nhãn trạng thái
        status_label_var.set("Đang tải dữ liệu...")
        tree.update_idletasks() 

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
            #Cập nhật nhãn khi thành công
            status_label_var.set(f"Đã tải {len(rows)} khách hàng.")

        except Exception as e:
            #Cập nhật nhãn khi lỗi
            status_label_var.set("Lỗi tải dữ liệu!")
            messagebox.showerror("Lỗi", f"Không thể tải danh sách khách hàng: {e}")

    # ====== NÚT CHỨC NĂNG ======
    ttk.Button(top_frame, text="🔄 Tải lại", style="Close.TButton",
             command=load_data).pack(side="left", padx=5)
    
    ttk.Button(top_frame, text="➕ Thêm", style="Add.TButton",
             command=lambda: add_customer(load_data)).pack(side="left", padx=5)
    
    # (role đã được xóa ở GĐ 2)
    ttk.Button(top_frame, text="✏️ Sửa", style="Edit.TButton",
             command=lambda: edit_customer(tree, load_data)).pack(side="left", padx=5)
    
    ttk.Button(top_frame, text="🗑 Xóa", style="Delete.TButton",
             command=lambda: delete_customer(tree, load_data)).pack(side="left", padx=5)
    
    # (callback đã được sửa ở GĐ 2)
    ttk.Button(top_frame, text="⬅ Quay lại", style="Close.TButton",
             command=on_back_callback).pack(side="right", padx=5)
    
    load_data()

    # ====== SỰ KIỆN TÌM KIẾM REALTIME ======
    def on_search_change(*args):
        keyword = search_var.get().strip()
        load_data(keyword)
    search_var.trace_add("write", on_search_change)


    def on_double_click(event):
        sel = tree.selection()
        if sel:
            # (role đã được xóa ở GĐ 2)
            edit_customer(tree, load_data)
    tree.bind("<Double-1>", on_double_click)  

    def refresh():
        load_data() 

    # SỬA 6: Trả về frame chính của module
    return module_frame

# ================================================
# CÁC HÀM CRUD (Giữ nguyên)
# (add_customer, edit_customer, delete_customer)
# ================================================

def add_customer(refresh):
    """Thêm khách hàng mới (chuẩn hóa giao diện form theo Employee/Drink)"""

    # --- Tạo cửa sổ form chuẩn ---
    win, form = create_form_window("➕ Thêm khách hàng", size="460x400")
    entries = {}

    # --- Cấu trúc form ---
    labels = ["Mã KH", "Tên khách hàng", "Số điện thoại", "Điểm tích lũy", "Trạng thái"]
    statuses = ["Thành viên", "Khách lẻ", "VIP", "Ngưng hoạt động"]

    for i, text in enumerate(labels):
        ttk.Label(form, text=text, font=("Arial", 11), background="#f8f9fa")\
            .grid(row=i, column=0, sticky="w", padx=8, pady=8)

        if text == "Trạng thái":
            cb = ttk.Combobox(form, values=statuses, state="readonly", font=("Arial", 11))
            cb.set(statuses[0])
            cb.grid(row=i, column=1, padx=8, pady=8, sticky="ew")
            entries[text] = cb

        elif text == "Điểm tích lũy":
            spin = ttk.Spinbox(form, from_=0, to=99999, font=("Arial", 11), width=10)
            spin.set(0)
            spin.grid(row=i, column=1, padx=8, pady=8, sticky="w")
            entries[text] = spin

        else:
            ent = ttk.Entry(form, font=("Arial", 11))
            ent.grid(row=i, column=1, padx=8, pady=8, sticky="ew")
            entries[text] = ent

    form.grid_columnconfigure(1, weight=1)

    # --- Nút lưu ---
    btn_frame = tk.Frame(win, bg="#f8f9fa")
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="💾 Lưu khách hàng", style="Add.TButton",
             command=lambda: submit()).pack(ipadx=10, ipady=6)

    # --- Hàm submit ---
    def submit():
        try:
            makh = entries["Mã KH"].get().strip().upper()
            ten = entries["Tên khách hàng"].get().strip()
            sdt = entries["Số điện thoại"].get().strip()
            trangthai = entries["Trạng thái"].get().strip()
            try:
                diem = int(entries["Điểm tích lũy"].get())
                if diem < 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Lỗi", "⚠️ Điểm tích lũy phải là số nguyên không âm.", parent=win)
                return

            # --- Kiểm tra thông tin bắt buộc ---
            if not ten:
                messagebox.showwarning("Thiếu thông tin", "⚠️ Tên khách hàng không được để trống.", parent=win)
                return

            # --- Kiểm tra định dạng số điện thoại ---
            if sdt and (not sdt.isdigit() or len(sdt) not in (9, 10, 11)):
                messagebox.showwarning("Lỗi", "⚠️ Số điện thoại không hợp lệ (phải là số, 9–11 ký tự).", parent=win)
                return

            # --- Sinh mã tự động nếu trống ---
            if not makh:
                makh = generate_next_makh(db.cursor)

            # --- Kiểm tra trùng mã ---
            db.cursor.execute("SELECT COUNT(*) FROM KhachHang WHERE MaKH=?", (makh,))
            if db.cursor.fetchone()[0] > 0:
                messagebox.showwarning("Trùng mã", f"⚠️ Mã khách hàng {makh} đã tồn tại.", parent=win)
                return

            # --- Ghi vào DB ---
            query = """
                INSERT INTO KhachHang (MaKH, TenKH, SDT, DiemTichLuy, TrangThai)
                VALUES (?, ?, ?, ?, ?)
            """
            params = (makh, ten, sdt, diem, trangthai)
            if execute_query(query,params):
                messagebox.showinfo("✅ Thành công", f"Đã thêm khách hàng {makh} - {ten}.", parent=win)
                refresh()
                win.destroy()

        except Exception as e:
            db.conn.rollback()
            messagebox.showerror("Lỗi", f"Không thể thêm khách hàng: {e}", parent=win)


# (role đã được xóa ở GĐ 2)
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

            query = """
                UPDATE KhachHang
                SET TenKH=?, SDT=?, DiemTichLuy=?
                WHERE MaKH=?
            """
            params = (ten, sdt, diem, makh)

            if execute_query(query, params):
                messagebox.showinfo("✅ Thành công", f"Đã cập nhật khách hàng {makh}.")
                win.destroy()
                refresh()
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể cập nhật khách hàng: {e}")

    btn_frame = tk.Frame(win, bg="#f8f9fa")
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="💾 Lưu thay đổi", style="Add.TButton",
             command=save).pack(ipadx=10, ipady=6)


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

    # Gọi helper để xóa hóa đơn
    safe_delete(
        table_name="KhachHang",
        key_column="MaKH",
        key_value=makh,
        cursor=db.cursor,
        conn=db.conn,
        refresh_func=refresh,
        item_label="khách hàng"
    )