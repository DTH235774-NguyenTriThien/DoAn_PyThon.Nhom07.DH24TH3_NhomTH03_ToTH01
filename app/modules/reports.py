# app/modules/reports.py
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta

# Import các helper chuẩn của dự án
from app import db
from app.theme import setup_styles
from app.utils.utils import clear_window, go_back, center_window
from app.utils.treeview_helpers import fill_treeview_chunked
from app.utils.report_helpers import (
    get_kpi_data, get_top_products_data, get_salary_report_data, 
    get_daily_revenue_data
)

# Import Matplotlib (Đã có)
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.dates import DateFormatter
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("WARNING: Thư viện 'matplotlib' chưa được cài đặt.")
    print("Vui lòng chạy: pip install matplotlib")


# --- HÀM CHÍNH HIỂN THỊ MODULE ---
def show_reports_module(root, username=None, role=None):
    """Giao diện chính cho Module Báo cáo & Thống kê"""
    clear_window(root)
    setup_styles()
    root.title("📊 BÁO CÁO & THỐNG KÊ")
    root.configure(bg="#f5e6ca")

    center_window(root, 1200, 700, offset_y=-60)
    root.minsize(1000, 600)

    # --- Header ---
    header = tk.Frame(root, bg="#4b2e05", height=70)
    header.pack(fill="x")
    tk.Label(header, text="📊 BÁO CÁO & THỐNG KÊ", bg="#4b2e05", fg="white",
             font=("Segoe UI", 16, "bold")).pack(pady=12)

    # --- Thanh điều khiển (Control Frame) ---
    # (Đã tái cấu trúc với bộ lọc động)
    control_frame = tk.Frame(root, bg="#f9fafb")
    control_frame.pack(fill="x", pady=10, padx=10)

    btn_frame = tk.Frame(control_frame, bg="#f9fafb")
    btn_frame.pack(side="right", anchor="n", padx=(10, 0))
    btn_generate = ttk.Button(btn_frame, text="✅ Tạo Báo cáo", style="Add.TButton",
                              command=lambda: generate_report())
    btn_generate.pack(side="left", padx=5)
    btn_back = ttk.Button(btn_frame, text="⬅ Quay lại", style="Close.TButton",
                          command=lambda: go_back(root, username, role))
    btn_back.pack(side="left", padx=5)

    filter_frame = tk.Frame(control_frame, bg="#f9fafb")
    filter_frame.pack(side="left", fill="x", expand=True)

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

    today = datetime(2025, 10, 30) 
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

    lbl_month = ttk.Label(filter_frame, text="Tháng:", background="#f9fafb",
              font=("Segoe UI", 11))
    month_var = tk.StringVar(value=today.month)
    cb_month = ttk.Combobox(filter_frame, textvariable=month_var, state="readonly",
                             font=("Segoe UI", 11), width=10, values=list(range(1, 13)))
    lbl_year = ttk.Label(filter_frame, text="Năm:", background="#f9fafb",
              font=("Segoe UI", 11))
    year_var = tk.StringVar(value=today.year)
    entry_year = ttk.Entry(filter_frame, textvariable=year_var, font=("Segoe UI", 11), width=10)

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
    result_frame = tk.Frame(root, bg="#f5e6ca")
    result_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # --- LOGIC CÁC HÀM BÁO CÁO (ĐÃ REFACTOR) ---
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
                tree = ttk.Treeview(result_frame, show="headings", height=20)
                tree.pack(fill="both", expand=True)
                _build_salary_report(tree, status_label_var, month, year)
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
                # SỬA 1: Bỏ TreeView, gọi hàm biểu đồ cột
                _build_top_product_chart(result_frame, status_label_var, start_date, end_date)

    # --- Báo cáo 1: KPI Cards + Biểu đồ đường (Doanh thu) ---
    def _build_kpi_and_chart_report(parent, start_date, end_date):
        # (Hàm này giữ nguyên như cũ)
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

    # =========================================================
    # SỬA 2: NÂNG CẤP BÁO CÁO 2 (BIỂU ĐỒ CỘT NGANG)
    # =========================================================
    def _build_top_product_chart(parent, status_var, start_date, end_date):
        """Vẽ Biểu đồ cột ngang (Bar Chart) cho Top 10 Sản phẩm"""
        status_var.set("Đang tải...")
        parent.update_idletasks()

        if not MATPLOTLIB_AVAILABLE:
            ttk.Label(parent, text="Lỗi: Vui lòng cài đặt 'matplotlib' để xem biểu đồ.",
                      font=("Segoe UI", 12), background="#f5e6ca", foreground="red").pack(expand=True)
            return
        
        try:
            # 1. Lấy dữ liệu
            rows = get_top_products_data(start_date, end_date)
            
            if not rows:
                ttk.Label(parent, text="Không có dữ liệu sản phẩm trong khoảng thời gian này.",
                          font=("Segoe UI", 14), background="#f5e6ca").pack(expand=True)
                return

            # 2. Chuẩn bị dữ liệu (đảo ngược để vẽ)
            # Matplotlib vẽ từ dưới lên, nên ta cần đảo ngược list
            products = [r["TenSP"] for r in reversed(rows)]
            quantities = [r["TongSoLuong"] for r in reversed(rows)]
            
            # 3. Tạo Figure và Axis (bảng vẽ)
            fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
            
            # ---- Đồng bộ màu sắc (Rất quan trọng) ----
            fig.set_facecolor('#f5e6ca')    # Nền ngoài (màu nền chính)
            ax.set_facecolor('#f5e6ca')   # Nền trong
            text_color = '#4b2e05'        # Nâu đậm
            bar_color = '#a47148'         # Nâu vừa (màu nút)
            
            ax.tick_params(colors=text_color)
            ax.spines['top'].set_color('none')
            ax.spines['right'].set_color('none')
            ax.spines['left'].set_color(text_color)
            ax.spines['bottom'].set_color(text_color)
            # -----------------------------------------

            # 4. Vẽ biểu đồ cột ngang (barh)
            bars = ax.barh(products, quantities, color=bar_color, height=0.6)
            
            # 5. Thêm nhãn (label) số lượng trên đầu mỗi cột
            for bar in bars:
                ax.text(bar.get_width() + 0.1, # Vị trí X (cách 0.1)
                        bar.get_y() + bar.get_height()/2, # Vị trí Y (giữa cột)
                        f'{bar.get_width()}', # Văn bản
                        va='center', 
                        color=text_color,
                        fontweight='bold')
            
            # 6. Định dạng
            ax.set_title("Top Sản phẩm Bán chạy", color=text_color, fontdict={'fontsize': 16, 'fontweight': 'bold'})
            ax.set_xlabel("Tổng Số Lượng Bán", color=text_color)
            plt.tight_layout()

            # 7. Nhúng biểu đồ vào Tkinter
            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            
            status_var.set(f"Đã tải {len(rows)} sản phẩm.")

        except Exception as e:
            status_var.set("Lỗi!")
            messagebox.showerror("Lỗi SQL", f"Không thể lấy báo cáo sản phẩm: {e}")

    # --- Báo cáo 3: Báo cáo Lương (TreeView) ---
    # (Hàm này giữ nguyên như cũ, chỉ đổi tham số)
    def _build_salary_report(tree_widget, status_var, month, year):
        status_var.set("Đang tải...")
        tree_widget.update_idletasks()
        
        cols = ["MaLuong", "HoTen", "Thang", "Nam", "TongGio", "LuongThucTe", "TrangThai"]
        headers = {
            "MaLuong": "Mã Lương", "HoTen": "Họ tên", "Thang": "Tháng", "Nam": "Năm",
            "TongGio": "Tổng Giờ", "LuongThucTe": "Lương (VNĐ)", "TrangThai": "Trạng thái"
        }
        tree_widget.configure(columns=cols, show="headings")
        for c, h in headers.items():
            tree_widget.heading(c, text=h)
            tree_widget.column(c, anchor="center", width=150)
        
        try:
            rows = get_salary_report_data(month, year) # Dùng tham số mới
            tree_data = []
            if not rows:
                 status_var.set(f"Không có dữ liệu lương cho {month}/{year}.")
                 
            for r in rows:
                tong_gio_f = f"{r['TongGio']:.1f}" if r['TongGio'] is not None else "0.0"
                luong_f = f"{r['LuongThucTe']:,.0f}" if r['LuongThucTe'] is not None else "0"
                values_tuple = (
                    r['MaLuong'], r['HoTen'], r['Thang'], r['Nam'],
                    tong_gio_f, luong_f, r['TrangThai']
                )
                tree_data.append({"iid": r['MaLuong'], "values": values_tuple})
            
            fill_treeview_chunked(
                tree_widget, 
                tree_data, 
                on_complete=lambda: status_var.set(f"Đã tải {len(rows)} bản ghi lương.")
            )
        except Exception as e:
            status_var.set("Lỗi!")
            messagebox.showerror("Lỗi SQL", f"Không thể lấy báo cáo lương: {e}")

    # --- Tải báo cáo mặc định khi mở ---
    generate_report()