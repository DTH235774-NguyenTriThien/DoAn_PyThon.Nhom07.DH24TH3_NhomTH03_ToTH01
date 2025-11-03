# app/utils/treeview_helpers.py
import math
# import threading # <- Đã xóa import không dùng
import tkinter as tk
from tkinter import ttk

def fill_treeview_chunked(tree: ttk.Treeview, rows: list, batch: int = 200, on_complete=None):
    """
    Chèn (insert) dữ liệu vào ttk.Treeview theo từng khối (chunk)
    để tránh làm đứng giao diện người dùng (UI freezing).

    Args:
        tree (ttk.Treeview): Widget Treeview để chèn dữ liệu vào.
        rows (list): Danh sách dữ liệu, mỗi phần tử là 1 dict 
                     (ví dụ: {"iid": "MA001", "values": (...)}).
        batch (int, optional): Số lượng dòng chèn mỗi lần. Mặc định là 200.
        on_complete (function, optional): Hàm callback để gọi khi hoàn tất.
    """
    # Xóa dữ liệu cũ
    tree.delete(*tree.get_children())

    total = len(rows)
    if total == 0:
        if on_complete:
            on_complete()
        return

    def insert_chunk(start=0):
        """Hàm nội bộ, chèn một khối dữ liệu"""
        end = min(start + batch, total)
        for r in rows[start:end]:
            # Xử lý dữ liệu đầu vào (thường là dict)
            if isinstance(r, dict):
                iid = r.get("id") or r.get("iid") or None
                vals = r.get("values") or r.get("vals") or tuple(r.values())
            # Xử lý dự phòng (nếu là list/tuple)
            elif isinstance(r, (list, tuple)) and len(r) == 2:
                iid, vals = r
            else:
                iid = None
                vals = r
            tree.insert("", "end", iid=iid, values=vals)
            
        # Lên lịch chèn khối tiếp theo
        if end < total:
            tree.after(10, insert_chunk, end) # 10ms delay
        else:
            # Nếu hoàn tất, gọi callback
            if on_complete:
                on_complete()

    # Bắt đầu chèn từ khối đầu tiên (start=0)
    insert_chunk(0)


class Paginator:
    """
    Một lớp (class) helper đơn giản để quản lý logic phân trang.
    (Hiện tại chưa được sử dụng, nhưng có thể dùng cho các bảng dữ liệu lớn sau này).
    """
    def __init__(self, page_size=200):
        self.page_size = page_size
        self.page = 1
        self.total = 0

    def set_total(self, total):
        self.total = total
        self.page = 1

    def pages_count(self):
        if self.total == 0: return 1
        return math.ceil(self.total / self.page_size)

    def offset(self):
        return (self.page - 1) * self.page_size

    def next(self):
        if self.page < self.pages_count():
            self.page += 1

    def prev(self):
        if self.page > 1:
            self.page -= 1