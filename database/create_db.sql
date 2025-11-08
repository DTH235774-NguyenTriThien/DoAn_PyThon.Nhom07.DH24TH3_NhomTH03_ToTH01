USE QL_CaPhe;
GO

-- create_db.sql - Full schema for QL_CaPhe (SQL Server)
-- Author: Nguyen Tri Thien
-- Date: 2025-10-08


-- ==== DB: QL_CaPhe
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'QL_CaPhe')
BEGIN
    CREATE DATABASE QL_CaPhe;
END
GO

USE QL_CaPhe;
GO

/* --- Bảng 1: Nhân Viên --- */
CREATE TABLE NhanVien (
    MaNV NVARCHAR(10) NOT NULL PRIMARY KEY,
    HoTen NVARCHAR(100) NOT NULL,
    GioiTinh NVARCHAR(10) NULL,
    NgaySinh DATE NULL,
    ChucVu NVARCHAR(50) NULL,
    LuongCoBan DECIMAL(18, 2) NULL, -- (Giả định đây là Lương THEO GIỜ)
    TrangThai NVARCHAR(50) NOT NULL DEFAULT N'Đang làm'
);
GO

/* --- Bảng 2: Tài Khoản (Bảo mật) --- */
CREATE TABLE TaiKhoan (
    TenDangNhap NVARCHAR(50) NOT NULL PRIMARY KEY,
    MatKhauHash NVARCHAR(100) NOT NULL, -- (Lưu trữ Bcrypt hash)
    Role NVARCHAR(50) NOT NULL,
    MaNV NVARCHAR(10) NULL,
    CONSTRAINT FK_TaiKhoan_NhanVien FOREIGN KEY (MaNV) REFERENCES NhanVien(MaNV) ON DELETE SET NULL
);
GO

/* --- Bảng 3: Ca Làm Việc --- */
CREATE TABLE CaLam (
    MaCa INT NOT NULL PRIMARY KEY,
    TenCa NVARCHAR(50) NOT NULL,
    GioBatDau TIME NOT NULL,
    GioKetThuc TIME NOT NULL
);
GO

/* --- Bảng 4: Chấm Công --- */
CREATE TABLE ChamCong (
    MaCham INT NOT NULL PRIMARY KEY,
    MaNV NVARCHAR(10) NULL,
    MaCa INT NULL,
    NgayLam DATE NOT NULL,
    ClockIn DATETIME NULL,
    ClockOut DATETIME NULL,
    GhiChu NVARCHAR(255) NULL,
    CONSTRAINT FK_ChamCong_NhanVien FOREIGN KEY (MaNV) REFERENCES NhanVien(MaNV) ON DELETE SET NULL,
    CONSTRAINT FK_ChamCong_CaLam FOREIGN KEY (MaCa) REFERENCES CaLam(MaCa) ON DELETE SET NULL
);
GO

/* --- Bảng 5: Bảng Lương (Tính theo tháng) --- */
CREATE TABLE BangLuong (
    MaLuong INT IDENTITY(1,1) NOT NULL PRIMARY KEY, -- (Dùng ID tự tăng)
    MaNV NVARCHAR(10) NULL,
    Thang INT NOT NULL,
    Nam INT NOT NULL,
    TongGio DECIMAL(10, 2) NULL,
    LuongThucTe DECIMAL(18, 2) NULL,
    TrangThai NVARCHAR(50) NOT NULL DEFAULT N'Chưa trả',
    CONSTRAINT FK_BangLuong_NhanVien FOREIGN KEY (MaNV) REFERENCES NhanVien(MaNV) ON DELETE SET NULL
);
GO

/* --- Bảng 6: Khách Hàng --- */
CREATE TABLE KhachHang (
    MaKH NVARCHAR(10) NOT NULL PRIMARY KEY,
    TenKH NVARCHAR(100) NOT NULL,
    SDT NVARCHAR(15) NULL,
    DiemTichLuy INT NOT NULL DEFAULT 0
    -- (Cột TrangThai đã bị loại bỏ)
);
GO

