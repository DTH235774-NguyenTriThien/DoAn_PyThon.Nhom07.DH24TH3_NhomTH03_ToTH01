import pyodbc

try:
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=QL_CaPhe;"
        "UID=qluser;"
        "PWD=thien_dth235774;"
        "Trusted_Connection=no;"
    )
    print("✅ Kết nối SQL Server thành công!")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM NhanVien;")
    count = cursor.fetchone()[0]
    print(f"Tổng số nhân viên: {count}")
    conn.close()
except Exception as e:
    print("❌ Lỗi kết nối:", e)