# scripts/seed_products.py
import sys
import os

# --- Thêm thư mục gốc vào system path để import các module của app ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # Import các helper CSDL và ID
    from app.db import execute_query, execute_scalar, conn, cursor
    from app.utils.id_helpers import generate_next_masp
except ImportError as e:
    print(f"LỖI: Không thể import 'app.db' hoặc 'id_helpers'. Lỗi: {e}")
    print("Hãy đảm bảo bạn chạy script này từ thư mục gốc (Doan_Python), không phải từ 'scripts/'")
    sys.exit(1)

# =========================================================
# TỪ ĐIỂN SẢN PHẨM MẪU
# (Tên SP: (Loại SP, Đơn giá))
# =========================================================
PRODUCT_MAP = {
    # Cà phê
    "Cà Phê Đen": ("Cà phê", 20000),
    "Cà Phê Sữa": ("Cà phê", 25000),
    "Bạc Xỉu": ("Cà phê", 30000),
    "Cà Phê Cốt Dừa": ("Cà phê", 35000),
    "Espresso": ("Cà phê", 35000),
    "Cappuccino": ("Cà phê", 45000),
    "Latte": ("Cà phê", 45000),

    # Trà
    "Trà Đào Cam Sả": ("Trà trái cây", 35000),
    "Trà Vải": ("Trà trái cây", 32000),
    "Trà Ô Long": ("Trà", 30000),
    "Trà Gừng Mật Ong": ("Trà", 30000),
    "Trà Sen": ("Trà", 30000),

    # Nước ép / Đá xay
    "Nước Cam Ép": ("Nước ép", 40000),
    "Nước Chanh": ("Nước ép", 28000),
    "Sinh tố Bơ": ("Đá xay", 45000),
    "Sinh tố Xoài": ("Đá xay", 45000),
    "Cookie Đá Xay": ("Đá xay", 50000),

    # Đồ ăn kèm
    "Bánh Croissant": ("Bánh ngọt", 28000),
    "Bánh Tiramisu": ("Bánh ngọt", 35000),
    "Hạt hướng dương": ("Đồ ăn vặt", 15000),
}

def seed_data():
    """
    Thêm các sản phẩm từ PRODUCT_MAP vào CSDL.
    Sẽ bỏ qua nếu Tên Sản Phẩm (TenSP) đã tồn tại.
    """
    print("Bắt đầu thêm dữ liệu sản phẩm mẫu...")

    if cursor is None or conn is None:
        print("LỖI: Không thể kết nối CSDL.")
        return

    count_added = 0
    count_skipped = 0

    try:
        # Sắp xếp map theo tên
        sorted_products = sorted(PRODUCT_MAP.items())

        for ten_sp, (loai_sp, don_gia) in sorted_products:

            # 1. Kiểm tra xem TÊN SẢN PHẨM đã tồn tại chưa
            check_query = "SELECT COUNT(*) FROM SanPham WHERE TenSP = ?"
            if execute_scalar(check_query, (ten_sp,)) > 0:
                print(f"  [BỎ QUA] '{ten_sp}' đã tồn tại.")
                count_skipped += 1
                continue

            # 2. Tạo Mã SP mới
            masp = generate_next_masp(cursor)

            # 3. Thêm vào CSDL (Mặc định 'Còn bán')
            insert_query = """
                INSERT INTO SanPham (MaSP, TenSP, LoaiSP, DonGia, TrangThai) 
                VALUES (?, ?, ?, ?, N'Còn bán')
            """
            if execute_query(insert_query, (masp, ten_sp, loai_sp, don_gia)):
                print(f"  [THÊM] {masp} - {ten_sp} ({don_gia:,.0f}đ)")
                count_added += 1
            else:
                print(f"  [LỖI] Không thể thêm {ten_sp}")

        print("\nHoàn tất!")
        print(f"Đã thêm mới: {count_added} sản phẩm.")
        print(f"Đã bỏ qua (trùng lặp): {count_skipped} sản phẩm.")

    except Exception as e:
        print(f"\nĐÃ XẢY RA LỖI: {e}")
    finally:
        if conn:
            conn.close()
            print("Đã đóng kết nối CSDL.")

if __name__ == "__main__":
    seed_data()