/* --- Bảng 7: Nguyên Liệu (Kho) --- */
CREATE TABLE NguyenLieu (
    MaNL NVARCHAR(10) NOT NULL PRIMARY KEY,
    TenNL NVARCHAR(100) NOT NULL UNIQUE,
    DonVi NVARCHAR(20) NOT NULL,
    SoLuongTon DECIMAL(18, 3) NOT NULL DEFAULT 0
);
GO

/* --- Bảng 8: Sản Phẩm (Menu) --- */
CREATE TABLE SanPham (
    MaSP NVARCHAR(10) NOT NULL PRIMARY KEY,
    TenSP NVARCHAR(100) NOT NULL,
    LoaiSP NVARCHAR(50) NULL,
    DonGia DECIMAL(18, 2) NOT NULL DEFAULT 0,
    TrangThai NVARCHAR(50) NOT NULL DEFAULT N'Còn bán',
    ImagePath NVARCHAR(255) NULL 
);
GO

/* --- Bảng 9: Công Thức (Liên kết SP và NL) --- */
CREATE TABLE CongThuc (
    MaSP NVARCHAR(10) NOT NULL,
    MaNL NVARCHAR(10) NOT NULL,
    SoLuong DECIMAL(18, 3) NOT NULL,
    CONSTRAINT PK_CongThuc PRIMARY KEY (MaSP, MaNL),
    CONSTRAINT FK_CongThuc_SanPham FOREIGN KEY (MaSP) REFERENCES SanPham(MaSP) ON DELETE CASCADE,
    CONSTRAINT FK_CongThuc_NguyenLieu FOREIGN KEY (MaNL) REFERENCES NguyenLieu(MaNL) ON DELETE CASCADE
);
GO

/* --- Bảng 10: Hóa Đơn (Thông tin chung) --- */
CREATE TABLE HoaDon (
    MaHD NVARCHAR(10) NOT NULL PRIMARY KEY,
    NgayLap DATETIME NOT NULL DEFAULT GETDATE(),
    MaNV NVARCHAR(10) NULL,
    MaKH NVARCHAR(10) NULL, 
    TongTien DECIMAL(18, 2) NULL,
    GiamGia DECIMAL(18, 2) NULL,
    ThanhTien DECIMAL(18, 2) NULL,
    TrangThai NVARCHAR(50) NOT NULL DEFAULT N'Đã thanh toán',
    DiemSuDung INT NULL,
    GhiChu NVARCHAR(255) NULL, 
    CONSTRAINT FK_HoaDon_NhanVien FOREIGN KEY (MaNV) REFERENCES NhanVien(MaNV) ON DELETE SET NULL,
    CONSTRAINT FK_HoaDon_KhachHang FOREIGN KEY (MaKH) REFERENCES KhachHang(MaKH) ON DELETE SET NULL
);
GO

/* --- Bảng 11: Chi Tiết Hóa Đơn (Các món đã bán) --- */
CREATE TABLE ChiTietHoaDon (
    ChiTietID INT IDENTITY(1,1) NOT NULL PRIMARY KEY, 
    MaHD NVARCHAR(10) NOT NULL,
    MaSP NVARCHAR(10) NOT NULL,
    SoLuong INT NOT NULL,
    DonGia DECIMAL(18, 2) NOT NULL,
    ThanhTien AS (SoLuong * DonGia),
    GhiChu NVARCHAR(100) NULL, 
    CONSTRAINT FK_CTHD_HoaDon FOREIGN KEY (MaHD) REFERENCES HoaDon(MaHD) ON DELETE CASCADE,
    CONSTRAINT FK_CTHD_SanPham FOREIGN KEY (MaSP) REFERENCES SanPham(MaSP)
);
GO

/* --- Bảng 12: Lịch sử Kho */
CREATE TABLE InventoryMovements (
    MovementID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    MaNL NVARCHAR(10) NULL,
    ChangeQty DECIMAL(18, 3) NOT NULL,
    MovementType NVARCHAR(50),
    Timestamp DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_Movements_NguyenLieu FOREIGN KEY (MaNL) REFERENCES NguyenLieu(MaNL) ON DELETE SET NULL
);
GO