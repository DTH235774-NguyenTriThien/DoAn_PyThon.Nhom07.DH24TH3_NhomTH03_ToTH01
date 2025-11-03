# app/modules/reports.py
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta

# Import các helper chuẩn của dự án
from app import db
from app.theme import setup_styles
from app.utils.utils import clear_window
from app.utils.treeview_helpers import fill_treeview_chunked

# Import helper báo cáo
from app.utils.report_helpers import (
    get_kpi_data, get_top_products_data, 
    get_daily_revenue_data,
    get_salary_kpi_data, 
    get_salary_pie_chart_data 
)

# Import Matplotlib
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.dates import DateFormatter
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("WARNING: Thư viện 'matplotlib' chưa được cài đặt.")
    print("Vui lòng chạy: pip install matplotlib")


def create_reports_module(parent_frame, on_back_callback):
    """Giao diện chính cho Module Báo cáo & Thống kê"""
    
    setup_styles()

    # --- Frame chính của module ---
    module_frame = tk.Frame(parent_frame, bg="#f5e6ca")
    
    # --- Header ---
    header = tk.Frame(module_frame, bg="#4b2e05", height=70)
    header.pack(fill="x")
    tk.Label(header, text="📊 BÁO CÁO & THỐNG KÊ", bg="#4b2e05", fg="white",
             font=("Segoe UI", 16, "bold")).pack(pady=12)

    # --- Thanh điều khiển (Control Frame) ---
    control_frame = tk.Frame(module_frame, bg="#f9fafb")
    control_frame.pack(fill="x", pady=10, padx=10)

    # --- Frame Nút (Bên phải) ---
    btn_frame = tk.Frame(control_frame, bg="#f9fafb")
    btn_frame.pack(side="right", anchor="n", padx=(10, 0))
    
    btn_generate = ttk.Button(btn_frame, text="✅ Tạo Báo cáo", style="Add.TButton",
                                command=lambda: generate_report())
    btn_generate.pack(side="left", padx=5)
    
    btn_back = ttk.Button(btn_frame, text="⬅ Quay lại", style="Close.TButton",
                          command=on_back_callback)
    btn_back.pack(side="left", padx=5)

    # --- Frame Lọc (Bên trái) ---
    filter_frame = tk.Frame(control_frame, bg="#f9fafb")
    filter_frame.pack(side="left", fill="x", expand=True)

    # --- Hàng 0: Chọn loại báo cáo ---
    ttk.Label(filter_frame, text="Loại Báo cáo:", background="#f9fafb",
              font=("Segoe UI", 11)).grid(row=0, column=0, padx=(5, 5), pady=5, sticky="e")
    
    report_type_var = tk.StringVar(value="Doanh thu Tổng quan")
    report_cb = ttk.Combobox(filter_frame, textvariable=report_type_var, state="readonly",
                             font=("Segoe UI", 11), width=25)
    report_cb['values'] = [
        "Doanh thu Tổng quan", 
        "Top 10 Sản phẩm Bán chạy", 
        "Báo cáo Lương Nhân viên"
    ]
    report_cb.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    # --- Hàng 1: Bộ lọc NGÀY ---
    today = datetime.now() # Dùng ngày hiện tại
    start_of_month = today.replace(day=1)

    lbl_date_start = ttk.Label(filter_frame, text="Từ ngày:", background="#f9fafb",
              font=("Segoe UI", 11))
    lbl_date_start.grid(row=1, column=0, padx=(10, 5), pady=5, sticky="e")
    
    date_start_entry = DateEntry(filter_frame, date_pattern="dd/mm/yyyy", font=("Arial", 11),
                                 background="#3e2723", foreground="white", borderwidth=2, width=12)
    date_start_entry.set_date(start_of_month)
    date_start_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    lbl_date_end = ttk.Label(filter_frame, text="Đến ngày:", background="#f9fafb",
              font=("Segoe UI", 11))
    lbl_date_end.grid(row=1, column=2, padx=(10, 5), pady=5, sticky="e")
    
    date_end_entry = DateEntry(filter_frame, date_pattern="dd/mm/yyyy", font=("Arial", 11),
                                 background="#3e2723", foreground="white", borderwidth=2, width=12)
    date_end_entry.set_date(today)
    date_end_entry.grid(row=1, column=3, padx=5, pady=5, sticky="w")

    # --- Hàng 1: Bộ lọc THÁNG/NĂM ---
    lbl_month = ttk.Label(filter_frame, text="Tháng:", background="#f9fafb",
              font=("Segoe UI", 11))
    
    month_var = tk.StringVar(value=today.month)
    cb_month = ttk.Combobox(filter_frame, textvariable=month_var, state="readonly",
                              font=("Segoe UI", 11), width=10, values=list(range(1, 13)))
    
    lbl_year = ttk.Label(filter_frame, text="Năm:", background="#f9fafb",
              font=("Segoe UI", 11))
    
    year_var = tk.StringVar(value=today.year)
    entry_year = ttk.Entry(filter_frame, textvariable=year_var, font=("Segoe UI", 11), width=10)

    # --- Hàng 2: Trạng thái ---
    status_label_var = tk.StringVar(value="")
    status_label = ttk.Label(filter_frame, textvariable=status_label_var, font=("Arial", 10, "italic"), background="#f9fafb", foreground="blue")
    status_label.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky="w")
    
    def on_report_type_changed(event=None):
        """Ẩn/Hiện các bộ lọc dựa trên loại báo cáo"""
        report_type = report_type_var.get()
        
        if report_type == "Báo cáo Lương Nhân viên":
            lbl_date_start.grid_remove()
            date_start_entry.grid_remove()
            lbl_date_end.grid_remove()
            date_end_entry.grid_remove()
            
            lbl_month.grid(row=1, column=0, padx=(10, 5), pady=5, sticky="e")
            cb_month.grid(row=1, column=1, padx=5, pady=5, sticky="w")
            lbl_year.grid(row=1, column=2, padx=(10, 5), pady=5, sticky="e")
            entry_year.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        else:
            lbl_date_start.grid(row=1, column=0, padx=(10, 5), pady=5, sticky="e")
            date_start_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
            lbl_date_end.grid(row=1, column=2, padx=(10, 5), pady=5, sticky="e")
            date_end_entry.grid(row=1, column=3, padx=5, pady=5, sticky="w")

            lbl_month.grid_remove()
            cb_month.grid_remove()
            lbl_year.grid_remove()
            entry_year.grid_remove()
            
    report_cb.bind("<<ComboboxSelected>>", on_report_type_changed)
    on_report_type_changed() 

    # --- Khung kết quả (Result Frame) ---
    result_frame = tk.Frame(module_frame, bg="#f5e6ca")
    result_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def generate_report():
        """Hàm điều hướng, gọi báo cáo tương ứng"""
        clear_window(result_frame)
        status_label_var.set("")
        
        report_type = report_type_var.get()
        
        if report_type == "Báo cáo Lương Nhân viên":
            try:
                month = int(month_var.get())
                year = int(year_var.get())
                if not (1 <= month <= 12 and year > 1900): raise ValueError
                
                _build_salary_dashboard(result_frame, status_label_var, month, year)
                
            except Exception as e:
                messagebox.showerror("Lỗi đầu vào", f"Tháng hoặc Năm không hợp lệ: {e}")
                return
        else:
            try:
                start_date = date_start_entry.get_date()
                end_date = date_end_entry.get_date() + timedelta(days=1)
            except Exception as e:
                messagebox.showerror("Lỗi ngày", "Định dạng ngày không hợp lệ.")
                return

            if report_type == "Doanh thu Tổng quan":
                _build_kpi_and_chart_report(result_frame, start_date, end_date)
            elif report_type == "Top 10 Sản phẩm Bán chạy":
                _build_top_product_chart(result_frame, status_label_var, start_date, end_date)

    # --- Báo cáo 1: KPI Cards + Biểu đồ đường (Doanh thu) ---
    def _build_kpi_and_chart_report(parent, start_date, end_date):
        clear_window(parent)
        kpi_data = get_kpi_data(start_date, end_date)
        daily_data = get_daily_revenue_data(start_date, end_date)
        if kpi_data["TongSoHoaDon"] == 0:
            ttk.Label(parent, text="Không có dữ liệu trong khoảng thời gian này.",
                      font=("Segoe UI", 14), background="#f5e6ca").pack(expand=True)
            return
            
        kpi_frame = tk.Frame(parent, bg="#f5e6ca")
        kpi_frame.pack(pady=10, fill="x", anchor="n")
        style = ttk.Style()
        style.configure("KPI.TFrame", background="#f9fafb", relief="solid", borderwidth=1)
        style.configure("KPI.Title.TLabel", background="#f9fafb", foreground="#4b2e05", font=("Segoe UI", 14, "bold"))
        style.configure("KPI.Value.TLabel", background="#f9fafb", foreground="#a47148", font=("Segoe UI", 28, "bold"))
        
        card1 = ttk.Frame(kpi_frame, style="KPI.TFrame", padding=20)
        card1.pack(side="left", padx=10, fill="x", expand=True)
        ttk.Label(card1, text="TỔNG DOANH THU", style="KPI.Title.TLabel").pack()
        ttk.Label(card1, text=f"{int(kpi_data['TongDoanhThu']):,} đ", style="KPI.Value.TLabel").pack(pady=5)
        
        card2 = ttk.Frame(kpi_frame, style="KPI.TFrame", padding=20)
        card2.pack(side="left", padx=10, fill="x", expand=True)
        ttk.Label(card2, text="TỔNG SỐ HÓA ĐƠN", style="KPI.Title.TLabel").pack()
        ttk.Label(card2, text=f"{kpi_data['TongSoHoaDon']}", style="KPI.Value.TLabel").pack(pady=5)
        
        card3 = ttk.Frame(kpi_frame, style="KPI.TFrame", padding=20)
        card3.pack(side="left", padx=10, fill="x", expand=True)
        ttk.Label(card3, text="TRUNG BÌNH / HÓA ĐƠN", style="KPI.Title.TLabel").pack()
        ttk.Label(card3, text=f"{int(kpi_data['TrungBinhMoiHD']):,} đ", style="KPI.Value.TLabel").pack(pady=5)
        
        if not MATPLOTLIB_AVAILABLE:
            ttk.Label(parent, text="Lỗi: Vui lòng cài đặt 'matplotlib' để xem biểu đồ.",
                      font=("Segoe UI", 12), background="#f5e6ca", foreground="red").pack(expand=True)
            return
        if not daily_data: return
        
        chart_frame = tk.Frame(parent, bg="#f9fafb", relief="solid", borderwidth=1)
        chart_frame.pack(fill="both", expand=True, pady=(10, 0))
        fig, ax = plt.subplots(figsize=(10, 4), dpi=100)
        fig.set_facecolor('#f9fafb')
        ax.set_facecolor('#f5e6ca')
        ax.tick_params(colors='#4b2e05')
        ax.spines['top'].set_color('none')
        ax.spines['right'].set_color('none')
        ax.spines['left'].set_color('#4b2e05')
        ax.spines['bottom'].set_color('#4b2e05')
        ax.plot( [r['Ngay'] for r in daily_data], [r['DoanhThuNgay'] for r in daily_data], 
               marker='o', linestyle='-', color='#a47148', linewidth=2)
        ax.set_title("Doanh thu theo Ngày", color="#4b2e05", fontdict={'fontsize': 14, 'fontweight': 'bold'})
        ax.set_ylabel("Doanh thu (VNĐ)", color="#4b2e05")
        ax.xaxis.set_major_formatter(DateFormatter('%d/%m'))
        fig.autofmt_xdate()
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # --- Báo cáo 2: Biểu đồ cột ngang (Top Sản phẩm) ---
    def _build_top_product_chart(parent, status_var, start_date, end_date):
        status_var.set("Đang tải...")
        parent.update_idletasks()
        if not MATPLOTLIB_AVAILABLE:
            ttk.Label(parent, text="Lỗi: Vui lòng cài đặt 'matplotlib' để xem biểu đồ.",
                      font=("Segoe UI", 12), background="#f5e6ca", foreground="red").pack(expand=True)
            return
        try:
            rows = get_top_products_data(start_date, end_date)
            if not rows:
                ttk.Label(parent, text="Không có dữ liệu sản phẩm trong khoảng thời gian này.",
                            font=("Segoe UI", 14), background="#f5e6ca").pack(expand=True)
                return
                
            products = [r["TenSP"] for r in reversed(rows)]
            quantities = [r["TongSoLuong"] for r in reversed(rows)]
            fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
            fig.set_facecolor('#f5e6ca')
            ax.set_facecolor('#f5e6ca')
            text_color = '#4b2e05'
            bar_color = '#a47148'
            ax.tick_params(colors=text_color)
            ax.spines['top'].set_color('none')
            ax.spines['right'].set_color('none')
            ax.spines['left'].set_color(text_color)
            ax.spines['bottom'].set_color(text_color)
            bars = ax.barh(products, quantities, color=bar_color, height=0.6)
            for bar in bars:
                ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                        f'{bar.get_width()}', va='center', color=text_color, fontweight='bold')
            ax.set_title("Top Sản phẩm Bán chạy", color=text_color, fontdict={'fontsize': 16, 'fontweight': 'bold'})
            ax.set_xlabel("Tổng Số Lượng Bán", color=text_color)
            plt.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            status_var.set(f"Đã tải {len(rows)} sản phẩm.")
            
        except Exception as e:
            status_var.set("Lỗi!")
            messagebox.showerror("Lỗi SQL", f"Không thể lấy báo cáo sản phẩm: {e}")

    # --- Báo cáo 3: Dashboard Lương (KPIs + Pie Chart) ---
    def _build_salary_dashboard(parent, status_var, month, year):
        status_var.set("Đang tải...")
        parent.update_idletasks()

        if not MATPLOTLIB_AVAILABLE:
            ttk.Label(parent, text="Lỗi: Vui lòng cài đặt 'matplotlib' để xem biểu đồ.",
                      font=("Segoe UI", 12), background="#f5e6ca", foreground="red").pack(expand=True)
            return
        
        try:
            kpi_data = get_salary_kpi_data(month, year)
            pie_data = get_salary_pie_chart_data(month, year)

            if kpi_data["TongGioLam"] == 0:
                ttk.Label(parent, text=f"Không có dữ liệu lương cho tháng {month}/{year}.",
                            font=("Segoe UI", 14), background="#f5e6ca").pack(expand=True)
                status_var.set("Không có dữ liệu.")
                return

            kpi_frame = tk.Frame(parent, bg="#f5e6ca")
            kpi_frame.pack(pady=10, fill="x", anchor="n")
            
            style = ttk.Style()
            style.configure("KPI.TFrame", background="#f9fafb", relief="solid", borderwidth=1)
            style.configure("KPI.Title.TLabel", background="#f9fafb", foreground="#4b2e05", font=("Segoe UI", 14, "bold"))
            style.configure("KPI.Value.TLabel", background="#f9fafb", foreground="#a47148", font=("Segoe UI", 28, "bold"))

            card1 = ttk.Frame(kpi_frame, style="KPI.TFrame", padding=20)
            card1.pack(side="left", padx=10, fill="x", expand=True)
            ttk.Label(card1, text="TỔNG LƯƠNG ĐÃ TRẢ", style="KPI.Title.TLabel").pack()
            ttk.Label(card1, text=f"{int(kpi_data['TongLuongDaTra']):,} đ", style="KPI.Value.TLabel").pack(pady=5)

            card2 = ttk.Frame(kpi_frame, style="KPI.TFrame", padding=20)
            card2.pack(side="left", padx=10, fill="x", expand=True)
            ttk.Label(card2, text="TỔNG GIỜ CÔNG", style="KPI.Title.TLabel").pack()
            ttk.Label(card2, text=f"{kpi_data['TongGioLam']:.1f} giờ", style="KPI.Value.TLabel").pack(pady=5)
            
            card3 = ttk.Frame(kpi_frame, style="KPI.TFrame", padding=20)
            card3.pack(side="left", padx=10, fill="x", expand=True)
            ttk.Label(card3, text="LƯƠNG TB / GIỜ", style="KPI.Title.TLabel").pack()
            ttk.Label(card3, text=f"{int(kpi_data['LuongTBGio']):,} đ", style="KPI.Value.TLabel").pack(pady=5)
            
            if not pie_data:
                status_var.set("Đã tải KPI.")
                return 

            chart_frame = tk.Frame(parent, bg="#f9fafb", relief="solid", borderwidth=1)
            chart_frame.pack(fill="both", expand=True, pady=(10, 0))

            labels = [r['ChucVu'] for r in pie_data]
            sizes = [r['LuongTheoChucVu'] for r in pie_data]
            
            theme_colors = ['#a47148', '#c75c5c', '#8b5e34', '#f5e6ca', '#d7ccc8']
            
            fig, ax = plt.subplots(figsize=(10, 4), dpi=100)
            fig.set_facecolor('#f9fafb') 

            wedges, texts, autotexts = ax.pie(
                sizes, 
                autopct='%1.1f%%', 
                startangle=90,
                colors=theme_colors,
                pctdistance=0.85 
            )
            
            centre_circle = plt.Circle((0,0), 0.70, fc='#f9fafb')
            fig.gca().add_artist(centre_circle)
            
            plt.setp(texts, color='#4b2e05', fontweight='bold')
            plt.setp(autotexts, color='white', fontweight='bold')

            ax.axis('equal')  
            ax.set_title(f"Phân bổ Quỹ lương (Tháng {month}/{year})", color="#4b2e05", fontdict={'fontsize': 16, 'fontweight': 'bold'})
            
            ax.legend(wedges, labels,
                      title="Chức vụ",
                      loc="center left",
                      bbox_to_anchor=(1, 0, 0.5, 1),
                      facecolor="#f9fafb",
                      edgecolor="#f9fafb",
                      labelcolor="#4b2e05"
                     )

            plt.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

            status_var.set(f"Đã tải báo cáo lương T{month}/{year}.")

        except Exception as e:
            status_var.set("Lỗi!")
            messagebox.showerror("Lỗi SQL", f"Không thể lấy báo cáo lương: {e}")

    
    # --- Tải báo cáo mặc định khi mở ---
    generate_report()
    
    return module_frame