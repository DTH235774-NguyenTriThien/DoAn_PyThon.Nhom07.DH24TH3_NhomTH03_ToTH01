# app/utils/report_helpers.py
from app import db
from datetime import datetime
import win32print  # Thư viện pywin32
from app.db import fetch_query,execute_scalar # (Đảm bảo đã import)

def get_kpi_data(start_date: datetime, end_date: datetime) -> dict:
    """
    Lấy dữ liệu KPI tổng quan (Doanh thu, SL Hóa đơn, TB Hóa đơn).
    Trả về một dict duy nhất.
    """
    query = """
        SELECT
            COUNT(MaHD) AS TongSoHoaDon,
            ISNULL(SUM(TongTien), 0) AS TongDoanhThu,
            ISNULL(AVG(TongTien), 0) AS TrungBinhMoiHD
        FROM HoaDon
        WHERE TrangThai = N'Đã thanh toán'
          AND NgayLap >= ? AND NgayLap < ?
    """
    result = db.fetch_query(query, (start_date, end_date))
    
    if not result:
        # Trả về dict rỗng để UI tự xử lý
        return {"TongSoHoaDon": 0, "TongDoanhThu": 0, "TrungBinhMoiHD": 0}
    
    return result[0] # fetch_query trả về list[dict], ta lấy phần tử đầu tiên

def get_daily_revenue_data(start_date: datetime, end_date: datetime) -> list[dict]:
    """
    Lấy doanh thu theo từng ngày (để vẽ biểu đồ đường).
    Trả về list[dict] gồm 'Ngay' và 'DoanhThuNgay'.
    """
    query = """
        SELECT
            CAST(NgayLap AS DATE) AS Ngay,
            SUM(TongTien) AS DoanhThuNgay
        FROM HoaDon
        WHERE TrangThai = N'Đã thanh toán'
          AND NgayLap >= ? AND NgayLap < ?
        GROUP BY CAST(NgayLap AS DATE)
        ORDER BY Ngay
    """
    return db.fetch_query(query, (start_date, end_date))

def get_top_products_data(start_date: datetime, end_date: datetime) -> list[dict]:
    """
    Lấy Top 10 sản phẩm bán chạy nhất.
    Trả về list[dict].
    """
    query = """
        SELECT TOP 10
            p.TenSP,
            SUM(ct.SoLuong) AS TongSoLuong
        FROM ChiTietHoaDon ct
        JOIN SanPham p ON ct.MaSP = p.MaSP
        JOIN HoaDon h ON ct.MaHD = h.MaHD
        WHERE h.TrangThai = N'Đã thanh toán'
          AND h.NgayLap >= ? AND h.NgayLap < ?
        GROUP BY p.TenSP
        ORDER BY TongSoLuong DESC
    """
    return db.fetch_query(query, (start_date, end_date))

# =========================================================
# SỬA 1: THÊM CÁC HÀM HELPER MỚI CHO BÁO CÁO LƯƠNG
# =========================================================

def get_salary_kpi_data(month: int, year: int) -> dict:
    """
    Lấy dữ liệu KPI Lương (Tổng chi, Tổng giờ) theo Tháng/Năm.
    """
    query = """
        SELECT
            ISNULL(SUM(CASE WHEN TrangThai = N'Đã trả' THEN LuongThucTe ELSE 0 END), 0) AS TongLuongDaTra,
            ISNULL(SUM(TongGio), 0) AS TongGioLam
        FROM BangLuong
        WHERE Thang = ? AND Nam = ?
    """
    result = db.fetch_query(query, (month, year))
    
    if not result:
        return {"TongLuongDaTra": 0, "TongGioLam": 0, "LuongTBGio": 0}
    
    kpi_data = result[0]
    
    # Tính KPI thứ 3 (Lương TB/Giờ)
    if kpi_data["TongGioLam"] > 0:
        kpi_data["LuongTBGio"] = kpi_data["TongLuongDaTra"] / kpi_data["TongGioLam"]
    else:
        kpi_data["LuongTBGio"] = 0
        
    return kpi_data

