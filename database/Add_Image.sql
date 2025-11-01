SELECT * FROM NguyenLieu
SELECT * FROM KhachHang
SELECT * from HoaDon
select * from ChiTietHoaDon
select * from congthuc
select * from SanPham	

-- 1. Thêm cột mới để lưu đường dẫn ảnh
ALTER TABLE SanPham
ADD ImagePath NVARCHAR(255) NULL;
GO

UPDATE SanPham
SET ImagePath = 'app/assets/products/caphe_sua.png'
WHERE TenSP = N'Cà Phê Sữa';
GO

UPDATE SanPham
SET ImagePath = 'app/assets/products/caphe_den.png'
WHERE TenSP = N'Cà Phê Đen';
GO

UPDATE SanPham
SET ImagePath = 'app/assets/products/bac_xiu.png'
WHERE TenSP = N'Bạc Xỉu';
GO

UPDATE SanPham
SET ImagePath = 'app/assets/products/tradao_camxa.png'
WHERE TenSP = N'Trà Đào Cam Sả';
GO
