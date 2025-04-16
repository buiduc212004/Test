# src/bot_logic.py
import streamlit as st
from src.conversation_engine import ConversationEngine
from src.global_settings import CHAT_HISTORY_FILE
from datetime import datetime

class BotLogic:
    def __init__(self):
        self.engine = ConversationEngine()

    def process_input(self, prompt):
        if not prompt:
            return {"question": None, "options": [], "response": "Hãy chia sẻ thêm để tôi có thể hỗ trợ bạn nhé!"}
        quiz = self.engine.generate_question(prompt)
        return {
            "question": quiz["question"],
            "options": quiz["options"],
            "response": "Hãy chọn mức độ phù hợp với bạn!"
        }

    def process_answer(self, prompt, question, answer):
        return self.engine.process_answer(prompt, question, answer)

    def save_message(self, role, content, prompt=None):
        current_time = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
        message = {"role": role, "content": content, "time": current_time, "message": content}
        if not st.session_state.current_conversation:
            st.session_state.current_conversation_name = prompt[:50] if prompt else "New Chat"
        st.session_state.current_conversation.append(message)