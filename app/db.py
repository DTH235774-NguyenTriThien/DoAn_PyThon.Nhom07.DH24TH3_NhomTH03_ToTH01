import pyodbc
import configparser
from tabulate import tabulate  # giúp hiển thị bảng gọn gàng, dễ đọc

# ----------------------------
# 1️⃣ Đọc file cấu hình config.ini
# ----------------------------
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

server = config['database']['server']
database = config['database']['database']
driver = config['database']['driver']
trusted = config['database'].get('trusted_connection', 'no')
timeout = config['database'].get('timeout', '30')

# ----------------------------
# 2️⃣ Kết nối đến SQL Server
# ----------------------------
try:
    if trusted.lower() == 'yes':
        # Kết nối bằng Windows Authentication
        conn_str = (
            f"DRIVER={driver};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"Trusted_Connection=yes;"
            f"timeout={timeout}"
        )
    else:
        # Kết nối bằng SQL Server Authentication
        username = config['database']['username']
        password = config['database']['password']
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
    print("✅ Kết nối SQL Server thành công!")

except Exception as e:
    print("❌ Lỗi kết nối SQL Server:", e)


# ----------------------------
# 3️⃣ Hàm: Lấy toàn bộ dữ liệu từ 1 bảng
# ----------------------------
def fetch_all(table_name):
    """
    Truy vấn và hiển thị toàn bộ dữ liệu từ 1 bảng trong database.
    Dữ liệu được hiển thị có định dạng dễ đọc, hỗ trợ tiếng Việt.
    """
    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        if not rows:
            print(f"⚠️ Không có dữ liệu trong bảng '{table_name}'")
            return

        headers = [desc[0] for desc in cursor.description]

        # Làm sạch dữ liệu để hiển thị
        formatted_data = []
        for row in rows:
            cleaned_row = []
            for item in row:
                if item is None:
                    cleaned_row.append("")
                elif hasattr(item, 'strftime'):  # định dạng ngày tháng
                    cleaned_row.append(item.strftime('%d/%m/%Y'))
                elif hasattr(item, 'quantize'):  # xử lý Decimal
                    cleaned_row.append(f"{int(item):,}")
                else:
                    cleaned_row.append(str(item).strip())
            formatted_data.append(cleaned_row)

        print(f"\n📋 Dữ liệu trong bảng: {table_name}")
        print(tabulate(formatted_data, headers=headers, tablefmt="fancy_grid", stralign="center"))

    except Exception as e:
        print(f"❌ Lỗi khi truy vấn bảng '{table_name}':", e)


# ----------------------------
# 4️⃣ Hàm: Đóng kết nối
# ----------------------------
def close_connection():
    """Đóng kết nối đến SQL Server"""
    try:
        cursor.close()
        conn.close()
        print("🔒 Đã đóng kết nối SQL Server.")
    except Exception as e:
        print("⚠️ Lỗi khi đóng kết nối:", e)


# ----------------------------
# 5️⃣ Test nhanh khi chạy file trực tiếp
# ----------------------------
if __name__ == "__main__":
    fetch_all("NhanVien")
    close_connection()
