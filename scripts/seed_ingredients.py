# scripts/seed_ingredients.py
import sys
import os

# --- Thêm thư mục gốc vào system path để import các module của app ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # Import các helper CSDL và ID
    from app.db import execute_query, execute_scalar, conn, cursor
    from app.utils.id_helpers import generate_next_manl
except ImportError as e:
    print(f"LỖI: Không thể import 'app.db' hoặc 'id_helpers'. Lỗi: {e}")
    print("Hãy đảm bảo bạn chạy script này từ thư mục gốc (Doan_Python), không phải từ 'scripts/'")
    sys.exit(1)

# =========================================================
# SAO CHÉP TỪ ĐIỂN TỪ MODULE INGREDIENTS
# (Để script này có thể chạy độc lập mà không cần import UI)
# =========================================================
INGREDIENT_MAP = {
    # Cà phê
    "Cà phê hạt": "kg", "Cà phê bột": "kg", "Cà phê (phin giấy)": "gói",
    # Sữa
    "Sữa đặc": "lon", "Sữa tươi": "l", "Sữa (ml)": "ml", "Kem béo (Rich)": "l",
    "Kem (Whipping Cream)": "l", "Sữa chua": "kg", "Đường cát": "kg",
    # Đường / Siro
    "Đường nước": "ml", "Đường phèn": "kg", "Siro Caramel": "ml", "Siro Vani": "ml",
    "Siro Bạc hà": "ml", "Siro Dâu": "ml", "Mật ong": "ml", "Sốt Chocolate": "kg",
    # Trà
    "Trà đen": "kg", "Trà lài": "kg", "Trà ô long": "kg", "Trà túi lọc": "gói",
    "Bột Matcha": "g", "Bột Cacao": "g", "Bột Frappe (Base)": "kg", 
    # Trái cây
    "Cam": "kg", "Chanh": "kg", "Dâu tây": "kg", "Đào (ngâm)": "hộp", 
    "Vải (ngâm)": "hộp", "Bơ": "kg", "Xoài": "kg",
    # Khác
    "Đá viên": "kg", "Nước lọc": "l", "Trân châu": "kg", "Bánh Croissant": "cái",
    "Bánh (khác)": "cái", "Ống hút": "hộp", "Ly (nhựa)": "cái",
}

def seed_data():
    """
    Thêm các nguyên liệu từ INGREDIENT_MAP vào CSDL.
    Sẽ bỏ qua nếu Tên Nguyên Liệu đã tồn tại.
    """
    print("Bắt đầu thêm dữ liệu nguyên liệu mẫu...")

    if cursor is None or conn is None:
        print("LỖI: Không thể kết nối CSDL.")
        return

    count_added = 0
    count_skipped = 0

    try:
        # Sắp xếp map theo tên để Mã NL (NL001, NL002...) được tạo ra
        # nhất quán theo thứ tự bảng chữ cái
        sorted_ingredients = sorted(INGREDIENT_MAP.items())

        for ten_nl, don_vi in sorted_ingredients:

            # 1. Kiểm tra xem TÊN NGUYÊN LIỆU đã tồn tại chưa
            check_query = "SELECT COUNT(*) FROM NguyenLieu WHERE TenNL = ?"
            if execute_scalar(check_query, (ten_nl,)) > 0:
                print(f"  [BỎ QUA] '{ten_nl}' đã tồn tại.")
                count_skipped += 1
                continue

            # 2. Tạo Mã NL mới
            # (Chúng ta truyền cursor vào vì helper này yêu cầu)
            manl = generate_next_manl(cursor)

            # 3. Thêm vào CSDL
            insert_query = "INSERT INTO NguyenLieu (MaNL, TenNL, DonVi, SoLuongTon) VALUES (?, ?, ?, 0)"
            if execute_query(insert_query, (manl, ten_nl, don_vi)):
                print(f"  [THÊM] {manl} - {ten_nl} ({don_vi})")
                count_added += 1
            else:
                print(f"  [LỖI] Không thể thêm {ten_nl}")

        print("\nHoàn tất!")
        print(f"Đã thêm mới: {count_added} nguyên liệu.")
        print(f"Đã bỏ qua (trùng lặp): {count_skipped} nguyên liệu.")

    except Exception as e:
        print(f"\nĐÃ XẢY RA LỖI: {e}")
    finally:
        if conn:
            conn.close()
            print("Đã đóng kết nối CSDL.")

if __name__ == "__main__":
    seed_data()