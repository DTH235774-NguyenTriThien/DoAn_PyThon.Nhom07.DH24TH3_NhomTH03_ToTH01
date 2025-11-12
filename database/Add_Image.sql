SELECT * FROM NguyenLieu
SELECT * FROM KhachHang
SELECT * from HoaDon
select * from ChiTietHoaDon
select * from congthuc
select * from SanPham	

USE QL_CaPhe
GO

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

UPDATE SanPham
SET ImagePath = 'app/assets/products/tra_vai.png'
WHERE TenSP = N'Trà Vải';
GO

UPDATE SanPham
SET ImagePath = 'app/assets/products/banh_croissant.png'
WHERE TenSP = N'Bánh Croissant';
GO

UPDATE SanPham
SET ImagePath = 'app/assets/products/banh_tiramisu.png'
WHERE TenSP = N'Bánh Tiramisu';
GO


UPDATE SanPham
SET ImagePath = 'app/assets/products/cam_ep.png'
WHERE TenSP = N'Nước Cam Ép';
GO




UPDATE SanPham
SET ImagePath = 'app/assets/products/cappuccino.png'
WHERE TenSP = N'Cappuccino';
GO



UPDATE SanPham
SET ImagePath = 'app/assets/products/espresso.png'
WHERE TenSP = N'Espresso';
GO



UPDATE SanPham
SET ImagePath = 'app/assets/products/tra_sen.png' 
WHERE TenSP = N'Trà Sen';
GO


UPDATE SanPham
SET ImagePath = 'app/assets/products/latte.png'
WHERE TenSP = N'Latte';
GO

UPDATE SanPham
SET ImagePath = 'app/assets/products/caphe_cotdua.png'
WHERE TenSP = N'Cà Phê Cốt Dừa';
GO



UPDATE SanPham
SET ImagePath = 'app/assets/products/cookie_daxay.png'
WHERE TenSP = N'Cookie Đá Xay';
GO

UPDATE SanPham
SET ImagePath = 'app/assets/products/hat_huongduong.png'
WHERE TenSP = N'Hạt hướng dương';
GO

UPDATE SanPham
SET ImagePath = 'app/assets/products/latte.png'
WHERE TenSP = N'Latte';
GO

UPDATE SanPham
SET ImagePath = 'app/assets/products/nuoc_chanh.png'
WHERE TenSP = N'Nước Chanh';
GO

UPDATE SanPham
SET ImagePath = 'app/assets/products/sinhto_bo.png'
WHERE TenSP = N'Sinh tố Bơ';
GO

UPDATE SanPham
SET ImagePath = 'app/assets/products/sinhto_xoai.png'
WHERE TenSP = N'Sinh tố Xoài';
GO

UPDATE SanPham
SET ImagePath = 'app/assets/products/tra_olong.png'
WHERE TenSP = N'Trà Ô Long';
GO




UPDATE SanPham
SET ImagePath = 'app/assets/products/tragung_matong.png'
WHERE TenSP = N'Trà Gừng Mật Ong';
GO


UPDATE SanPham
SET ImagePath = 'app/assets/products/trasua_mochi.png'
WHERE TenSP = N'Trà Sữa Mochi';
GO

SELECT * from NhanVien
select * from TaiKhoan