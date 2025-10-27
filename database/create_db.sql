USE QL_CaPhe;
GO

-- create_db.sql - Full schema for QL_CaPhe (SQL Server)
-- Author: Nguyen Tri Thien
-- Date: 2025-10-08


-- ==== DB: QL_CaPhe
IF DB_ID(N'QL_CaPhe') IS NOT NULL
BEGIN
    ALTER DATABASE QL_CaPhe SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE QL_CaPhe;
END
GO

-- ----- Create DB -----
CREATE DATABASE QL_CaPhe;
GO
USE QL_CaPhe;
GO

 
-- ===== TABLE: NhanVien =====
CREATE TABLE NhanVien (
    MaNV CHAR(6) PRIMARY KEY,
    HoTen NVARCHAR(100) NOT NULL,
    GioiTinh NVARCHAR(10) NULL,
    NgaySinh DATE NULL,
    ChucVu NVARCHAR(50) NULL,
    LuongCoBan DECIMAL(12,2) DEFAULT 0,
    TrangThai NVARCHAR(20) DEFAULT N'Đang làm'
);
GO

-- ===== TABLE: KhachHang =====
CREATE TABLE KhachHang (
    MaKH CHAR(6) PRIMARY KEY,
    TenKH NVARCHAR(100) NULL,
    SDT NVARCHAR(15) NULL,
    DiemTichLuy INT DEFAULT 0
);
GO

-- ===== TABLE: SanPham =====
CREATE TABLE SanPham (
    MaSP CHAR(6) PRIMARY KEY,
    TenSP NVARCHAR(150) NOT NULL,
    LoaiSP NVARCHAR(50) NULL,
    DonGia DECIMAL(12,2) NOT NULL DEFAULT 0,
    TrangThai NVARCHAR(20) DEFAULT N'Còn bán'
);
GO

-- ===== TABLE: HoaDon (hoặc Order) =====
CREATE TABLE HoaDon (
    MaHD CHAR(8) PRIMARY KEY,
    NgayLap DATETIME DEFAULT GETDATE(),
    MaNV CHAR(6) NOT NULL,                 -- người lập hóa đơn (nhân viên)
    MaKH CHAR(6) NULL,                     -- khách hàng (nếu có)
    TongTien DECIMAL(12,2) DEFAULT 0,
    TrangThai NVARCHAR(20) DEFAULT N'Chưa thanh toán',
    GhiChu NVARCHAR(255) NULL,
    CONSTRAINT FK_HoaDon_NhanVien FOREIGN KEY (MaNV) REFERENCES NhanVien(MaNV),
    CONSTRAINT FK_HoaDon_KhachHang FOREIGN KEY (MaKH) REFERENCES KhachHang(MaKH)
);
GO

-- ===== TABLE: ChiTietHoaDon =====
CREATE TABLE ChiTietHoaDon (
    MaHD CHAR(8) NOT NULL,
    MaSP CHAR(6) NOT NULL,
    SoLuong INT NOT NULL CHECK (SoLuong > 0),
    DonGia DECIMAL(12,2) NOT NULL CHECK (DonGia >= 0), -- giá tại thời điểm bán
    ThanhTien AS (SoLuong * DonGia) PERSISTED,         -- computed persisted
    PRIMARY KEY (MaHD, MaSP),
    CONSTRAINT FK_CTHD_HoaDon FOREIGN KEY (MaHD) REFERENCES HoaDon(MaHD),
    CONSTRAINT FK_CTHD_SanPham FOREIGN KEY (MaSP) REFERENCES SanPham(MaSP)
);
GO

-- ===== TABLE: CaLam (ca làm chuẩn) =====
CREATE TABLE CaLam (
    MaCa INT IDENTITY(1,1) PRIMARY KEY,
    TenCa NVARCHAR(50) NULL,
    GioBatDau TIME NULL,
    GioKetThuc TIME NULL
);
GO

