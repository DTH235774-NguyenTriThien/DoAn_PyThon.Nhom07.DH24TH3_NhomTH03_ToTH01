# app/utils/employee/tab_salary.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from app import db
import os
from openpyxl import Workbook
from datetime import datetime

# Imports
from app.db import fetch_query, execute_query, execute_scalar
from app.theme import setup_styles
# SỬA 1: Xóa import go_back
# from app.utils.utils import go_back 
from app.utils.export_helper import export_to_excel_from_query
from app.utils.business_helpers import safe_delete 
from app.utils.treeview_helpers import fill_treeview_chunked 

# SỬA 2: Thay đổi chữ ký hàm, loại bỏ root, username, role
# và nhận on_back_callback
def build_tab(parent, on_back_callback):
    """Tab Bảng lương — quản lý lương nhân viên"""
    setup_styles()
    parent.configure(bg="#f5e6ca")

    # ===== THANH CÔNG CỤ (TOP FRAME) =====
    top_frame = tk.Frame(parent, bg="#f9fafb")
    top_frame.pack(fill="x", pady=10, padx=10) 

    # --- Frame NÚT CHỨC NĂNG (Bên phải) ---
    btn_frame = tk.Frame(top_frame, bg="#f9fafb")
    btn_frame.pack(side="right", anchor="n", padx=(10, 0))
    
    ttk.Button(btn_frame, text="🔄 Tải lại", style="Close.TButton",
             command=lambda: refresh_data()).pack(side="left", padx=5)
    
    ttk.Button(btn_frame, text="💾 Xuất Excel", style="Add.TButton",
             command=lambda: export_salary()).pack(side="left", padx=5)

    ttk.Button(btn_frame, text="➕ Tính lương tháng này", style="Add.TButton", # Đổi tên nút
             command=lambda: calculate_or_update_salary(refresh_data)).pack(side="left", padx=5)
    
    ttk.Button(btn_frame, text="✏️ Cập nhật trạng thái", style="Edit.TButton",
             command=lambda: edit_status(tree, refresh_data)).pack(side="left", padx=5)
    
    ttk.Button(btn_frame, text="🗑 Xóa", style="Delete.TButton",
             command=lambda: delete_salary(tree, refresh_data)).pack(side="left", padx=5)
    
    # SỬA 3: Sử dụng on_back_callback cho command
    ttk.Button(btn_frame, text="⬅ Quay lại", style="Close.TButton",
             command=on_back_callback).pack(side="left", padx=5)

    # --- Frame LỌC (Bên trái, tự mở rộng) ---
    filter_frame = tk.Frame(top_frame, bg="#f9fafb")
    filter_frame.pack(side="left", fill="x", expand=True)

    tk.Label(filter_frame, text="🔎 Tìm NV:", font=("Arial", 11),
           bg="#f9fafb").pack(side="left", padx=(5, 2))
    search_var = tk.StringVar()
    entry_search = ttk.Entry(filter_frame, textvariable=search_var, width=30) 
    entry_search.pack(side="left", padx=5, fill="x", expand=True) 

    # Label trạng thái
    status_label_var = tk.StringVar(value="")
    status_label = ttk.Label(filter_frame, textvariable=status_label_var, font=("Arial", 10, "italic"), background="#f9fafb", foreground="blue")
    status_label.pack(side="left", padx=10)

    # ===== TREEVIEW =====
    columns = ["MaLuong", "MaNV", "HoTen", "Thang", "Nam", "TongGio", "LuongThucTe", "TrangThai"]
    headers = {
        "MaLuong": "Mã Lương",
        "MaNV": "Mã NV",
        "HoTen": "Họ tên",
        "Thang": "Tháng",
        "Nam": "Năm",
        "TongGio": "Tổng Giờ",
        "LuongThucTe": "Lương (VNĐ)",
        "TrangThai": "Trạng thái"
    }

    tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)
    for col in columns:
        tree.heading(col, text=headers[col])
        tree.column(col, anchor="center", width=120)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    # ===== HÀM TẢI DỮ LIỆU =====
    def load_data(tree_widget, status_var, keyword=None):
        status_var.set("Đang tải dữ liệu...")
        tree_widget.update_idletasks() 

        query = """
            SELECT BL.MaLuong, NV.MaNV, NV.HoTen, BL.Thang, BL.Nam, BL.TongGio, BL.LuongThucTe, BL.TrangThai
            FROM BangLuong BL
            JOIN NhanVien NV ON BL.MaNV = NV.MaNV
        """
        params = ()
        if keyword:
            query += " WHERE NV.HoTen LIKE ? OR NV.MaNV LIKE ?"
            keyword = f"%{keyword.strip()}%"
            params = (keyword, keyword)
        
        query += " ORDER BY BL.Nam DESC, BL.Thang DESC"

        try:
            rows = db.fetch_query(query, params)
            tree_data = []
            for r in rows:
                tong_gio_f = f"{r['TongGio']:.1f}" if r['TongGio'] is not None else "0.0"
                luong_f = f"{r['LuongThucTe']:,.0f}" if r['LuongThucTe'] is not None else "0"
                
                values_tuple = (
                    r['MaLuong'], r['MaNV'].strip(), r['HoTen'].strip(),
                    r['Thang'], r['Nam'],
                    tong_gio_f, luong_f,
                    r['TrangThai']
                )
                tree_data.append({"iid": r['MaLuong'], "values": values_tuple})

            def on_load_complete():
                status_var.set(f"Đã tải {len(rows)} bản ghi.")
                
            fill_treeview_chunked(
                tree=tree_widget, 
                rows=tree_data, 
                batch=100,
                on_complete=on_load_complete
            )
        except Exception as e:
            status_var.set("Lỗi tải dữ liệu!")
            messagebox.showerror("Lỗi", f"Không thể tải bảng lương: {e}")

    # ===== CÁC HÀM TIỆN ÍCH =====
    def refresh_data():
        keyword = search_var.get().strip()
        load_data(tree, status_label_var, keyword)
    
    def on_search_change(*args):
        refresh_data()
    search_var.trace_add("write", on_search_change)

    # Tải lần đầu
    refresh_data()

