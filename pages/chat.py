# pages/chat.py
import streamlit as st
import sys
import os
from src.bot_logic import BotLogic
from src.slide_bar import render_sidebar

# Thêm thư mục gốc (Project/) vào sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

st.set_page_config(page_title="Trò chuyện", layout="wide", initial_sidebar_state="expanded")
st.markdown("<h1 style='text-align: center;'>Chatbot Tâm Lý Con Người</h1>", unsafe_allow_html=True)

# Kiểm tra trạng thái đăng nhập
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("Vui lòng đăng nhập trước khi truy cập trang trò chuyện.")
    st.markdown("[Quay lại Trang chủ](./home.py)")
    st.stop()

# Lấy username và user_info từ session (hoặc dùng giá trị mặc định cho demo)
username = st.session_state.get("username", "demo_user")
user_info = st.session_state.get("user_info", {"name": "Người dùng Demo", "age": 25})

# Khởi tạo session state
if "conversations" not in st.session_state:
    st.session_state.conversations = []
if "current_conversation" not in st.session_state:
    st.session_state.current_conversation = []
if "current_conversation_name" not in st.session_state:
    st.session_state.current_conversation_name = None
if "show_history" not in st.session_state:
    st.session_state.show_history = False
if "show_search" not in st.session_state:
    st.session_state.show_search = False
if "waiting_for_answer" not in st.session_state:
    st.session_state.waiting_for_answer = False
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "current_options" not in st.session_state:
    st.session_state.current_options = []
if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = ""

# Khởi tạo BotLogic với username và user_info
try:
    bot = BotLogic(username=username, user_info=user_info)
except Exception as e:
    st.error(f"Lỗi khi khởi tạo chatbot: {str(e)}. Vui lòng kiểm tra Vector DB và mô hình.")
    st.stop()

# Hiển thị sidebar
render_sidebar()

# Hiển thị tin nhắn
for message in st.session_state.current_conversation:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "question" in message and "options" in message:
            st.write(f"**Câu hỏi**: {message['question']}")
            st.write("**Lựa chọn**:")
            for option in message["options"]:
                st.write(f"- {option}")

# Xử lý trạng thái chờ đáp án
if st.session_state.waiting_for_answer:
    with st.chat_message("assistant"):
        st.write(f"**Câu hỏi**: {st.session_state.current_question}")
        answer = st.radio("Chọn mức độ:", st.session_state.current_options, key="answer_radio")
        if st.button("Gửi đáp án"):
            try:
                response = bot.process_answer(st.session_state.last_prompt, st.session_state.current_question, answer)
                # Lưu câu hỏi và lựa chọn trước khi xóa trạng thái
                bot.save_message("assistant", f"**Câu hỏi**: {st.session_state.current_question}\n\n{response}", 
                                question=st.session_state.current_question, 
                                options=st.session_state.current_options)
                bot.save_message("user", answer)
                st.session_state.waiting_for_answer = False
                st.session_state.current_question = None
                st.session_state.current_options = []
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi khi xử lý đáp án: {str(e)}")

# Nhập tin nhắn
if prompt := st.chat_input("Chia sẻ cảm xúc của bạn, tôi sẽ lắng nghe!"):
    with st.chat_message("user"):
        st.markdown(prompt)
    try:
        bot.save_message("user", prompt, prompt)
        st.session_state.last_prompt = prompt
        result = bot.process_input(prompt)
        if result["question"]:
            st.session_state.current_question = result["question"]
            st.session_state.current_options = result["options"]
            st.session_state.waiting_for_answer = True
            with st.chat_message("assistant"):
                st.markdown(result["response"])
                st.write(f"**Câu hỏi**: {result['question']}")
                st.radio("Chọn mức độ:", result["options"], key="initial_radio")
            bot.save_message("assistant", f"{result['response']}\n\n**Câu hỏi**: {result['question']}", 
                            question=result["question"], options=result["options"])
        else:
            with st.chat_message("assistant"):
                st.markdown(result["response"])
            bot.save_message("assistant", result["response"])
        st.rerun()
    except Exception as e:
        st.error(f"Lỗi khi xử lý tin nhắn: {str(e)}")