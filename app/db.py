import pyodbc
import configparser
from tkinter import messagebox

# ==============================
# 🔧 Đọc cấu hình từ config.ini
# ==============================
config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")

server = config["database"]["server"]
database = config["database"]["database"]
driver = config["database"]["driver"]
trusted = config["database"].get("trusted_connection", "no")
timeout = config["database"].get("timeout", "30")

username = config["database"].get("username", "")
password = config["database"].get("password", "")

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
            f"timeout={timeout}"
        )
    else:
        conn_str = (
            f"DRIVER={driver};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"timeout={timeout}"
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
    """Truy vấn toàn bộ dữ liệu từ 1 bảng."""
    if cursor is None:
        messagebox.showwarning("Cảnh báo", "Chưa kết nối SQL Server.")
        return []

    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        messagebox.showerror("Lỗi truy vấn", f"Không thể lấy dữ liệu từ {table_name}:\n{e}")
        return []


def fetch_one(table_name, condition=None):
    """Truy vấn 1 dòng dữ liệu từ bảng (có điều kiện WHERE tùy chọn)."""
    if cursor is None:
        messagebox.showwarning("Cảnh báo", "Chưa kết nối SQL Server.")
        return None

    try:
        query = f"SELECT * FROM {table_name}"
        if condition:
            query += f" WHERE {condition}"
        cursor.execute(query)
        return cursor.fetchone()
    except Exception as e:
        messagebox.showerror("Lỗi truy vấn", f"Không thể lấy dữ liệu từ {table_name}:\n{e}")
        return None


def execute_query(query, params=()):
    """Thực thi truy vấn bất kỳ (INSERT, UPDATE, DELETE)."""
    if cursor is None:
        messagebox.showwarning("Cảnh báo", "Chưa kết nối SQL Server.")
        return False

    try:
        cursor.execute(query, params)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Lỗi SQL", f"Không thể thực thi truy vấn:\n{e}")
        return False


def close_connection():
    """Đóng kết nối đến SQL Server."""
    try:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    except Exception:
        pass
