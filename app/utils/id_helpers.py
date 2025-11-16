# app/utils/id_helpers.py

def generate_next_manv(cursor):
    """
    Tạo mã nhân viên tiếp theo (NV00x) dựa trên dữ liệu hiện có trong DB.
    Trả về mã nhỏ nhất chưa được dùng.
    """
    cursor.execute("SELECT MaNV FROM NhanVien")
    rows = [r.MaNV.strip().upper() for r in cursor.fetchall() if r.MaNV]

    numbers = []
    for code in rows:
        if code.startswith("NV"):
            try:
                num = int(code[2:])
                numbers.append(num)
            except ValueError:
                pass

    next_num = 1
    while next_num in numbers:
        next_num += 1

    return f"NV{next_num:03d}"

def generate_next_masp(cursor):
    """
    Sinh mã MaSP dạng SP001, SP002... dựa trên MaSP hiện có trong bảng SANPHAM.
    """
    cursor.execute("SELECT MaSP FROM SANPHAM")
    rows = [r.MaSP.strip().upper() for r in cursor.fetchall() if r.MaSP]
    nums = []
    for code in rows:
        if code.startswith("SP"):
            try:
                nums.append(int(code[2:]))
            except Exception:
                pass
    next_num = 1
    while next_num in nums:
        next_num += 1
    return f"SP{next_num:03d}"

def generate_next_mahd(cursor):
    """
    Sinh mã MaHD dạng HD0001, HD0002... dựa trên MaHD hiện có trong bảng HoaDon.
    """
    cursor.execute("SELECT MaHD FROM HoaDon")
    rows = [r.MaHD.strip().upper() for r in cursor.fetchall() if r.MaHD]
    nums = []
    for code in rows:
        if code.startswith("HD"):
            try:
                nums.append(int(code[2:]))
            except Exception:
                pass
    next_num = 1
    while next_num in nums:
        next_num += 1
    return f"HD{next_num:04d}"

def generate_next_makh(cursor):
    """
    Sinh mã MaKH dạng KH001, KH002...
    """
    cursor.execute("SELECT MaKH FROM KhachHang")
    rows = [r.MaKH.strip().upper() for r in cursor.fetchall() if r.MaKH]
    nums = []
    for code in rows:
        if code.startswith("KH"):
            try:
                nums.append(int(code[2:]))
            except Exception:
                pass
    next_num = 1
    while next_num in nums:
        next_num += 1
    return f"KH{next_num:03d}"

def generate_next_macc(cursor):
    """
    Sinh mã chấm công (MaCham) mới — tự động tìm khoảng trống nhỏ nhất.
    Nếu bảng rỗng, bắt đầu từ 1.
    """
    try:
        cursor.execute("SELECT MaCham FROM ChamCong ORDER BY MaCham ASC")
        rows = cursor.fetchall()
        if not rows:
            return 1

        existing = [r.MaCham for r in rows if r.MaCham is not None]

        expected = 1
        for val in existing:
            if val != expected:
                break
            expected += 1
        return expected
    except Exception as e:
        return 1

def generate_next_maca(cursor):
    """
    Sinh mã ca (MaCa) mới, tự động tìm khoảng trống nhỏ nhất chưa dùng.
    """
    try:
        cursor.execute("SELECT MaCa FROM CaLam ORDER BY MaCa ASC")
        rows = cursor.fetchall()

        if not rows:
            return 1 

        existing_ids = [r.MaCa for r in rows if r.MaCa is not None]
        expected = 1
        for value in existing_ids:
            if value != expected:
                return expected
            expected += 1

        return expected
    except Exception as e:
        return 1
    
def generate_next_manl(cursor):
    """
    Sinh mã MaNL dạng NL001, NL002... dựa trên MaNL hiện có.
    """
    try:
        cursor.execute("SELECT MaNL FROM NguyenLieu")
        rows = [r.MaNL.strip().upper() for r in cursor.fetchall() if r.MaNL]
        nums = []
        for code in rows:
            if code.startswith("NL"):
                try:
                    nums.append(int(code[2:]))
                except Exception:
                    pass
        next_num = 1
        while next_num in nums:
            next_num += 1
        return f"NL{next_num:03d}"
    except Exception as e:
        return "NL001"