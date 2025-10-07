# \# ☕ Phần mềm Quản lý Quán Cà Phê  

# Đồ án môn học: Chuyên đề Python

# 

# ---

# 

# 🧩 Giới thiệu dự án

# 

# Phần mềm "Quản lý Quán Cà Phê" được xây dựng bằng ngôn ngữ \*\*Python (Tkinter)\*\* và sử dụng \*\*SQL Server 2022\*\* để quản lý dữ liệu.  

# Mục tiêu của ứng dụng là \*\*giúp chủ quán và nhân viên vận hành công việc hiệu quả hơn\*\*, bao gồm:

# 

# \- Quản lý \*\*nhân viên\*\* (thông tin, chấm công, lương)

# \- Quản lý \*\*sản phẩm\*\* (cà phê, nước uống, đồ ăn nhẹ)

# \- Quản lý \*\*hóa đơn\*\* và \*\*bán hàng\*\*

# \- Quản lý \*\*ca làm việc\*\*

# \- Theo dõi \*\*doanh thu\*\*, \*\*báo cáo\*\*, và \*\*thống kê\*\*

# 

# Ứng dụng hướng đến sự \*\*thực tế, dễ sử dụng\*\* và \*\*thân thiện với người dùng Việt Nam\*\*.

# 

# ---

# 

# 🏗️ Công nghệ sử dụng

# 

# | Thành phần | Mô tả |

# |-------------|--------|

# | \*\*Ngôn ngữ chính\*\* | Python 3.11 |

# | \*\*Thư viện GUI\*\* | Tkinter |

# | \*\*Cơ sở dữ liệu\*\* | Microsoft SQL Server 2022 |

# | \*\*Thư viện kết nối DB\*\* | pyodbc |

# | \*\*Công cụ quản lý\*\* | Git + GitHub |

# | \*\*IDE khuyến nghị\*\* | Visual Studio Code |

# 

# ---

# 

# \## 🗂️ Cấu trúc thư mục dự án

# 

# ```bash

# Doan\_Python/

# │

# ├── app/                      # (Sẽ được tạo trong Sprint 1 - chứa source code chính)

# │   ├── ui/                   # Giao diện Tkinter

# │   ├── database/             # Mô-đun kết nối và thao tác SQL

# │   ├── models/               # Lớp đại diện cho thực thể (Nhân viên, Sản phẩm, Hóa đơn, ...)

# │   ├── controllers/          # Xử lý nghiệp vụ (quản lý bán hàng, tính lương, ...)

# │   └── main.py               # Điểm khởi chạy ứng dụng

# │

# ├── create\_db.sql             # Script tạo cơ sở dữ liệu SQL Server

# ├── test\_mssql.py             # File kiểm tra kết nối SQL Server

# ├── config.ini                # Cấu hình kết nối (local, không push lên GitHub)

# ├── config.ini.example        # Mẫu cấu hình (dành cho repo public)

# ├── requirements.txt          # Danh sách thư viện Python

# ├── .gitignore                # Bỏ qua file nhạy cảm (\_\_pycache\_\_, config.ini, venv, ...)

# └── README.md                 # Tài liệu mô tả dự án



