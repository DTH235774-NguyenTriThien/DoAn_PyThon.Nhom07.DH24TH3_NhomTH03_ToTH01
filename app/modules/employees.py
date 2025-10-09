# app/modules/employees.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from app import db
from app.utils import clear_window


def show_employee_module(root, username=None, role=None):
    """Giao diện quản lý nhân viên (phiên bản frame-based, không mở cửa sổ mới)."""
    clear_window(root)
    root.title("Quản lý nhân viên")

    # ====== THANH TIÊU ĐỀ ======
    header = tk.Frame(root, bg="#3e2723", height=70)
    header.pack(fill="x")
    tk.Label(header, text="📋 QUẢN LÝ NHÂN VIÊN", bg="#3e2723", fg="white",
             font=("Arial", 18, "bold")).pack(pady=15)

    # ====== KHUNG NÚT CHỨC NĂNG ======
    top_frame = tk.Frame(root, bg="#f9fafb")
    top_frame.pack(fill="x", pady=10)

    search_var = tk.StringVar()
    tk.Label(top_frame, text="🔎 Tìm nhân viên:", font=("Arial", 11), bg="#f9fafb").pack(side="left", padx=5)
    entry_search = ttk.Entry(top_frame, textvariable=search_var, width=40)
    entry_search.pack(side="left", padx=5)

    ttk.Button(top_frame, text="Tìm", command=lambda: load_data(search_var.get())).pack(side="left", padx=5)
    ttk.Button(top_frame, text="Tải lại", command=lambda: load_data()).pack(side="left", padx=5)
    ttk.Button(top_frame, text="➕ Thêm", command=lambda: add_employee(load_data)).pack(side="left", padx=5)
    ttk.Button(top_frame, text="✏️ Sửa", command=lambda: edit_employee(tree, load_data)).pack(side="left", padx=5)
    ttk.Button(top_frame, text="🗑️ Xóa", command=lambda: delete_employee(tree, load_data)).pack(side="left", padx=5)
    ttk.Button(top_frame, text="⬅ Quay lại", command=lambda: go_back(root, username, role)).pack(side="right", padx=10)

    # ====== BẢNG HIỂN THỊ ======
    columns = ("MaNV", "HoTen", "GioiTinh", "NgaySinh", "ChucVu", "LuongCoBan", "TrangThai")
    tree = ttk.Treeview(root, columns=columns, show="headings", height=15)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=120)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    def load_data(keyword=None):
        """Tải danh sách nhân viên"""
        for item in tree.get_children():
            tree.delete(item)
        query = "SELECT MaNV, HoTen, GioiTinh, NgaySinh, ChucVu, LuongCoBan, TrangThai FROM NhanVien"
        if keyword:
            query += " WHERE MaNV LIKE ? OR HoTen LIKE ?"
            db.cursor.execute(query, (f"%{keyword}%", f"%{keyword}%"))
        else:
            db.cursor.execute(query)
        rows = db.cursor.fetchall()
        for row in rows:
            tree.insert("", "end", values=[
                row.MaNV.strip(), row.HoTen, row.GioiTinh,
                row.NgaySinh.strftime("%d/%m/%Y") if row.NgaySinh else "",
                row.ChucVu, f"{int(row.LuongCoBan):,}", row.TrangThai
            ])

    load_data()


