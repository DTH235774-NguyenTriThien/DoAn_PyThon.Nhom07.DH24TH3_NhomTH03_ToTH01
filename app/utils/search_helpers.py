# app/utils/search_helpers.py
import unicodedata

def normalize_text(text: str) -> str:
    """
    Chuẩn hóa văn bản:
    1. Chuyển sang chữ thường.
    2. Loại bỏ dấu (ví dụ: "Họ tên" -> "ho ten").
    3. Loại bỏ khoảng trắng thừa.
    """
    if not isinstance(text, str):
        text = str(text)
        
    text = text.lower().strip()
    
    # Loại bỏ dấu (convert to ASCII compatible)
    try:
        text = str(unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8'))
    except Exception:
        pass # Bỏ qua nếu có lỗi
        
    return text

def filter_data_client_side(all_data: list[dict], keyword: str) -> list[dict]:
    """
    Helper tìm kiếm "mạnh mẽ" phía client.
    - all_data: Danh sách đầy đủ (cache) dạng list[dict].
    - keyword: Từ khóa người dùng gõ.
    
    Trả về: Danh sách list[dict] đã được lọc.
    """
    
    # 1. Chuẩn hóa từ khóa tìm kiếm
    normalized_keyword = normalize_text(keyword)
    
    if not normalized_keyword:
        return all_data # Trả về tất cả nếu không có từ khóa

    filtered_list = []
    
    # 2. Lặp qua từng dòng dữ liệu trong cache
    for row_dict in all_data:
        match_found = False
        
        # 3. Lặp qua từng giá trị (cột) trong dòng
        for column_value in row_dict.values():
            
            if column_value is None:
                continue
                
            # 4. Chuẩn hóa giá trị của cột
            normalized_value = normalize_text(str(column_value))
            
            # 5. Kiểm tra
            if normalized_keyword in normalized_value:
                match_found = True
                break # Đã tìm thấy, không cần check các cột khác
        
        if match_found:
            filtered_list.append(row_dict)
            
    return filtered_list