# ==============================================================
#  HÀM CRUD VÀ NGHIỆP VỤ
# ==============================================================

# ==============================================================
# SỬA 3: NÂNG CẤP HÀM TÍNH LƯƠNG (LOGIC UPSERT)
# (Phần này giữ nguyên, đã chính xác)
# ==============================================================
def calculate_or_update_salary(refresh_func):
    """
    Tính toán hoặc Cập nhật bảng lương hàng loạt cho tháng hiện tại.
    - INSERT nếu chưa có.
    - UPDATE nếu đã có VÀ Trạng thái = 'Chưa trả'.
    - Bỏ qua nếu Trạng thái = 'Đã trả'.
    """
    try:
        now = datetime.now()
        thang, nam = now.month, now.year

        # Lấy danh sách nhân viên đang làm
        nv_query = "SELECT MaNV, LuongCoBan FROM NhanVien WHERE TrangThai=N'Đang làm'"
        nvs = db.fetch_query(nv_query) 

        if not nvs:
            messagebox.showinfo("Thông báo", "Không có nhân viên nào 'Đang làm' để tính lương.")
            return

        count_processed = 0
        
        for nv in nvs:
            manv = nv["MaNV"].strip()
            luongcb = nv["LuongCoBan"]

            # 1. Tính toán lương mới
            sum_query = """
                SELECT SUM(DATEDIFF(MINUTE, ClockIn, ClockOut)) / 60.0
                FROM ChamCong
                WHERE MaNV=? AND MONTH(NgayLam)=? AND YEAR(NgayLam)=?
                      AND ClockIn IS NOT NULL AND ClockOut IS NOT NULL
            """
            tong_gio = db.execute_scalar(sum_query, (manv, thang, nam)) or 0.0 
            
            # =========================================================
            # SỬA LỖI LOGIC TÍNH LƯƠNG TẠI ĐÂY
            # (Giả định LuongCoBan là LƯƠNG THEO GIỜ)
            # =========================================================
            
            # Code CŨ (SAI):
            # luong_thuc_te = float(luongcb or 0) * (float(tong_gio) / 208.0) 
            
            # Code MỚI (ĐÚNG):
            luong_thuc_te = float(luongcb or 0) * float(tong_gio)
            
            # =========================================================

            # 2. Kiểm tra bản ghi hiện có
            check_query = "SELECT MaLuong, TrangThai FROM BangLuong WHERE MaNV=? AND Thang=? AND Nam=?"
            existing_record = db.fetch_query(check_query, (manv, thang, nam))

            if existing_record:
                # ĐÃ TỒN TẠI -> Cân nhắc UPDATE
                current_status = existing_record[0]["TrangThai"]
                maluong = existing_record[0]["MaLuong"]
                
                if current_status == 'Chưa trả':
                    # Chỉ cập nhật nếu CHƯA TRẢ
                    update_query = """
                        UPDATE BangLuong 
                        SET TongGio = ?, LuongThucTe = ?
                        WHERE MaLuong = ?
                    """
                    if db.execute_query(update_query, (tong_gio, luong_thuc_te, maluong)):
                        count_processed += 1
                else:
                    # Nếu 'Đã trả', bỏ qua không xử lý
                    pass 
            else:
                # CHƯA TỒN TẠI -> INSERT
                insert_query = """
                    INSERT INTO BangLuong (MaNV, Thang, Nam, TongGio, LuongThucTe, TrangThai)
                    VALUES (?, ?, ?, ?, ?, N'Chưa trả')
                """
                if db.execute_query(insert_query, (manv, thang, nam, tong_gio, luong_thuc_te)):
                    count_processed += 1

        messagebox.showinfo("✅ Thành công", f"Đã tính toán/cập nhật lương cho {count_processed} nhân viên.")
        refresh_func()

    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể tính lương: {e}")


