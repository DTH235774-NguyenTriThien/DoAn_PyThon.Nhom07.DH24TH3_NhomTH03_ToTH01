import tkinter as tk
from tkinter import ttk

def build_tab(parent):
    """Tab Ca làm việc - tạm thời"""
    label = ttk.Label(
        parent,
        text="🕐 Tab Ca làm việc (đang phát triển)",
        font=("Segoe UI", 14, "bold"),
        foreground="#3e2723"
    )
    label.pack(pady=30)
