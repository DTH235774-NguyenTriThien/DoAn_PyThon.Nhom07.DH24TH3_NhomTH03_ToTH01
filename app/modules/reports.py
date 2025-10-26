# app/modules/statistics.py
import tkinter as tk
from tkinter import ttk, messagebox
from app import db
from app.utils.utils import clear_window, go_back, center_window
from app.theme import setup_styles
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def show_statistics_module(root, username=None, role=None):
    """Giao diện thống kê tổng hợp"""
    clear_window(root)
    setup_styles()

    root.title("📊 Thống kê")
    root.configure(bg="#f5e6ca")

    # ====== CẤU HÌNH FORM CHÍNH ======
    center_window(root, 1200, 700, offset_y=-60)
    root.minsize(1000, 550)


    # Header
    header = tk.Frame(root, bg="#4b2e05", height=70)
    header.pack(fill="x")
    tk.Label(header, text="📊 THỐNG KÊ HOẠT ĐỘNG", bg="#4b2e05", fg="white",
             font=("Segoe UI", 18, "bold")).pack(pady=15)

    # Tổng quan số liệu
    summary_frame = tk.Frame(root, bg="#f5e6ca")
    summary_frame.pack(fill="x", padx=20, pady=10)

    # Thống kê nhanh
    total_revenue = get_total_revenue()
    total_invoices = get_total_invoices()
    total_customers = get_total_customers()
    total_employees = get_total_employees()

    infos = [
        ("💰 Tổng doanh thu", f"{total_revenue:,.0f} VNĐ"),
        ("🧾 Tổng hóa đơn", total_invoices),
        ("👥 Tổng khách hàng", total_customers),
        ("👨‍💼 Tổng nhân viên", total_employees)
    ]

    for i, (label, value) in enumerate(infos):
        card = tk.Frame(summary_frame, bg="#fff", bd=2, relief="groove")
        card.grid(row=0, column=i, padx=10, pady=10, ipadx=20, ipady=10, sticky="nsew")
        tk.Label(card, text=label, bg="#fff", font=("Segoe UI", 12, "bold")).pack()
        tk.Label(card, text=value, bg="#fff", font=("Segoe UI", 14)).pack()

    summary_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

    # Biểu đồ
    chart_frame = tk.Frame(root, bg="#f8f9fa")
    chart_frame.pack(fill="both", expand=True, padx=20, pady=20)

    ttk.Button(chart_frame, text="⬅ Quay lại", style="Close.TButton",
               command=lambda: go_back(root, username, role)).pack(anchor="e", pady=5)

    show_revenue_chart(chart_frame)
    show_top_products_chart(chart_frame)

def get_total_revenue():
    try:
        db.cursor.execute("SELECT SUM(TongTien) FROM HoaDon")
        result = db.cursor.fetchone()[0]
        return result or 0
    except Exception as e:
        print("Error:", e)
        return 0

def get_total_invoices():
    db.cursor.execute("SELECT COUNT(*) FROM HoaDon")
    return db.cursor.fetchone()[0]

def get_total_customers():
    db.cursor.execute("SELECT COUNT(*) FROM KhachHang")
    return db.cursor.fetchone()[0]

def get_total_employees():
    db.cursor.execute("SELECT COUNT(*) FROM NhanVien")
    return db.cursor.fetchone()[0]

def show_revenue_chart(parent):
    """Biểu đồ doanh thu theo tháng"""
    db.cursor.execute("""
        SELECT MONTH(NgayLap) AS Thang, SUM(TongTien) AS DoanhThu
        FROM HoaDon
        GROUP BY MONTH(NgayLap)
        ORDER BY Thang
    """)
    rows = db.cursor.fetchall()
    months = [r.Thang for r in rows]
    revenues = [r.DoanhThu for r in rows]

    fig = Figure(figsize=(6, 4), dpi=100)
    ax = fig.add_subplot(111)
    ax.bar(months, revenues)
    ax.set_title("Doanh thu theo tháng")
    ax.set_xlabel("Tháng")
    ax.set_ylabel("VNĐ")

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.get_tk_widget().pack(side="left", fill="both", expand=True)
    canvas.draw()

def show_top_products_chart(parent):
    """Top 5 sản phẩm bán chạy"""
    db.cursor.execute("""
        SELECT TOP 5 SP.TenSP, SUM(CT.SoLuong) AS TongSL
        FROM ChiTietHoaDon CT
        JOIN SanPham SP ON CT.MaSP = SP.MaSP
        GROUP BY SP.TenSP
        ORDER BY TongSL DESC
    """)
    rows = db.cursor.fetchall()
    products = [r.TenSP for r in rows]
    counts = [r.TongSL for r in rows]

    fig = Figure(figsize=(6, 4), dpi=100)
    ax = fig.add_subplot(111)
    ax.pie(counts, labels=products, autopct="%1.1f%%", startangle=90)
    ax.set_title("Top 5 sản phẩm bán chạy")

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.get_tk_widget().pack(side="right", fill="both", expand=True)
    canvas.draw()
