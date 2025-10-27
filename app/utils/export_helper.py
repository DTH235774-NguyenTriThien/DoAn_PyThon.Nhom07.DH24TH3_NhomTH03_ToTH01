import os
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from datetime import datetime
from tkinter import messagebox

def export_to_excel_from_query(cursor, query, headers, title="Dữ liệu", filename=None):
    """
    Helper xuất dữ liệu từ query ra Excel với định dạng đẹp.
    ---
    cursor: con trỏ DB đã kết nối (vd: db.cursor)
    query: chuỗi SQL SELECT cần xuất
    headers: list tiêu đề cột (VD: ["Mã NV", "Họ tên", "Chức vụ", ...])
    title: tiêu đề sheet (VD: "Bảng Lương Tháng 10")
    filename: tên file (tự động nếu None)
    """

    try:
        # === Tạo thư mục export ===
        export_dir = "exports"
        os.makedirs(export_dir, exist_ok=True)

        now = datetime.now()
        filename = filename or f"{title.replace(' ', '_')}_{now.strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(export_dir, filename)

        # === Chạy truy vấn ===
        cursor.execute(query)
        rows = cursor.fetchall()

        if not rows:
            messagebox.showinfo("Không có dữ liệu", "⚠️ Không có dữ liệu để xuất!")
            return

        # === Tạo workbook ===
        wb = Workbook()
        ws = wb.active
        ws.title = title[:31]  # Excel giới hạn 31 ký tự

        # Header
        ws.append(headers)

        # Ghi dữ liệu
        for row in rows:
            ws.append([str(item).strip() if item is not None else "" for item in row])

        # Định dạng
        bold_font = Font(bold=True)
        center = Alignment(horizontal="center", vertical="center")
        fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")

        for col in ws.columns:
            max_length = 0
            for cell in col:
                cell.alignment = center
                if cell.row == 1:
                    cell.font = bold_font
                    cell.fill = fill
                max_length = max(max_length, len(str(cell.value)) if cell.value else 0)
            ws.column_dimensions[col[0].column_letter].width = max_length + 2

        wb.save(filepath)
        messagebox.showinfo("✅ Xuất thành công", f"Đã lưu file Excel:\n{filepath}")

    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể xuất file Excel: {e}")