def get_salary_pie_chart_data(month: int, year: int) -> list[dict]:
    """
    Lấy dữ liệu phân bổ lương theo Chức vụ (cho biểu đồ tròn).
    """
    query = """
        SELECT
            nv.ChucVu,
            ISNULL(SUM(bl.LuongThucTe), 0) AS LuongTheoChucVu
        FROM BangLuong bl
        JOIN NhanVien nv ON bl.MaNV = nv.MaNV
        WHERE bl.Thang = ? AND bl.Nam = ?
        GROUP BY nv.ChucVu
        HAVING SUM(bl.LuongThucTe) > 0 -- Chỉ lấy các nhóm có lương
    """
    return db.fetch_query(query, (month, year))

# =========================================================
# HELPER IN HÓA ĐƠN (POS)
# =========================================================

def _send_text_to_printer(text_content):
    """
    Hàm cấp thấp: Gửi một chuỗi text thô đến máy in mặc định.
    (Dùng cho máy in bill/in nhiệt)
    """
    try:
        # 1. Lấy tên máy in mặc định
        printer_name = win32print.GetDefaultPrinter()
        
        # 2. Mở kết nối đến máy in
        hPrinter = win32print.OpenPrinter(printer_name)
        
        try:
            # 3. Bắt đầu một "tài liệu" (document) in
            hJob = win32print.StartDocPrinter(hPrinter, 1, ("POS Receipt", None, "RAW"))
            if hJob > 0:
                try:
                    # 4. Bắt đầu một trang
                    win32print.StartPagePrinter(hPrinter)
                    
                    # 5. Ghi dữ liệu (đã encode sang utf-8)
                    win32print.WritePrinter(hPrinter, text_content.encode('utf-8'))
                    
                    # 6. Kết thúc trang và tài liệu
                    win32print.EndPagePrinter(hPrinter)
                finally:
                    win32print.EndDocPrinter(hPrinter)
            else:
                raise Exception("Không thể bắt đầu tác vụ in (StartDocPrinter).")
        finally:
            # 7. Đóng kết nối máy in (rất quan trọng)
            win32print.ClosePrinter(hPrinter)
            
    except Exception as e:
        print(f"Lỗi máy in: {e}")
        # Ném lỗi lên để `pos.py` có thể bắt và hiển thị
        raise Exception(f"Lỗi máy in: {e}\nĐảm bảo máy in đã được cài đặt và là 'Default'.")


def _generate_receipt_text(mahd, hoa_don_data, chi_tiet_data, khach_hang_data):
    """
    Tạo nội dung text thô cho hóa đơn (định dạng cho máy in bill 40 ký tự).
    """
    
    # --- Thông tin Quán (Bạn có thể sửa) ---
    shop_name = "QUAN CA PHE ANHKH"
    address = "123 Duong ABC, Phuong XYZ, Q.1, TP.HCM"
    phone = "Hotline: 0909.123.456"

    # --- Căn giữa Tiêu đề ---
    receipt = f"{shop_name:^40}\n"
    receipt += f"{address:^40}\n"
    receipt += f"{phone:^40}\n"
    receipt += "="*40 + "\n"
    receipt += f"{'HOA DON BAN LE':^40}\n"
    
    # --- Thông tin Hóa đơn ---
    hd = hoa_don_data
    now = hd.get('NgayLap', datetime.now()).strftime("%d/%m/%Y %H:%M")
    receipt += f"So HD: {mahd.ljust(20)} Ngay: {now}\n"
    receipt += f"Thu ngan: {str(hd.get('MaNV', 'N/A')).ljust(30)}\n"
    
    if khach_hang_data:
        receipt += f"Khach hang: {khach_hang_data.get('TenKH', 'N/A')}\n"
        receipt += f"Diem dung: {hd.get('DiemSuDung', 0)}\n"
    
    receipt += "-"*40 + "\n"
    
    # --- Chi tiết Món hàng (Căn lề) ---
    # Định dạng: Tên (18) | SL (3) | ĐG (8) | TT (9)
    receipt += "TEN MON           SL    DON GIA   T.TIEN\n"
    receipt += "-"*40 + "\n"
    
    for item in chi_tiet_data:
        # Lấy tên, cắt ngắn nếu quá dài (15 ký tự)
        ten_sp = str(item.get('TenSP', 'N/A'))
        if len(ten_sp) > 15:
            ten_sp = ten_sp[:15] + "."
        
        sl = str(item.get('SoLuong', 0))
        don_gia = int(item.get('DonGia', 0))
        thanh_tien = int(sl) * don_gia
        
        # Căn lề
        line = f"{ten_sp:<16} {sl:>3} {don_gia:>{8},} {thanh_tien:>{10},}\n"
        receipt += line

    # --- Tổng tiền ---
    receipt += "-"*40 + "\n"
    tong_cong_str = f"{int(hd.get('TongTien', 0)):,} d"
    giam_gia_str = f"{int(hd.get('GiamGia', 0)):,} d"
    thanh_toan_str = f"{int(hd.get('ThanhTien', 0)):,} d"
    
    receipt += f"{'Tong cong:':<12}{tong_cong_str:>{28}}\n"
    receipt += f"{'Giam gia (diem):':<12}{giam_gia_str:>{28}}\n"
    
    receipt += "-"*40 + "\n"
    receipt += f"{'KHACH CAN TRA:':<12}{thanh_toan_str:>{28}}\n"
    receipt += "-"*40 + "\n"

    # --- Lời cảm ơn ---
    receipt += f"{'Cam on quy khach! Hen gap lai!':^40}\n\n\n" # Thêm 3 dòng trống để đẩy giấy
    
    return receipt

