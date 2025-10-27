import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from app import db
from app.db import execute_query
from app.utils.employee.tab_attendance import combine_date_time  # nếu cần tính giờ
from app.theme import setup_styles
from app.utils.utils import go_back
import os
from app.utils.export_helper import export_to_excel_from_query
from openpyxl import Workbook
from datetime import datetime



def build_tab(parent, root=None, username=None, role=None):
    """Tab Bảng lương — quản lý lương nhân viên"""
    setup_styles()
    parent.configure(bg="#f5e6ca")

    # ===== THANH CÔNG CỤ =====
    top_frame = tk.Frame(parent, bg="#f9fafb")
    top_frame.pack(fill="x", pady=10)

    tk.Label(top_frame, text="💰 Quản lý bảng lương", font=("Arial", 13, "bold"),
             bg="#f9fafb", fg="#333").pack(side="left", padx=10)

    search_var = tk.StringVar()
    entry_search = ttk.Entry(top_frame, textvariable=search_var, width=35)
    entry_search.pack(side="left", padx=5)

    def on_search_change(*args):
        keyword = search_var.get().strip()
        load_data(keyword)

    search_var.trace_add("write", on_search_change)

    ttk.Button(top_frame, text="🔄 Tải lại", style="Close.TButton",
            command=lambda: [search_var.set(""), load_data()]).pack(side="left", padx=5)
    
    ttk.Button(top_frame, text="💾 Xuất Excel", style="Add.TButton",
           command=lambda: export_salary()).pack(side="left", padx=5)



    ttk.Button(top_frame, text="➕ Tạo lương mới", style="Add.TButton",
               command=lambda: generate_salary()).pack(side="left", padx=5)
    
    ttk.Button(top_frame, text="✏️ Cập nhật trạng thái", style="Edit.TButton",
               command=lambda: edit_status(tree, load_data)).pack(side="left", padx=5)
    
    ttk.Button(top_frame, text="🗑 Xóa", style="Delete.TButton",
               command=lambda: delete_salary(tree, load_data)).pack(side="left", padx=5)
    
    ttk.Button(top_frame, text="⬅ Quay lại", style="Close.TButton",
               command=lambda: go_back(root, username, role)).pack(side="right", padx=5)

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
    def load_data(keyword=None):
        for item in tree.get_children():
            tree.delete(item)

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

        db.cursor.execute(query, params)
        rows = db.cursor.fetchall()

        for r in rows:
            tree.insert("", "end", values=[
                r.MaLuong, r.MaNV.strip(), r.HoTen.strip(),
                r.Thang, r.Nam,
                f"{r.TongGio:.1f}", f"{r.LuongThucTe:,.0f}",
                r.TrangThai
            ])

    load_data()

    # ===== HÀM TẠO LƯƠNG MỚI =====
    def generate_salary():
        try:
            now = datetime.now()
            thang, nam = now.month, now.year

            # Lấy danh sách nhân viên đang làm
            db.cursor.execute("SELECT MaNV, LuongCoBan FROM NhanVien WHERE TrangThai=N'Đang làm'")
            nvs = db.cursor.fetchall()

            count_added = 0
            for nv in nvs:
                manv, luongcb = nv.MaNV.strip(), nv.LuongCoBan

                # Tính tổng giờ trong tháng
                db.cursor.execute("""
                    SELECT SUM(DATEDIFF(MINUTE, ClockIn, ClockOut)) / 60.0
                    FROM ChamCong
                    WHERE MaNV=? AND MONTH(NgayLam)=? AND YEAR(NgayLam)=?
                          AND ClockIn IS NOT NULL AND ClockOut IS NOT NULL
                """, (manv, thang, nam))
                tong_gio = db.cursor.fetchone()[0] or 0

                luong_thuc_te = float(luongcb) * (float(tong_gio) / 208.0)

                # Thêm vào bảng lương nếu chưa tồn tại
                db.cursor.execute("""
                    SELECT COUNT(*) FROM BangLuong WHERE MaNV=? AND Thang=? AND Nam=?
                """, (manv, thang, nam))
                if db.cursor.fetchone()[0] == 0:
                    execute_query("""
                        INSERT INTO BangLuong (MaNV, Thang, Nam, TongGio, LuongThucTe, TrangThai)
                        VALUES (?, ?, ?, ?, ?, N'Chưa trả')
                    """, (manv, thang, nam, tong_gio, luong_thuc_te))
                    count_added += 1

            messagebox.showinfo("✅ Thành công", f"Đã tạo bảng lương cho {count_added} nhân viên.")
            load_data()

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tạo bảng lương: {e}")

    # ===== CẬP NHẬT TRẠNG THÁI =====
    def edit_status(tree, refresh):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn bản ghi cần cập nhật!")
            return

        val = tree.item(sel[0])["values"]
        maluong, trangthai = val[0], val[-1]
        new_state = "Đã trả" if trangthai == "Chưa trả" else "Chưa trả"

        if execute_query("UPDATE BangLuong SET TrangThai=? WHERE MaLuong=?", (new_state, maluong)):
            messagebox.showinfo("✅ Thành công", f"Đã cập nhật trạng thái lương {maluong}.")
            refresh()

    # ===== XÓA BẢNG LƯƠNG =====
    def delete_salary(tree, refresh):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn bản ghi cần xóa!")
            return

        val = tree.item(sel[0])["values"]
        maluong = val[0]

        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa bảng lương {maluong}?"):
            if execute_query("DELETE FROM BangLuong WHERE MaLuong=?", (maluong,)):
                messagebox.showinfo("✅ Thành công", f"Đã xóa bảng lương {maluong}.")
                refresh()

def export_salary():
    query = """
        SELECT BL.MaLuong, NV.MaNV, NV.HoTen, BL.Thang, BL.Nam, 
               BL.TongGio, BL.LuongThucTe, BL.TrangThai
        FROM BangLuong BL
        JOIN NhanVien NV ON BL.MaNV = NV.MaNV
        ORDER BY BL.Nam DESC, BL.Thang DESC
    """
    headers = ["Mã Lương", "Mã NV", "Họ Tên", "Tháng", "Năm", "Tổng Giờ", "Lương (VNĐ)", "Trạng Thái"]
    export_to_excel_from_query(db.cursor, query, headers, title="Bảng Lương")
