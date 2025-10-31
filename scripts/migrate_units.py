# scripts/migrate_units.py
import sys
import os
from decimal import Decimal

# --- Thêm thư mục gốc vào system path ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.db import fetch_query, execute_query, conn, cursor
except ImportError as e:
    print(f"LỖI: Không thể import 'app.db'. Lỗi: {e}")
    sys.exit(1)

# =========================================================
# SỬA 1: CẬP NHẬT MAP CHO CHÍNH XÁC VỚI DỮ LIỆU CỦA BẠN
# =========================================================
CONVERSION_MAP = {
    # (Tên NL, Đơn vị CŨ): (Đơn vị MỚI, Hệ số nhân)
    
    # Các mục bị sai tên trong CSDL của bạn
    ('Đường', 'kg'): ('g', 1000),
    ('Muối', 'kg'): ('g', 1000),
    ('Bơ', 'kg'): ('g', 1000),
    ('Cam', 'kg'): ('g', 1000),    # Chuẩn hóa Cam(kg) -> Cam(g)
    ('Chanh', 'kg'): ('g', 1000),  # Chuẩn hóa Chanh(kg) -> Chanh(g)
    ('Dâu tây', 'kg'): ('g', 1000),# Chuẩn hóa Dâu tây(kg) -> Dâu tây(g)
    ('Đường phèn', 'kg'): ('g', 1000),
    ('Xoài', 'kg'): ('g', 1000),
    ('Nước lọc', 'l'): ('ml', 1000),

    # Các mục chuẩn (phòng hờ nếu bạn có)
    ('Cà phê hạt', 'kg'):    ('g', 1000),
    ('Cà phê bột', 'kg'):    ('g', 1000),
    ('Sữa đặc', 'lon'):      ('ml', 380), # Giả định 1 lon = 380ml
    ('Sữa tươi', 'l'):       ('ml', 1000),
    ('Sữa chua', 'kg'):      ('g', 1000),
    ('Sốt Chocolate', 'kg'): ('g', 1000),
    ('Trà đen', 'kg'):       ('g', 1000),
    ('Trà lài', 'kg'):       ('g', 1000),
    ('Trà ô long', 'kg'):    ('g', 1000),
    ('Trân châu', 'kg'):     ('g', 1000),
}

def migrate_units():
    """
    Quét và chuẩn hóa CSDL sang đơn vị 'g' và 'ml'.
    """
    print("Bắt đầu quét và chuẩn hóa đơn vị nguyên liệu (Bản vá V2)...")
    
    if cursor is None or conn is None:
        print("LỖI: Không thể kết nối CSDL.")
        return

    try:
        all_ingredients = fetch_query("SELECT MaNL, TenNL, DonVi, SoLuongTon FROM NguyenLieu")
        count_updated = 0
        
        for item in all_ingredients:
            manl = item['MaNL']
            tennl = item['TenNL']
            donvi_cu = item['DonVi']
            tonkho_cu = Decimal(item['SoLuongTon'] or 0)
            key = (tennl, donvi_cu)
            
            if key in CONVERSION_MAP:
                donvi_moi, he_so = CONVERSION_MAP[key]
                tonkho_moi = tonkho_cu * Decimal(he_so)
                
                print(f"  [PHÁT HIỆN] '{tennl}' ({donvi_cu}). Chuẩn hóa sang '{donvi_moi}' (x{he_so})...")
                
                # 1. Cập nhật NGUYENLIEU
                execute_query(
                    "UPDATE NguyenLieu SET DonVi = ?, SoLuongTon = ? WHERE MaNL = ?",
                    (donvi_moi, tonkho_moi, manl)
                )
                
                # 2. Cập nhật CONGTHUC (nếu có)
                execute_query(
                    "UPDATE CongThuc SET SoLuong = SoLuong * ? WHERE MaNL = ?",
                    (he_so, manl)
                )
                
                # 3. Ghi lại lịch sử
                execute_query(
                    "INSERT INTO InventoryMovements (MaNL, ChangeQty, MovementType) VALUES (?, 0, 'adjust')",
                    (manl,)
                )
                count_updated += 1
            else:
                pass

        print(f"\nHoàn tất! Đã chuẩn hóa {count_updated} nguyên liệu.")
        
    except Exception as e:
        print(f"\nĐÃ XẢY RA LỖI: {e}")
        if conn:
            conn.rollback() 
            print("Đã rollback giao dịch.")
    finally:
        if conn:
            conn.close()
            print("Đã đóng kết nối CSDL.")

if __name__ == "__main__":
    migrate_units()