-- ===== TABLE: ChamCong (attendance) =====
CREATE TABLE ChamCong (
    MaCham INT IDENTITY(1,1) PRIMARY KEY,
    MaNV CHAR(6) NOT NULL,
    MaCa INT NULL,
    NgayLam DATE NOT NULL,
    ClockIn DATETIME NULL,
    ClockOut DATETIME NULL,
    GhiChu NVARCHAR(255) NULL,
    CONSTRAINT FK_ChamCong_NhanVien FOREIGN KEY (MaNV) REFERENCES NhanVien(MaNV),
    CONSTRAINT FK_ChamCong_CaLam FOREIGN KEY (MaCa) REFERENCES CaLam(MaCa)
);
GO

-- ===== TABLE: BangLuong =====
CREATE TABLE BangLuong (
    MaLuong INT IDENTITY(1,1) PRIMARY KEY,
    MaNV CHAR(6) NOT NULL,
    Thang INT NOT NULL,
    Nam INT NOT NULL,
    TongGio DECIMAL(10,2) DEFAULT 0,
    LuongThucTe DECIMAL(12,2) DEFAULT 0,
    TrangThai NVARCHAR(20) DEFAULT N'Chưa trả',
    CONSTRAINT FK_BangLuong_NhanVien FOREIGN KEY (MaNV) REFERENCES NhanVien(MaNV)
);
GO

-- ===== TABLE: TaiKhoan (accounts / users) =====
CREATE TABLE TaiKhoan (
    TenDangNhap NVARCHAR(50) PRIMARY KEY,
    MatKhauHash NVARCHAR(256) NOT NULL,
    Role NVARCHAR(20) DEFAULT N'cashier',  -- admin / manager / cashier / barista
    MaNV CHAR(6) NULL,
    CreatedAt DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_TaiKhoan_NhanVien FOREIGN KEY (MaNV) REFERENCES NhanVien(MaNV)
);
GO

-- ===== Optional: Table for inventory / ingredients and recipes =====
CREATE TABLE NguyenLieu (
    MaNL CHAR(6) PRIMARY KEY,
    TenNL NVARCHAR(150),
    DonVi NVARCHAR(30),
    SoLuongTon DECIMAL(12,3) DEFAULT 0
);
GO

CREATE TABLE CongThuc (
    MaCT INT IDENTITY(1,1) PRIMARY KEY,
    MaSP CHAR(6) NOT NULL,
    MaNL CHAR(6) NOT NULL,
    SoLuong DECIMAL(12,3) NOT NULL, -- quantity of ingredient per product
    CONSTRAINT FK_CongThuc_SanPham FOREIGN KEY (MaSP) REFERENCES SanPham(MaSP),
    CONSTRAINT FK_CongThuc_NguyenLieu FOREIGN KEY (MaNL) REFERENCES NguyenLieu(MaNL)
);  
GO

CREATE TABLE InventoryMovements (
    MovementID INT IDENTITY(1,1) PRIMARY KEY,
    MaNL CHAR(6) NOT NULL,
    ChangeQty DECIMAL(12,3) NOT NULL,
    MovementType NVARCHAR(20) NOT NULL, -- sale / purchase / adjust
    RefMaHD CHAR(8) NULL,
    CreatedAt DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_InvMov_NL FOREIGN KEY (MaNL) REFERENCES NguyenLieu(MaNL),
    CONSTRAINT FK_InvMov_HD FOREIGN KEY (RefMaHD) REFERENCES HoaDon(MaHD)
);
GO

use QL_CaPhe
go

DECLARE @kw NVARCHAR(10) = '%1%';
SELECT *
FROM CaLam
WHERE CAST(MaCa AS NVARCHAR(10)) LIKE @kw
   OR TenCa LIKE @kw
   OR CONVERT(VARCHAR(5), GioBatDau, 108) LIKE @kw
   OR CONVERT(VARCHAR(5), GioKetThuc, 108) LIKE @kw;
