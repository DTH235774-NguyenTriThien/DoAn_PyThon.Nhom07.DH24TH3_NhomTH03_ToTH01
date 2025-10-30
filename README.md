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

📁 Doan\_Python (root)
│
│
│
├── Doan\_Python/
│   │
│   ├── .gitignore
│   │
│   ├── config.ini
│   │
│   ├── project\_structure.txt
│   │
│   ├── README.md
│   │
│   ├── remember.ini
│   │
│   ├── requirements.txt
│   │
│   ├── app/
│   │   │
│   │   ├── db.py
│   │   │
│   │   ├── main.py
│   │   │
│   │   ├── remember.ini
│   │   │
│   │   ├── theme.py
│   │   │
│   │   ├── \_\_init\_\_.py
│   │   │
│   │   ├── assets/
│   │   │
│   │   ├── modules/
│   │   │   │
│   │   │   ├── customers.py
│   │   │   │
│   │   │   ├── drinks.py
│   │   │   │
│   │   │   ├── employees.py
│   │   │   │
│   │   │   ├── invoices.py
│   │   │   │
│   │   │   ├── reports.py
│   │   │   │
│   │   │   ├── \_\_init\_\_.py
│   │   │
│   │   ├── ui/
│   │   │   │
│   │   │   ├── login\_frame.py
│   │   │   │
│   │   │   ├── mainmenu\_frame.py
│   │   │   │
│   │   │   ├── \_\_init\_\_.py
│   │   │
│   │   ├── utils/
│   │   │   │
│   │   │   ├── export\_helper.py
│   │   │   │
│   │   │   ├── utils.py
│   │   │   │
│   │   │   ├── \_\_init\_\_.py
│   │   │   │
│   │   │   ├── employee/
│   │   │   │   │
│   │   │   │   ├── tab\_attendance.py
│   │   │   │   │
│   │   │   │   ├── tab\_info.py
│   │   │   │   │
│   │   │   │   ├── tab\_salary.py
│   │   │   │   │
│   │   │   │   ├── tab\_shift.py
│   │   
│   ├── database/
│   │   │
│   │   ├── AddEX.sql
│   │   │
│   │   ├── create\_db.sql
│   │   │
│   │   ├── Test\_QuanHe\_CacKhoa.sql
│   │   │
│   │   ├── ERD/
│   │   │   │
│   │   │   ├── ERD.png
│   │   
│   ├── docs/
│   │   │
│   │   ├── README\_Project.md
│   │   │
│   │   ├── Sprint0.md
│   │   │
│   │   ├── Sprint1.md
│   │   │
│   │   ├── Sprint2.md
│   │   
│   ├── exports/
│   │   │
│   │   ├── Bảng\_Lương\_20251027\_231718.xlsx
│   │
│   ├── scripts/
│   │   │
│   │   ├── create\_admin.py
│   │   │
│   │   ├── test\_mssql.py



