# app/modules/employees.py
import tkinter as tk
from tkinter import ttk, messagebox

def open_window(parent):
    """Cửa sổ kiểm thử module nhân viên"""
    win = tk.Toplevel(parent)
    win.title("Quản lý nhân viên (kiểm thử)")
    win.geometry("400x250")

    label = ttk.Label(win, text="✅ Module quản lý nhân viên đã hoạt động!", font=("Arial", 12))
    label.pack(pady=50)

    btn_close = ttk.Button(win, text="Đóng", command=win.destroy)
    btn_close.pack(pady=20)
