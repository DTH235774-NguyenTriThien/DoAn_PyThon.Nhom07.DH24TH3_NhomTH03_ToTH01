# scripts/seed_recipes_for_existing_products.py
import sys
import os
import tkinter as tk
from tkinter import messagebox
from decimal import Decimal

# --- Cấu hình Path (Giống script trước) ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

try:
    from app import db
    from app.db import fetch_query, execute_query
except ImportError:
    print("Lỗi: Không thể import app.db.")
    sys.exit(1)

# --- BIẾN TOÀN CỤC ĐỂ LƯU BẢN ĐỒ ---
ingredient_map = {} # {'Cà phê bột': 'NL001', ...}
product_map = {}    # {'Cà Phê Sữa': 'SP002', ...}

# =========================================================
# DỮ LIỆU SEEDING CÔNG THỨC
# (Nó sẽ tự động tìm 'MaSP' và 'MaNL' dựa trên tên)
# =========================================================
SEED_RECIPES = {
    # Tên sản phẩm (phải khớp 100% với tên trong CSDL của bạn)
    "Cà Phê Sữa": [ 
        ("Cà phê bột", 25), ("Sữa đặc", 30), ("Đá viên", 150) 
    ],
    "Cà Phê Đen": [ 
        ("Cà phê bột", 25), ("Đường nước", 10), ("Đá viên", 150) 
    ],
    "Bạc Xỉu": [ 
        ("Cà phê bột", 15), ("Sữa đặc", 40), ("Sữa tươi", 20), ("Đá viên", 150) 
    ],
    "Espresso": [ 
        ("Cà phê hạt", 18) # (Giả sử máy xay từ hạt)
    ],
    "Cappuccino": [
        ("Cà phê hạt", 18), ("Sữa tươi", 100)
    ],
    "Latte": [
        ("Cà phê hạt", 18), ("Sữa tươi", 150)
    ],
    "Cà Phê Cốt Dừa": [ # Giả sử 'Bột Frappe (Base)' là bột cốt dừa
        ("Cà phê bột", 20), ("Bột Frappe (Base)", 30), ("Sữa đặc", 20), ("Đá viên", 150)
    ],
    
    # Trà & Trà sữa
    "Trà Sữa Mochi": [ 
        ("Trà đen", 5), ("Bột Frappe (Base)", 10), ("Sữa đặc", 20), ("Trân châu", 30), ("Đá viên", 150) 
    ],
    "Trà Đào Cam Sả": [ 
        ("Trà túi lọc", 1), ("Đào (ngâm)", 50), ("Cam", 20), ("Đường nước", 15), ("Đá viên", 150) 
    ],
    "Trà Vải": [ 
        ("Trà lài", 5), ("Vải (ngâm)", 50), ("Đường nước", 15), ("Đá viên", 150) 
    ],
    "Trà Sen": [
        ("Trà ô long", 5), ("Kem béo (Rich)", 20), ("Đường nước", 10), ("Đá viên", 150)
    ],
    "Trà Gừng Mật Ong": [
        ("Trà túi lọc", 1), ("Mật ong", 20) # (Giả sử không dùng đá)
    ],
    "Trà Ô Long": [
        ("Trà ô long", 5), ("Đường nước", 10), ("Đá viên", 150)
    ],

    # Nước ép & Sinh tố
    "Sinh tố Bơ": [ 
        ("Bơ", 100), ("Sữa đặc", 30), ("Sữa tươi", 20), ("Đá viên", 150) 
    ],
    "Sinh tố Xoài": [ 
        ("Xoài", 100), ("Sữa đặc", 20), ("Sữa tươi", 20), ("Đá viên", 150) 
    ],
    "Nước Cam Ép": [ 
        ("Cam", 250), ("Đường nước", 10), ("Đá viên", 100) 
    ],
    "Nước Chanh": [
        ("Chanh", 50), ("Đường nước", 20), ("Đá viên", 150)
    ],
    
    # Đá xay
    "Cookie Đá Xay": [
        ("Bột Frappe (Base)", 20), ("Sữa tươi", 50), ("Sốt Chocolate", 10), ("Đá viên", 150)
    ]
    
    # (Bánh và Hạt hướng dương tự động được bỏ qua vì không có trong danh sách này)
}


