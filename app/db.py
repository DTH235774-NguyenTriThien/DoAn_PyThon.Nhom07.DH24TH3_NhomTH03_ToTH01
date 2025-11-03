# app/db.py
import pyodbc
import configparser
from tkinter import messagebox
import re 
from app.utils.utils import resource_path

# ==============================
# 🔧 Đọc cấu hình từ config.ini
# ==============================
config = configparser.ConfigParser()
config.read(resource_path("config.ini"), encoding="utf-8-sig")

server = config["database"]["server"].strip()
database = config["database"]["database"].strip()
driver = config["database"]["driver"].strip()
trusted = config["database"].get("trusted_connection", "no").strip()
timeout = config["database"].get("timeout", "30").strip()
username = config["database"].get("username", "")
password = config["database"].get("password", "")


# ==============================
# 🔧 Đọc cấu hình từ config.ini
# ==============================
config = configparser.ConfigParser()
config.read(resource_path("config.ini"), encoding="utf-8-sig")

server = config["database"]["server"].strip()
database = config["database"]["database"].strip()
driver = config["database"]["driver"].strip()  # {ODBC Driver 17 for SQL Server}
trusted = config["database"].get("trusted_connection", "no").strip()
timeout = config["database"].get("timeout", "30").strip()
username = config["database"].get("username", "").strip()
password = config["database"].get("password", "").strip()

# ==============================
# 🔗 Kết nối SQL Server
# ==============================
conn = None
cursor = None

try:
    if trusted.lower() == "yes":
        conn_str = (
            f"DRIVER={driver};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"Trusted_Connection=yes;"
            f"Connection Timeout={timeout};"
        )
    else:
        conn_str = (
            f"DRIVER={driver};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Encrypt=no;"
            f"TrustServerCertificate=yes;"
            f"Connection Timeout={timeout};"
        )

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

except Exception as e:
    messagebox.showerror("Lỗi kết nối SQL Server", f"Không thể kết nối cơ sở dữ liệu:\n{e}")
    conn, cursor = None, None


# ==============================
# 📘 Các hàm tiện ích thao tác DB
# ==============================

def fetch_all(table_name):
    """Truy vấn toàn bộ dữ liệu từ 1 bảng (trả list[dict])."""
    if cursor is None:
        messagebox.showwarning("Cảnh báo", "Chưa kết nối SQL Server.")
        return []

    # Bắt buộc: Kiểm tra tên bảng để chống SQL Injection
    if not re.match(r"^[a-zA-Z0-9_]+$", table_name):
        messagebox.showerror("Lỗi bảo mật", f"Tên bảng không hợp lệ: {table_name}")
        return []

    try:
        cursor.execute(f"SELECT * FROM {table_name}") 
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        messagebox.showerror("Lỗi truy vấn", f"Không thể lấy dữ liệu từ {table_name}:\n{e}")
        return []


def fetch_one(table_name, where_clause=None, params=()):
    """Truy vấn 1 dòng dữ liệu (trả dict hoặc None)."""
    if cursor is None:
        messagebox.showwarning("Cảnh báo", "Chưa kết nối SQL Server.")
        return None

    # Kiểm tra tên bảng
    if not re.match(r"^[a-zA-Z0-9_]+$", table_name):
        messagebox.showerror("Lỗi bảo mật", f"Tên bảng không hợp lệ: {table_name}")
        return None

    try:
        query = f"SELECT * FROM {table_name}"
        if where_clause:
            # where_clause phải là "MaNV = ? AND Role = ?"
            query += f" WHERE {where_clause}" 
        
        # Truy vấn đã được tham số hóa
        cursor.execute(query, params) 
        row = cursor.fetchone()
        
        if row:
            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        messagebox.showerror("Lỗi truy vấn", f"Không thể lấy dữ liệu từ {table_name}:\n{e}")
        return None


def fetch_query(query, params=()):
    """Thực thi truy vấn SELECT bất kỳ (trả list[dict])."""
    if cursor is None:
        messagebox.showwarning("Cảnh báo", "Chưa kết nối SQL Server.")
        return []

    try:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        messagebox.showerror("Lỗi SQL", f"Không thể thực thi truy vấn:\n{e}\n\nQuery:\n{query}")
        return []


def execute_query(query, params=()):
    """Thực thi truy vấn ghi (INSERT, UPDATE, DELETE)."""
    if cursor is None:
        messagebox.showwarning("Cảnh báo", "Chưa kết nối SQL Server.")
        return False

    try:
        cursor.execute(query, params)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Lỗi SQL", f"Không thể thực thi truy vấn:\n{e}\n\nQuery:\n{query}")
        return False


def execute_scalar(query, params=()):
    """Thực thi truy vấn trả về 1 giá trị đơn (VD: COUNT, SUM, MAX...)."""
    if cursor is None:
        messagebox.showwarning("Cảnh báo", "Chưa kết nối SQL Server.")
        return None

    try:
        cursor.execute(query, params)
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        messagebox.showerror("Lỗi SQL", f"Không thể thực thi truy vấn scalar:\n{e}\n\nQuery:\n{query}")
        return None


def count_query(table_name, where_clause=None, params=()):
    """Đếm số dòng của 1 bảng (có thể có điều kiện WHERE)."""
    
    # Kiểm tra tên bảng
    if not re.match(r"^[a-zA-Z0-9_]+$", table_name):
        messagebox.showerror("Lỗi bảo mật", f"Tên bảng không hợp lệ: {table_name}")
        return None
        
    sql = f"SELECT COUNT(*) FROM {table_name}"
    if where_clause:
        sql += f" WHERE {where_clause}" # Ví dụ: "MaNV = ?"
        
    # Gọi hàm `execute_scalar` (an toàn)
    return execute_scalar(sql, params)


def close_db_connection():
    """Đóng kết nối đến SQL Server (được gọi bởi main.py)."""
    global conn, cursor
    try:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    except Exception as e:
        # Bỏ qua lỗi khi đóng CSDL (ví dụ: kết nối đã mất)
        pass 
    finally:
        cursor = None
        conn = None