def edit_status(tree, refresh):
    """Cập nhật trạng thái 'Đã trả' / 'Chưa trả'"""
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn bản ghi cần cập nhật!")
        return

    maluong = sel[0] 
    values = tree.item(maluong)["values"]
    trangthai = values[-1] 
    
    new_state = "Đã trả" if trangthai == "Chưa trả" else "Chưa trả"

    if execute_query("UPDATE BangLuong SET TrangThai=? WHERE MaLuong=?", (new_state, maluong)):
        messagebox.showinfo("✅ Thành công", f"Đã cập nhật trạng thái lương {maluong}.")
        refresh()


def delete_salary(tree, refresh):
    """Xóa bảng lương (dùng safe_delete)"""
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn bản ghi cần xóa!")
        return

    maluong = sel[0] 

    safe_delete(
        table_name="BangLuong",
        key_column="MaLuong",
        key_value=maluong,
        cursor=db.cursor,
        conn=db.conn,
        refresh_func=refresh,
        item_label="bảng lương"
    )

def export_salary():
    """Xuất bảng lương ra Excel (dùng helper)"""
    query = """
        SELECT BL.MaLuong, NV.MaNV, NV.HoTen, BL.Thang, BL.Nam, 
               BL.TongGio, BL.LuongThucTe, BL.TrangThai
        FROM BangLuong BL
        JOIN NhanVien NV ON BL.MaNV = NV.MaNV
        ORDER BY BL.Nam DESC, BL.Thang DESC
    """
    headers = ["Mã Lương", "Mã NV", "Họ Tên", "Tháng", "Năm", "Tổng Giờ", "Lương (VNĐ)", "Trạng Thái"]
    
    try:
        export_to_excel_from_query(db.cursor, query, headers, title="Bảng Lương")
        messagebox.showinfo("✅ Thành công", "Xuất file Excel thành công!")
    except Exception as e:
        messagebox.showerror("Lỗi xuất file", f"Không thể xuất file Excel:\n{e}")