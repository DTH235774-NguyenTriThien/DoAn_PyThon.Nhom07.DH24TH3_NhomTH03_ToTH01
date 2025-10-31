# scripts/seed_ingredients.py
import sys
import os

# --- Thêm thư mục gốc vào system path ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from app.db import execute_query, execute_scalar, conn, cursor
    from app.utils.id_helpers import generate_next_manl
except ImportError as e:
    print(f"LỖI: Không thể import 'app.db' hoặc 'id_helpers'. Lỗi: {e}")
    sys.exit(1)

# =========================================================
# SỬA 1: TÁCH LÀM 2 MAP VÀ CHUẨN HÓA ĐƠN VỊ
# =========================================================

# MAP 1: THỰC PHẨM (Dùng cho Công thức)
# (Đã chuẩn hóa về 'g' và 'ml')
FOOD_MAP = {
    # Cà phê
    "Cà phê hạt": "g",
    "Cà phê bột": "g",
    # Sữa
    "Sữa đặc": "ml",
    "Sữa tươi": "ml",
    "Kem béo (Rich)": "ml",
    "Kem (Whipping Cream)": "ml",
    "Sữa chua": "g",
    # Đường / Siro
    "Đường cát": "g",
    "Đường nước": "ml",
    "Siro Caramel": "ml",
    "Siro Vani": "ml",
    "Siro Bạc hà": "ml",
    "Siro Dâu": "ml",
    "Mật ong": "ml",
    "Sốt Chocolate": "g",
    # Trà
    "Trà đen": "g",
    "Trà lài": "g",
    "Trà ô long": "g",
    "Bột Matcha": "g",
    "Bột Cacao": "g",
    "Bột Frappe (Base)": "g",
    # Trái cây
    "Cam": "quả",
    "Chanh": "quả",
    "Dâu tây (tươi)": "g",
    "Đào (ngâm)": "hộp",
    "Vải (ngâm)": "hộp",
    # Khác
    "Trân châu": "g",
    "Đá viên": "kg", # Đá là ngoại lệ vì dùng nhiều
}

# MAP 2: VẬT TƯ (Không dùng cho Công thức)
SUPPLY_MAP = {
    "Cà phê (phin giấy)": "gói",
    "Trà túi lọc": "gói",
    "Bánh Croissant": "cái",
    "Bánh Tiramisu": "cái",
    "Ống hút": "hộp",
    "Ly (nhựa)": "cái",
    "Ly (giấy)": "cái",
    "Túi (mang đi)": "cái",
}

def seed_data(ingredient_map, type_name):
    """Hàm chung để seed dữ liệu từ một map"""
    count_added = 0
    count_skipped = 0
    
    sorted_ingredients = sorted(ingredient_map.items())
    
    for ten_nl, don_vi in sorted_ingredients:
        check_query = "SELECT COUNT(*) FROM NguyenLieu WHERE TenNL = ?"
        if execute_scalar(check_query, (ten_nl,)) > 0:
            print(f"  [BỎ QUA {type_name}] '{ten_nl}' đã tồn tại.")
            count_skipped += 1
            continue
        
        manl = generate_next_manl(cursor)
        
        insert_query = "INSERT INTO NguyenLieu (MaNL, TenNL, DonVi, SoLuongTon) VALUES (?, ?, ?, 0)"
        if execute_query(insert_query, (manl, ten_nl, don_vi)):
            print(f"  [THÊM {type_name}] {manl} - {ten_nl} ({don_vi})")
            count_added += 1
        else:
            print(f"  [LỖI] Không thể thêm {ten_nl}")
    
    return count_added, count_skipped

def main_seed():
    print("Bắt đầu thêm/cập nhật dữ liệu nguyên liệu mẫu...")
    if cursor is None or conn is None:
        print("LỖI: Không thể kết nối CSDL.")
        return

    try:
        # Seed Thực phẩm
        added_food, skipped_food = seed_data(FOOD_MAP, "Thực phẩm")
        
        # Seed Vật tư
        added_supply, skipped_supply = seed_data(SUPPLY_MAP, "Vật tư")
        
        print("\nHoàn tất!")
        print(f"Tổng Thực phẩm: {added_food} mới / {skipped_food} bỏ qua.")
        print(f"Tổng Vật tư: {added_supply} mới / {skipped_supply} bỏ qua.")

    except Exception as e:
        print(f"\nĐÃ XẢY RA LỖI: {e}")
    finally:
        if conn:
            conn.close()
            print("Đã đóng kết nối CSDL.")

if __name__ == "__main__":
    main_seed()