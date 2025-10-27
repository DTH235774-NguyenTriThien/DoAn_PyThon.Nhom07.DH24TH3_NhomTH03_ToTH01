import tkinter as tk
from tkinter import ttk

def build_tab(parent, root=None, username=None, role=None):
    """Tab Bảng lương - tạm thời"""
    label = ttk.Label(
        parent,
        text="💰 Tab Bảng lương (đang phát triển)",
        font=("Segoe UI", 14, "bold"),
        foreground="#3e2723"
    )
    label.pack(pady=30)
