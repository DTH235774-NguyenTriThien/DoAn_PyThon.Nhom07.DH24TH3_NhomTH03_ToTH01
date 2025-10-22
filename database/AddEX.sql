USE QL_CaPhe;
GO

-- Thêm NhanVien (dùng N'...' để đảm bảo Unicode)
INSERT INTO NhanVien (MaNV, HoTen, GioiTinh, NgaySinh, ChucVu, LuongCoBan, TrangThai)
VALUES
('NV001', N'Nguyễn Trí Thiện', N'Nam', '2003-01-01', N'Quản lý', 8000000, N'Đang làm'),
('NV002', N'Võ Thị Lan', N'Nữ', '2000-06-12', N'Thu ngân', 5500000, N'Đang làm');
GO

-- Thêm KhachHang mẫu
INSERT INTO KhachHang (MaKH, TenKH, SDT, DiemTichLuy)
VALUESUSE QL_CaPhe;
GO

-- Thêm NhanVien (dùng N'...' để đảm bảo Unicode)
INSERT INTO NhanVien (MaNV, HoTen, GioiTinh, NgaySinh, ChucVu, LuongCoBan, TrangThai)
VALUES
('NV001', N'Nguyễn Trí Thiện', N'Nam', '2003-01-01', N'Quản lý', 8000000, N'Đang làm'),
('NV002', N'Võ Thị Lan', N'Nữ', '2000-06-12', N'Thu ngân', 5500000, N'Đang làm');
GO

-- Thêm KhachHang mẫu
INSERT INTO KhachHang (MaKH, TenKH, SDT, DiemTichLuy)
VALUES
('KH001', N'Nguyễn Văn B', '0912345678', 10),
('KH002', N'Trần Thị C', '0987654321', 5);
GO

-- Thêm SanPham mẫu (Tên sản phẩm bằng tiếng Việt)
INSERT INTO SanPham (MaSP, TenSP, LoaiSP, DonGia, TrangThai)
VALUES
('CF001', N'Cà phê đen đá', N'Cà phê', 20000, N'Còn bán'),
('CF002', N'Cà phê sữa', N'Cà phê', 25000, N'Còn bán'),
('TS001', N'Trá sữa trân châu', N'Trá sữa', 35000, N'Còn bán');
GO

INSERT INTO CaLam (TenCa, GioBatDau, GioKetThuc)
VALUES (N'Sáng', '07:00', '11:00'),
       (N'Chiều', '13:00', '17:00');
GO

INSERT INTO ChamCong (MaNV, MaCa, NgayLam, ClockIn, ClockOut, GhiChu)
VALUES ('NV002', 1, '2025-10-08', '2025-10-08 07:10', '2025-10-08 11:05', N'Vào muộn 10 phút');
GO

INSERT INTO TaiKhoan (TenDangNhap, MatKhauHash, Role, MaNV)
VALUES ('admin', CONVERT(NVARCHAR(256), HASHBYTES('SHA2_256', N'admin123'), 2), N'admin', 'NV001');
GO

-- Tạo hoá đơn mẫu + chi tiết
INSERT INTO HoaDon (MaHD, MaNV, MaKH, TongTien, TrangThai, GhiChu)
VALUES ('HD000001', 'NV001', 'KH001', 0, N'Chưa thanh toán', N'Mẫu test');
GO

INSERT INTO ChiTietHoaDon (MaHD, MaSP, SoLuong, DonGia)
VALUES 
('HD000001', 'CF002', 2, 25000),
('HD000001', 'TS001', 1, 35000);
GO

-- Cập nhật TongTien trong HoaDon từ ChiTietHoaDon
UPDATE HoaDon
SET TongTien = (SELECT SUM(ThanhTien) FROM ChiTietHoaDon WHERE ChiTietHoaDon.MaHD = HoaDon.MaHD)
WHERE MaHD = 'HD000001';
GO

-- KIỂM TRA MẪU 
SELECT * FROM NhanVien;
SELECT * FROM KhachHang;
SELECT * FROM SanPham;
SELECT * FROM HoaDon;
SELECT * FROM ChiTietHoaDon;
SELECT * FROM TaiKhoan;
SELECT * FROM CaLam;
SELECT * FROM ChamCong;
SELECT * FROM BangLuong;
SELECT * FROM NguyenLieu;
SELECT * FROM CongThuc;
SELECT * FROM InventoryMovements;
('KH001', N'Nguyễn Văn B', '0912345678', 10),
('KH002', N'Trần Thị C', '0987654321', 5);
GO

-- Thêm SanPham mẫu (Tên sản phẩm bằng tiếng Việt)
INSERT INTO SanPham (MaSP, TenSP, LoaiSP, DonGia, TrangThai)
VALUES
('CF001', N'Cà phê đen đá', N'Cà phê', 20000, N'Còn bán'),
('CF002', N'Cà phê sữa', N'Cà phê', 25000, N'Còn bán'),
('TS001', N'Trá sữa trân châu', N'Trá sữa', 35000, N'Còn bán');
GO

-- Thêm CaLam & ChamCong mẫu (nếu bạn muốn test chấm công)
INSERT INTO CaLam (TenCa, GioBatDau, GioKetThuc)
VALUES (N'Sáng', '07:00', '11:00'),
       (N'Chiều', '13:00', '17:00');
GO

INSERT INTO ChamCong (MaNV, MaCa, NgayLam, ClockIn, ClockOut, GhiChu)
VALUES ('NV002', 1, '2025-10-08', '2025-10-08 07:10', '2025-10-08 11:05', N'Vào muộn 10 phút');
GO

-- Thêm TaiKhoan mẫu: (Lưu ý: dùng HASHBYTES để minh họa lưu hash)
-- LƯU Ý: Ở app bạn nên dùng bcrypt; đây chỉ là ví dụ sơ khai.
INSERT INTO TaiKhoan (TenDangNhap, MatKhauHash, Role, MaNV)
VALUES ('admin', CONVERT(NVARCHAR(256), HASHBYTES('SHA2_256', N'admin123'), 2), N'admin', 'NV001');
GO

-- Tạo hoá đơn mẫu + chi tiết
INSERT INTO HoaDon (MaHD, MaNV, MaKH, TongTien, TrangThai, GhiChu)
VALUES ('HD000001', 'NV001', 'KH001', 0, N'Chưa thanh toán', N'Mẫu test');
GO

INSERT INTO ChiTietHoaDon (MaHD, MaSP, SoLuong, DonGia)
VALUES 
('HD000001', 'CF002', 2, 25000),
('HD000001', 'TS001', 1, 35000);
GO

-- Cập nhật TongTien trong HoaDon từ ChiTietHoaDon
UPDATE HoaDon
SET TongTien = (SELECT SUM(ThanhTien) FROM ChiTietHoaDon WHERE ChiTietHoaDon.MaHD = HoaDon.MaHD)
WHERE MaHD = 'HD000001';
GO

-- KIỂM TRA MẪU 
SELECT * FROM NhanVien;
SELECT * FROM KhachHang;
SELECT * FROM SanPham;
SELECT * FROM HoaDon;
SELECT * FROM ChiTietHoaDon;
SELECT * FROM TaiKhoan;
SELECT * FROM CaLam;
SELECT * FROM ChamCong;
SELECT * FROM BangLuong;
SELECT * FROM NguyenLieu;
SELECT * FROM CongThuc;
SELECT * FROM InventoryMovements;