def add_employee(refresh):
    """Thêm nhân viên mới"""
    win = tk.Toplevel()
    win.title("Thêm nhân viên mới")
    win.geometry("400x400")

    labels = ["Mã NV", "Họ tên", "Giới tính", "Ngày sinh (YYYY-MM-DD)",
              "Chức vụ", "Lương cơ bản", "Trạng thái"]
    entries = {}
    for i, text in enumerate(labels):
        ttk.Label(win, text=text).grid(row=i, column=0, padx=10, pady=5, sticky="w")
        entry = ttk.Entry(win, width=30)
        entry.grid(row=i, column=1, padx=10, pady=5)
        entries[text] = entry

    def submit():
        try:
            manv = entries["Mã NV"].get().strip()
            hoten = entries["Họ tên"].get().strip()
            gt = entries["Giới tính"].get().strip()
            ngs = entries["Ngày sinh (YYYY-MM-DD)"].get().strip()
            cv = entries["Chức vụ"].get().strip()
            luong = float(entries["Lương cơ bản"].get().strip())
            tt = entries["Trạng thái"].get().strip()

            # Kiểm tra bắt buộc
            if not manv or not hoten:
                messagebox.showwarning("Thiếu thông tin", "Mã NV và Họ tên là bắt buộc.")
                return

            if ngs:
                ngs = datetime.strptime(ngs, "%Y-%m-%d").date()

            db.cursor.execute("""
                INSERT INTO NhanVien (MaNV, HoTen, GioiTinh, NgaySinh, ChucVu, LuongCoBan, TrangThai)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (manv, hoten, gt, ngs, cv, luong, tt))
            db.conn.commit()

            messagebox.showinfo("Thành công", "Đã thêm nhân viên mới!")

            #Gọi lại callback load_data (tự động làm mới Treeview)
            refresh()

            # ✅ Tự động chọn nhân viên vừa thêm (dòng cuối cùng của Treeview)
            try:
                tree = None
                for widget in win.master.winfo_children():
                    if isinstance(widget, ttk.Treeview):
                        tree = widget
                        break
                if tree:
                    tree.selection_set(tree.get_children()[-1])
                    tree.see(tree.get_children()[-1])
            except Exception:
                pass

            win.destroy()

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm: {e}")

    ttk.Button(win, text="Lưu", command=submit).grid(row=len(labels), column=0, columnspan=2, pady=10)



    def edit_employee(tree, refresh):
        """Sửa thông tin nhân viên"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn nhân viên cần sửa!")
            return
        values = tree.item(selected[0])["values"]
        manv = values[0]

        win = tk.Toplevel()
        win.title(f"Sửa nhân viên {manv}")
        win.geometry("400x400")

        columns = ["Họ tên", "Giới tính", "Ngày sinh (YYYY-MM-DD)",
                "Chức vụ", "Lương cơ bản", "Trạng thái"]
        entries = {}
        current = dict(zip(columns, values[1:]))
        for i, text in enumerate(columns):
            ttk.Label(win, text=text).grid(row=i, column=0, padx=10, pady=5, sticky="w")
            entry = ttk.Entry(win, width=30)
            entry.grid(row=i, column=1, padx=10, pady=5)
            entry.insert(0, current[text])
            entries[text] = entry

        def save():
            try:
                hoten = entries["Họ tên"].get().strip()
                gt = entries["Giới tính"].get().strip()
                ngs = entries["Ngày sinh (YYYY-MM-DD)"].get().strip()
                cv = entries["Chức vụ"].get().strip()
                luong = float(entries["Lương cơ bản"].get().replace(",", "").strip())
                tt = entries["Trạng thái"].get().strip()
                if ngs:
                    ngs = datetime.strptime(ngs, "%Y-%m-%d").date()

                db.cursor.execute("""
                    UPDATE NhanVien
                    SET HoTen=?, GioiTinh=?, NgaySinh=?, ChucVu=?, LuongCoBan=?, TrangThai=?
                    WHERE MaNV=?
                """, (hoten, gt, ngs, cv, luong, tt, manv))
                db.conn.commit()

                messagebox.showinfo("Thành công", "Cập nhật thông tin thành công!")

                # ✅ Làm mới Treeview sau khi cập nhật
                refresh()

                win.destroy()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể cập nhật: {e}")

        ttk.Button(win, text="Lưu", command=save).grid(row=len(columns), column=0, columnspan=2, pady=10)


        def save():
            try:
                hoten = entries["Họ tên"].get().strip()
                gt = entries["Giới tính"].get().strip()
                ngs = entries["Ngày sinh (YYYY-MM-DD)"].get().strip()
                cv = entries["Chức vụ"].get().strip()
                luong = float(entries["Lương cơ bản"].get().replace(",", "").strip())
                tt = entries["Trạng thái"].get().strip()
                if ngs:
                    ngs = datetime.strptime(ngs, "%Y-%m-%d").date()
                db.cursor.execute("""
                    UPDATE NhanVien
                    SET HoTen=?, GioiTinh=?, NgaySinh=?, ChucVu=?, LuongCoBan=?, TrangThai=?
                    WHERE MaNV=?
                """, (hoten, gt, ngs, cv, luong, tt, manv))
                db.conn.commit()
                messagebox.showinfo("Thành công", "Cập nhật thông tin thành công!")
                win.destroy()
                refresh()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể cập nhật: {e}")

        ttk.Button(win, text="Lưu", command=save).grid(row=len(columns), column=0, columnspan=2, pady=10)


    def delete_employee(tree, refresh):
        """Xóa nhân viên"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn nhân viên cần xóa!")
            return
        values = tree.item(selected[0])["values"]
        manv = values[0]
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa nhân viên {manv}?"):
            try:
                db.cursor.execute("DELETE FROM NhanVien WHERE MaNV=?", (manv,))
                db.conn.commit()
                messagebox.showinfo("Thành công", "Đã xóa nhân viên.")
                refresh()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa: {e}")


    def go_back(root, username, role):
        """Quay lại main menu"""
        from app.ui.mainmenu_frame import show_main_menu
        show_main_menu(root, username, role)
