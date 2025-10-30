# app/utils/report_helpers.py
from app import db
from datetime import datetime

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

def get_salary_report_data() -> list[dict]:
    """
    Lấy toàn bộ dữ liệu Bảng Lương (đã JOIN).
    Trả về list[dict].
    """
    query = """
        SELECT BL.MaLuong, NV.HoTen, BL.Thang, BL.Nam, BL.TongGio, BL.LuongThucTe, BL.TrangThai
        FROM BangLuong BL
        JOIN NhanVien NV ON BL.MaNV = NV.MaNV
        ORDER BY BL.Nam DESC, BL.Thang DESC
    """
    return db.fetch_query(query)