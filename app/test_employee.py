from employee_service import *

print("\n--- THÊM NHÂN VIÊN MỚI ---")
add_employee("NV003", "Nguyễn Văn Hòa", "Nam", "2001-10-01", "Pha chế", 6000000, "Đang làm")

print("\n--- DANH SÁCH NHÂN VIÊN ---")
list_employees()

print("\n--- CẬP NHẬT THÔNG TIN ---")
update_employee("NV003", chuc_vu="Quản lý quầy", luong=6500000)

print("\n--- DANH SÁCH NHÂN VIÊN SAU KHI CẬP NHẬT ---")
list_employees()

print("\n--- XÓA NHÂN VIÊN ---")
delete_employee("NV003")

print("\n--- DANH SÁCH NHÂN VIÊN SAU KHI XÓA ---")
list_employees()
