
-- ----- 2.1. Nhân viên -----
-- (Sử dụng dữ liệu từ hình ảnh của bạn + thêm mới)
INSERT INTO NhanVien (MaNV, HoTen, GioiTinh, NgaySinh, ChucVu, LuongCoBan, TrangThai)
VALUES
('NV001', N'Nguyễn Trí Thiện', N'Nam', '1990-05-15', N'Quản lý', 30000.00, N'Đang làm'),
('NV002', N'Võ Thị Lan', N'Nữ', '1995-11-20', N'Thu ngân', 25000.00, N'Đang làm'),
('NV003', N'Nguyễn Tiến Bình', N'Nam', '1998-03-10', N'Pha chế', 22000.00, N'Đang làm'),
('NV004', N'Nguyễn Võ Thanh Sơn', N'Nam', '2000-07-25', N'Pha chế', 22000.00, N'Đang làm'),
('NV005', N'Trần Minh Trí', N'Nam', '2002-01-30', N'Thu ngân', 25000.00, N'Đang làm'),
('NV006', N'Nguyễn Văn Chiến', N'Nam', '2001-09-05', N'Pha chế', 22000.00, N'Đang làm'),
('NV007', N'Lê Thị Hoài An', N'Nữ', '2003-02-14', N'Phục vụ', 20000.00, N'Đang làm'),
('NV008', N'Phạm Văn Bảo', N'Nam', '1985-12-17', N'Bảo vệ', 20000.00, N'Đang làm');
GO

-- ----- 2.2. Tài khoản -----
-- (Mật khẩu cho tất cả đều là: 123)
-- (Sử dụng HASHBYTES SHA2_256 như trong login_frame.py)
INSERT INTO TaiKhoan (TenDangNhap, MatKhauHash, Role, MaNV)
VALUES
('admin', CONVERT(NVARCHAR(256), HASHBYTES('SHA2_256', '123'), 2), N'Admin', 'NV001'),
('nv002', CONVERT(NVARCHAR(256), HASHBYTES('SHA2_256', '123'), 2), N'Cashier', 'NV002'),
('nv004', CONVERT(NVARCHAR(256), HASHBYTES('SHA2_256', '123'), 2), N'Barista', 'NV004'),
('nv005', CONVERT(NVARCHAR(256), HASHBYTES('SHA2_256', '123'), 2), N'Cashier', 'NV005');
GO

-- ----- 2.3. Khách hàng -----
INSERT INTO KhachHang (MaKH, TenKH, SDT, DiemTichLuy)
VALUES
('KH001', N'Khách vãng lai', '0000000000', 0),
('KH002', N'Trần Văn An', '0905111222', 120),
('KH003', N'Lê Thị Bình', '0912333444', 45);
GO

-- ----- 2.4. Sản phẩm (Đồ uống) -----
INSERT INTO SanPham (MaSP, TenSP, LoaiSP, DonGia, TrangThai)
VALUES
('SP001', N'Cà Phê Đen', N'Cà phê', 20000.00, N'Còn bán'),
('SP002', N'Cà Phê Sữa', N'Cà phê', 25000.00, N'Còn bán'),
('SP003', N'Bạc Xỉu', N'Cà phê', 30000.00, N'Còn bán'),
('SP004', N'Trà Đào Cam Sả', N'Trà trái cây', 35000.00, N'Còn bán'),
('SP005', N'Trà Vải', N'Trà trái cây', 32000.00, N'Còn bán'),
('SP006', N'Nước Cam Ép', N'Nước ép', 40000.00, N'Còn bán'),
('SP007', N'Bánh Croissant', N'Bánh ngọt', 28000.00, N'Còn bán');
GO

-- ----- 2.5. Ca làm -----
-- (Phải bật IDENTITY_INSERT vì MaCa là IDENTITY)
SET IDENTITY_INSERT CaLam ON;
INSERT INTO CaLam (MaCa, TenCa, GioBatDau, GioKetThuc)
VALUES
(1, N'Sáng', '07:00:00', '11:00:00'),
(2, N'Chiều', '13:00:00', '17:00:00'),
(3, N'Tối', '17:00:00', '22:00:00'),
(4, N'Sáng (Mở sớm)', '06:30:00', '11:00:00'),
(5, N'Khuya muộn', '20:00:00', '23:31:00');
SET IDENTITY_INSERT CaLam OFF;
GO

-- ========= BƯỚC 3: THÊM DỮ LIỆU NGHIỆP VỤ (HÓA ĐƠN, CHẤM CÔNG) =========

-- ----- 3.1. Hóa đơn (Tháng 9 & 10 / 2025) -----
INSERT INTO HoaDon (MaHD, NgayLap, MaNV, MaKH, TongTien, TrangThai, GhiChu)
VALUES
-- Tháng 9
('HD0001', '2025-09-15 08:30:00', 'NV002', 'KH002', 82000.00, N'Đã thanh toán', N''),
('HD0002', '2025-09-20 14:15:00', 'NV005', 'KH001', 50000.00, N'Đã thanh toán', N'Ít đá'),
-- Tháng 10
('HD0003', '2025-10-27 09:05:00', 'NV002', 'KH003', 70000.00, N'Đã thanh toán', N''),
('HD0004', '2025-10-28 10:20:00', 'NV005', 'KH002', 64000.00, N'Đã thanh toán', N'Nhiều đường'),
('HD0005', '2025-10-30 19:00:00', 'NV002', 'KH001', 45000.00, N'Chưa thanh toán', N'');
GO

