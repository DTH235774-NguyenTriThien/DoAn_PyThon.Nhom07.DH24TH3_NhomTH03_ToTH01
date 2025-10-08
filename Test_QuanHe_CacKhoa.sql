USE QL_CaPhe
GO

-- LIST TABLE 
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;

-- KIỂM TRA KHÓA NGOẠI

SELECT 
    fk.name AS FK_name,
    tp.name AS ParentTable,
    cp.name AS ParentColumn,
    tr.name AS ReferencedTable,
    cr.name AS ReferencedColumn
FROM sys.foreign_keys AS fk
INNER JOIN sys.foreign_key_columns AS fkc ON fk.object_id = fkc.constraint_object_id
INNER JOIN sys.tables AS tp ON fkc.parent_object_id = tp.object_id
INNER JOIN sys.columns AS cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
INNER JOIN sys.tables AS tr ON fkc.referenced_object_id = tr.object_id
INNER JOIN sys.columns AS cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
ORDER BY ParentTable;

-- Kiểm tra quan hệ Hóa đơn ↔ Nhân viên ↔ Khách hàng
SELECT 
    HD.MaHD,
    NV.HoTen AS NguoiLap,
    KH.TenKH AS KhachHang,
    HD.TongTien,
    HD.TrangThai
FROM dbo.HoaDon AS HD
JOIN dbo.NhanVien AS NV ON HD.MaNV = NV.MaNV
LEFT JOIN dbo.KhachHang AS KH ON HD.MaKH = KH.MaKH;
GO

-- Kiểm tra quan hệ Hóa đơn ↔ Sản phẩm
SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'HoaDon';

SELECT 
    CTHD.MaHD,
    SP.TenSP,
    CTHD.SoLuong,
    SP.DonGia,
    (CTHD.SoLuong * SP.DonGia) AS ThanhTien
FROM dbo.ChiTietHoaDon AS CTHD
JOIN dbo.SanPham AS SP ON CTHD.MaSP = SP.MaSP;
GO

-- Kiểm tra quan hệ Công thức ↔ Sản phẩm ↔ Nguyên liệu
SELECT 
    SP.TenSP,
    NL.TenNL,
    CT.SoLuong
FROM dbo.CongThuc AS CT
JOIN dbo.SanPham AS SP ON CT.MaSP = SP.MaSP
JOIN dbo.NguyenLieu AS NL ON CT.MaNL = NL.MaNL;
GO