def print_pos_receipt(mahd):
    """
    Hàm cấp cao: Lấy dữ liệu, tạo text, và gọi hàm in.
    """
    try:
        # 1. Lấy thông tin Hóa đơn
        hd_data = fetch_query("SELECT * FROM HoaDon WHERE MaHD = ?", (mahd,))
        if not hd_data:
            raise Exception(f"Không tìm thấy Hóa đơn {mahd}.")
        
        # 2. Lấy thông tin Chi tiết Hóa đơn
        cthd_data = fetch_query("""
            SELECT cthd.SoLuong, cthd.DonGia, sp.TenSP 
            FROM ChiTietHoaDon cthd
            JOIN SanPham sp ON cthd.MaSP = sp.MaSP
            WHERE cthd.MaHD = ?
        """, (mahd,))
        if not cthd_data:
            raise Exception(f"Không tìm thấy Chi tiết Hóa đơn cho {mahd}.")
        
        # 3. Lấy thông tin Khách hàng (nếu có)
        kh_data = None
        if hd_data[0].get('MaKH'):
            kh_result = fetch_query("SELECT TenKH FROM KhachHang WHERE MaKH = ?", (hd_data[0]['MaKH'],))
            if kh_result:
                kh_data = kh_result[0]
        
        # 4. Tạo nội dung text
        receipt_text = _generate_receipt_text(mahd, hd_data[0], cthd_data, kh_data)
        
        # 5. Gửi đến máy in
        _send_text_to_printer(receipt_text)
        
        return True
    
    except Exception as e:
        # Ném lỗi lên để pos.py hiển thị
        raise e
    
# =========================================================
# HELPER CHO DASHBOARD (MỚI)
# =========================================================
def get_dashboard_kpis():
    """
    Lấy 3 chỉ số KPI chính cho Dashboard (HÔM NAY).
    1. Tổng doanh thu (chỉ các hóa đơn 'Đã thanh toán')
    2. Tổng số đơn hàng (chỉ các hóa đơn 'Đã thanh toán')
    3. Số sản phẩm (KHÔNG PHẢI NGUYÊN LIỆU) ở trạng thái 'Hết hàng'
    """
    data = {
        "DoanhThuHomNay": 0,
        "DonHangHomNay": 0,
        "SPHetHang": 0
    }
    
    # Lấy ngày hôm nay (an toàn cho SQL)
    today_date = datetime.now().date()
    
    try:
        # 1 & 2. Lấy Doanh thu và Số đơn hàng
        query_revenue = """
            SELECT 
                SUM(ThanhTien) AS TongDoanhThu,
                COUNT(MaHD) AS TongDonHang
            FROM HoaDon
            WHERE TrangThai = N'Đã thanh toán'
              AND CONVERT(date, NgayLap) = ?
        """
        result_revenue = fetch_query(query_revenue, (today_date,))
        
        if result_revenue:
            data["DoanhThuHomNay"] = result_revenue[0].get("TongDoanhThu") or 0
            data["DonHangHomNay"] = result_revenue[0].get("TongDonHang") or 0

        # 3. Lấy Số sản phẩm hết hàng
        query_stock = """
            SELECT COUNT(MaSP) 
            FROM SanPham 
            WHERE TrangThai = N'Hết hàng'
        """
        data["SPHetHang"] = execute_scalar(query_stock) or 0
        
        return data

    except Exception as e:
        print(f"Lỗi khi lấy KPI Dashboard: {e}")
        return data # Trả về 0 nếu có lỗi