-- ----- 3.2. Chi tiết Hóa đơn -----
INSERT INTO ChiTietHoaDon (MaHD, MaSP, SoLuong, DonGia)
VALUES
-- HD0001
('HD0001', 'SP002', 2, 25000.00), -- 2 Cafe Sữa
('HD0001', 'SP005', 1, 32000.00), -- 1 Trà Vải
-- HD0002
('HD0002', 'SP002', 2, 25000.00), -- 2 Cafe Sữa
-- HD0003
('HD0003', 'SP003', 1, 30000.00), -- 1 Bạc Xỉu
('HD0003', 'SP006', 1, 40000.00), -- 1 Nước Cam
-- HD0004
('HD0004', 'SP005', 2, 32000.00), -- 2 Trà Vải
-- HD0005
('HD0005', 'SP001', 1, 20000.00), -- 1 Cafe Đen
('HD0005', 'SP002', 1, 25000.00); -- 1 Cafe Sữa
GO

-- ----- 3.3. Chấm công (Tháng 9 & 10 / 2025) -----
-- (Phải bật IDENTITY_INSERT vì MaCham là IDENTITY)
SET IDENTITY_INSERT ChamCong ON;
INSERT INTO ChamCong (MaCham, MaNV, MaCa, NgayLam, ClockIn, ClockOut, GhiChu)
VALUES
-- Dữ liệu T9/2025 (để tính lương T9)
(1, 'NV003', 1, '2025-09-01', '2025-09-01 07:00:00', '2025-09-01 11:00:00', N''), -- 4h
(2, 'NV004', 3, '2025-09-01', '2025-09-01 17:00:00', '2025-09-01 22:00:00', N''), -- 5h
(3, 'NV003', 1, '2025-09-02', '2025-09-02 07:00:00', '2025-09-02 11:00:00', N''), -- 4h
(4, 'NV004', 3, '2025-09-02', '2025-09-02 17:00:00', '2025-09-02 22:00:00', N''), -- 5h
(5, 'NV003', 1, '2025-09-03', '2025-09-03 07:00:00', '2025-09-03 11:00:00', N''), -- 4h (Tổng 12h)
(6, 'NV004', 3, '2025-09-03', '2025-09-03 17:00:00', '2025-09-03 22:00:00', N''), -- 5h (Tổng 15h)
(7, 'NV007', 2, '2025-09-03', '2025-09-03 13:00:00', '2025-09-03 17:00:00', N''), -- 4h

-- Dữ liệu T10/2025 (lấy từ hình ảnh của bạn + thêm mới)
(8, 'NV003', 1, '2025-10-27', '2025-10-27 07:00:00', '2025-10-27 11:00:00', N''), -- 4h (MaCham 1 cũ)
(9, 'NV006', 1, '2025-10-27', '2025-10-27 07:00:00', '2025-10-27 11:00:00', N''), -- 4h (MaCham 2 cũ)
(10, 'NV004', 3, '2025-10-27', '2025-10-27 17:10:00', '2025-10-27 22:00:00', N'Trễ 10 phút'), -- 4.83h (MaCham 3 cũ)
(11, 'NV004', 5, '2025-10-30', '2025-10-30 18:16:00', '2025-10-30 22:00:00', N'Trễ 1 tiếng 16 phút'), -- 3.73h (MaCham 5 cũ, ĐÃ SỬA GIỜ RA)
(12, 'NV007', 2, '2025-10-28', '2025-10-28 13:00:00', '2025-10-28 17:00:00', N''), -- 4h
(13, 'NV001', 1, '2025-10-28', '2025-10-28 07:00:00', '2025-10-28 11:00:00', N'Quản lý hỗ trợ'); -- 4h
SET IDENTITY_INSERT ChamCong OFF;
GO

-- ========= BƯỚC 4: TÍNH SẴN BẢNG LƯƠNG (CHỈ THÁNG 9) =========
-- (Để trống T10 để bạn test nút "Tính lương tháng này")
-- (Phải bật IDENTITY_INSERT vì MaLuong là IDENTITY)
SET IDENTITY_INSERT BangLuong ON;
INSERT INTO BangLuong (MaLuong, MaNV, Thang, Nam, TongGio, LuongThucTe, TrangThai)
VALUES
-- NV003: 12h * 22000 = 264,000 (Giả sử 1 tháng 208h) -> (22000 * 12) * (208/208) ?
-- Logic của bạn là: (LuongCoBan * TongGio) / 208
-- NV003 (T9): (22000 * 12) / 208 = 1269.23
-- NV004 (T9): (22000 * 15) / 208 = 1586.53
-- NV007 (T9): (20000 * 4) / 208 = 384.61
(1, 'NV003', 9, 2025, 12.0, (22000 * 12.0) / 208.0, N'Đã trả'),
(2, 'NV004', 9, 2025, 15.0, (22000 * 15.0) / 208.0, N'Đã trả'),
(3, 'NV007', 9, 2025, 4.0, (20000 * 4.0) / 208.0, N'Chưa trả');
SET IDENTITY_INSERT BangLuong OFF;
GO

PRINT N'✅ ĐÃ THÊM DỮ LIỆU MẪU THÀNH CÔNG!';

SELECT * FROM TaiKhoan