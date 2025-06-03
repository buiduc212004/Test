import os
import pandas as pd
import random
import time

# Đường dẫn thư mục lưu file CSV
OUTPUT_DIR = "data/keywords/"

# Đảm bảo thư mục tồn tại
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Danh sách từ khóa cơ bản
BASE_DIRECT_QUERY_KEYWORDS = [
    "hỏi", "tìm hiểu", "thông tin", "giải thích", "là gì", "tại sao", "như thế nào",
    "dsm-5", "tiêu chuẩn", "chẩn đoán", "rối loạn", "tâm lý", "triệu chứng", "điều trị",
    "phương pháp", "nguyên nhân", "hành vi", "phân loại", "yếu tố", "cách chữa",
    "đặc điểm", "hiệu quả", "liệu pháp", "thống kê", "nghiên cứu", "tác động",
    "phân tích", "đánh giá", "quy trình", "hỗ trợ"
]

BASE_EMOTION_KEYWORDS = [
    "buồn", "vui", "hạnh phúc", "lo âu", "lo lắng", "stress", "áp lực", "căng thẳng", "mệt mỏi",
    "tức giận", "sợ hãi", "hoang mang", "chán nản", "tự tin", "thất vọng", "hy vọng",
    "sợ sệt", "bồn chồn", "phấn khởi", "u uất", "trầm cảm", "hào hứng", "mất ngủ",
    "kích động", "thư giãn", "buồn chán", "tổn thương", "yêu đời", "cô đơn", "bối rối"
]

BASE_PERSONAL_KEYWORDS = [
    "tôi", "mình", "tớ", "chúng tôi", "bạn tôi", "gia đình tôi", "bản thân",
    "cảm giác của tôi", "tâm trạng tôi", "sức khỏe tôi", "cơ thể tôi", "cuộc sống tôi",
    "ngày của tôi", "tuần của tôi", "tháng của tôi", "năm của tôi", "hôm nay tôi",
    "đêm qua tôi", "sáng nay tôi", "hôm qua tôi", "tôi cảm thấy", "tôi nghĩ",
    "tôi muốn", "tôi cần", "tôi đang", "tôi đã"
]

# Danh sách tiền tố và hậu tố để mở rộng từ khóa
PREFIXES = ["cách", "vì", "tại", "hiểu", "tìm", "nghiên cứu", "phân tích", "đánh giá", "tổng hợp", "tra cứu"]
SUFFIXES = ["về", "của", "liên quan", "với", "đối với", "trong", "ngoài", "tại"]
EMOTION_MODIFIERS = ["rất", "hơi", "cực kỳ", "khá", "chút", "quá", "thật", "vô cùng", "hoàn toàn"]
PERSONAL_MODIFIERS = ["từng", "hay", "thường", "không", "luôn", "chưa", "vừa", "đã từng", "đang", "sẽ"]

def generate_keywords(base_keywords, num_keywords, prefixes=None, suffixes=None, modifiers=None):
    """Sinh từ khóa mở rộng với số lượng yêu cầu"""
    keywords = set(base_keywords)  # Bắt đầu với danh sách cơ bản
    attempts = 0
    max_attempts = num_keywords * 10  # Giới hạn số lần thử để tránh vòng lặp vô hạn

    print(f"Bắt đầu sinh {num_keywords} từ khóa...")
    start_time = time.time()

    while len(keywords) < num_keywords and attempts < max_attempts:
        base_word = random.choice(base_keywords)
        new_keyword = base_word

        # Tạo từ khóa mới với xác suất cao hơn
        if prefixes and random.random() > 0.3:
            new_keyword = f"{random.choice(prefixes)} {new_keyword}"
        if suffixes and random.random() > 0.3:
            new_keyword = f"{new_keyword} {random.choice(suffixes)}"
        if modifiers and random.random() > 0.3:
            new_keyword = f"{random.choice(modifiers)} {new_keyword}"

        # Thêm số ngẫu nhiên nếu cần để tăng tính đa dạng
        if random.random() > 0.7:
            new_keyword = f"{new_keyword} {random.randint(1, 100)}"

        keywords.add(new_keyword)
        attempts += 1

        # Thông báo tiến độ
        if attempts % 1000 == 0:
            print(f"Đã sinh {len(keywords)}/{num_keywords} từ khóa... ({attempts} lần thử)")

    if len(keywords) < num_keywords:
        print(f"Chỉ sinh được {len(keywords)} từ khóa sau {attempts} lần thử. Có thể cần thêm từ cơ bản.")
    
    print(f"Hoàn thành sinh từ khóa trong {time.time() - start_time:.2f} giây.")
    return list(keywords)[:num_keywords]

def save_to_csv(keywords, filename):
    """Lưu danh sách từ khóa vào file CSV"""
    df = pd.DataFrame(keywords, columns=["keyword"])
    df.to_csv(filename, index=False, encoding="utf-8")
    print(f"Đã lưu {len(keywords)} từ khóa vào {filename}")

def generate_all_keywords(num_keywords):
    """Sinh dữ liệu cho cả 3 file CSV"""
    # Sinh từ khóa cho direct_query_keywords
    print("Sinh từ khóa cho direct_query_keywords...")
    direct_query_keywords = generate_keywords(
        BASE_DIRECT_QUERY_KEYWORDS,
        num_keywords,
        prefixes=PREFIXES,
        suffixes=SUFFIXES
    )
    save_to_csv(direct_query_keywords, os.path.join(OUTPUT_DIR, "direct_query_keywords.csv"))

    # Sinh từ khóa cho emotion_keywords
    print("Sinh từ khóa cho emotion_keywords...")
    emotion_keywords = generate_keywords(
        BASE_EMOTION_KEYWORDS,
        num_keywords,
        modifiers=EMOTION_MODIFIERS
    )
    save_to_csv(emotion_keywords, os.path.join(OUTPUT_DIR, "emotion_keywords.csv"))

    # Sinh từ khóa cho personal_keywords
    print("Sinh từ khóa cho personal_keywords...")
    personal_keywords = generate_keywords(
        BASE_PERSONAL_KEYWORDS,
        num_keywords,
        modifiers=PERSONAL_MODIFIERS
    )
    save_to_csv(personal_keywords, os.path.join(OUTPUT_DIR, "personal_keywords.csv"))

if __name__ == "__main__":
    # Tham số: số lượng từ khóa cần sinh cho mỗi file
    num_keywords = 1000  # Có thể thay đổi số này
    generate_all_keywords(num_keywords)