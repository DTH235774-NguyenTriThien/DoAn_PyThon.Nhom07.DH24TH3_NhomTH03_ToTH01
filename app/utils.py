# app/utils.py
"""
Hàm tiện ích dùng chung trong app.
"""

def clear_window(root):
    """Xóa mọi widget con của root (dọn màn hình để hiển thị frame mới)."""
    for widget in root.winfo_children():
        widget.destroy()
