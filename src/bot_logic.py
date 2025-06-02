# src/bot_logic.py
import streamlit as st
from src.conversation_engine import ConversationEngine
from src.global_settings import CHAT_HISTORY_FILE
from datetime import datetime

class BotLogic:
    def __init__(self, username: str = "demo_user", user_info: dict = {"name": "Người dùng Demo", "age": 25}):
        # Khởi tạo ConversationEngine với username và user_info mặc định
        self.engine = ConversationEngine(username=username, user_info=user_info)

    def process_input(self, prompt):
        if not prompt.strip():
            return {
                "question": None,
                "options": [],
                "response": (
                    "Vui lòng nhập câu hỏi hoặc chia sẻ cảm xúc để tôi hỗ trợ!\n\n"
                    "**Ví dụ câu hỏi trực tiếp**: 'Tiêu chuẩn chẩn đoán rối loạn lo âu theo DSM-5 là gì?'\n"
                    "**Ví dụ yêu cầu câu hỏi trắc nghiệm**: 'Tôi đang cảm thấy buồn, hãy tạo câu hỏi tâm lý cho tôi.'"
                )
            }
        
        prompt_lower = prompt.lower()
        direct_query_keywords = [
            "hỏi", "tìm hiểu", "thông tin", "giải thích", "là gì", "tại sao", "như thế nào",
            "dsm-5", "tiêu chuẩn", "chẩn đoán", "rối loạn", "tâm lý", "triệu chứng", "điều trị",
            "phương pháp", "nguyên nhân", "hành vi", "phân loại", "yếu tố", "cách chữa",
            "đặc điểm", "hiệu quả", "liệu pháp", "thống kê", "nghiên cứu", "tác động",
            "phân tích", "đánh giá", "quy trình", "hỗ trợ"
        ]
        emotion_keywords = [
            "buồn", "vui", "hạnh phúc", "lo âu", "lo lắng", "stress", "áp lực", "căng thẳng", "mệt mỏi",
            "tức giận", "sợ hãi", "hoang mang", "chán nản", "tự tin", "thất vọng", "hy vọng",
            "sợ sệt", "bồn chồn", "phấn khởi", "u uất", "trầm cảm", "hào hứng", "mất ngủ",
            "kích động", "thư giãn", "buồn chán", "tổn thương", "yêu đời"
        ]
        personal_keywords = [
            "tôi", "mình", "tớ", "chúng tôi", "bạn tôi", "gia đình tôi", "bản thân",
            "cảm giác của tôi", "tâm trạng tôi", "sức khỏe tôi", "cơ thể tôi", "cuộc sống tôi",
            "ngày của tôi", "tuần của tôi", "tháng của tôi", "năm của tôi", "hôm nay tôi",
            "đêm qua tôi", "sáng nay tôi", "hôm qua tôi", "tôi cảm thấy", "tôi nghĩ",
            "tôi muốn", "tôi cần", "tôi đang", "tôi đã"
        ]
        
        # Kiểm tra truy vấn DSM-5: trả lời ngay mà không sinh câu hỏi trắc nghiệm
        if any(keyword in prompt_lower for keyword in direct_query_keywords):
            return self.engine.process_direct_query(prompt)

        # Kiểm tra truy vấn liên quan đến người dùng (có từ khóa cá nhân và cảm xúc)
        if any(keyword in prompt_lower for keyword in personal_keywords):
            if any(keyword in prompt_lower for keyword in emotion_keywords):
                return self.engine.generate_question(prompt)

        # Phản hồi mặc định nếu không khớp với các điều kiện trên
        return {
            "question": None,
            "options": [],
            "response": (
                "Đầu vào của bạn không rõ ràng. Vui lòng nhập câu hỏi hoặc chia sẻ cảm xúc để tôi hỗ trợ!\n\n"
                "**Ví dụ câu hỏi trực tiếp**: 'Tiêu chuẩn chẩn đoán rối loạn lo âu theo DSM-5 là gì?'\n"
                "**Ví dụ yêu cầu câu hỏi trắc nghiệm**: 'Tôi thấy buồn, hãy tạo câu hỏi tâm lý cho tôi.'"
            )
        }

    def process_answer(self, prompt, question, answer):
        return self.engine.process_answer(prompt, question, answer)

    def save_message(self, role, content, prompt=None, question=None, options=None):
        current_time = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
        message = {"role": role, "content": content, "time": current_time, "message": content}
        if question and options:
            message["question"] = question
            message["options"] = options
        if not st.session_state.current_conversation:
            st.session_state.current_conversation_name = prompt[:50] if prompt else "New Chat"
        st.session_state.current_conversation.append(message)