def load_maps():
    """
    Bước 1: Đọc 2 bảng NguyenLieu và SanPham để tạo bản đồ tra cứu
    """
    global ingredient_map, product_map
    try:
        # 1. Tải Nguyên liệu
        rows_ing = fetch_query("SELECT MaNL, TenNL FROM NguyenLieu")
        if not rows_ing:
            print("Lỗi: Bảng NguyenLieu của bạn đang trống. (Hãy chạy script 'seed_inventory.py' trước)")
            return False
        ingredient_map = {r['TenNL'].strip(): r['MaNL'].strip() for r in rows_ing}
        print(f"Đã tải {len(ingredient_map)} nguyên liệu.")

        # 2. Tải Sản phẩm
        rows_prod = fetch_query("SELECT MaSP, TenSP FROM SanPham")
        if not rows_prod:
            print("Lỗi: Bảng SanPham của bạn đang trống.")
            return False
        product_map = {r['TenSP'].strip(): r['MaSP'].strip() for r in rows_prod}
        print(f"Đã tải {len(product_map)} sản phẩm (từ CSDL của bạn).")
        
        return True
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi tải bản đồ: {e}")
        return False

def run_seeding():
    """
    Bước 2 & 3: Xóa CÔNG THỨC cũ và Chèn CÔNG THỨC mới
    """
    
    root = tk.Tk()
    root.withdraw() 
    
    if not messagebox.askyesno("⚠️ Cảnh báo",
        "Script này sẽ XÓA SẠCH tất cả dữ liệu trong bảng 'CongThuc' (công thức)\n"
        "Sau đó, nó sẽ tự động tạo công thức mới cho các sản phẩm tìm thấy trong bảng 'SanPham'.\n\n"
        "Bảng 'SanPham' (21 món) của bạn sẽ KHÔNG BỊ XÓA.\n\n"
        "Bạn có chắc chắn muốn tiếp tục?"):
        print("Đã hủy bỏ seeding.")
        root.destroy()
        return

    recipes_added = 0
    warnings = []

    try:
        # 1. Xóa dữ liệu CÔNG THỨC cũ
        print("Đang xóa CÔNG THỨC cũ...")
        execute_query("DELETE FROM CongThuc")
        
        print("Đã xóa công thức cũ. Bắt đầu chèn dữ liệu mới...")

        # 2. Lặp qua dữ liệu CÔNG THỨC MẪU
        for product_name, recipe_items in SEED_RECIPES.items():
            
            # 3. Tra cứu MaSP (Mã Sản phẩm)
            masp = product_map.get(product_name)
            
            if not masp:
                warnings.append(f"Bỏ qua: Không tìm thấy sản phẩm '{product_name}' trong bảng SanPham của bạn.")
                continue

            # 4. Lặp qua từng nguyên liệu trong công thức
            for (ing_name, qty) in recipe_items:
                
                # 5. Tra cứu MaNL (Mã Nguyên liệu)
                manl = ingredient_map.get(ing_name)
                
                if manl:
                    # 6. Chèn vào CSDL
                    query_ct = "INSERT INTO CongThuc (MaSP, MaNL, SoLuong) VALUES (?, ?, ?)"
                    if execute_query(query_ct, (masp, manl, qty)):
                        recipes_added += 1
                    else:
                        warnings.append(f"Lỗi khi thêm CT cho {product_name}: {ing_name}")
                else:
                    # Nếu không tìm thấy NL, ghi cảnh báo
                    warnings.append(f"CẢNH BÁO: Không tìm thấy NL '{ing_name}' trong bảng NguyenLieu. (Bỏ qua cho món {product_name})")

        # Hoàn tất
        if not warnings:
            messagebox.showinfo("✅ Thành công",
                                f"Seeding CÔNG THỨC thành công!\n\n"
                                f"Đã thêm: {recipes_added} chi tiết công thức mới.")
            print("Seeding hoàn tất.")
        else:
            messagebox.showwarning("Hoàn tất (Có cảnh báo)",
                                   f"Seeding hoàn tất với một số cảnh báo:\n\n"
                                   f"Đã thêm: {recipes_added} chi tiết công thức mới.\n\n"
                                   f"Cảnh báo (ví dụ):\n- {warnings[0]}\n"
                                   f"(Xem thêm ở terminal)")
            print("\n--- CẢNH BÁO SEEDING ---")
            for w in warnings:
                print(f"- {w}")

    except Exception as e:
        db.conn.rollback() 
        messagebox.showerror("Lỗi nghiêm trọng", f"Đã xảy ra lỗi:\n{e}")
    finally:
        db.close_db_connection()
        root.destroy()
        print("Đã đóng kết nối CSDL.")

# --- HÀM CHẠY CHÍNH ---
if __name__ == "__main__":
    if db.conn:
        if load_maps():
            run_seeding()
        else:
            messagebox.showerror("Lỗi", "Không thể tải bản đồ (SanPham/NguyenLieu) từ CSDL. Hủy bỏ seeding.")
            db.close_db_connection()
    else:
        print("Không thể kết nối CSDL.")