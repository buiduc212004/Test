# src/slide_bar.py
import streamlit as st
from src.global_settings import CHAT_HISTORY_FILE
import json
import os

def render_sidebar():
    with st.sidebar:
        st.markdown("<h1 style='text-align: left; margin-top: 0px;'>Menu</h1>", unsafe_allow_html=True)
        if st.button("Lịch sử các cuộc hội thoại"):
            st.session_state.show_history = not st.session_state.show_history
            st.session_state.show_search = False
        if st.session_state.show_history:
            history = load_chat_history()
            if history:
                st.write("### Danh sách các cuộc hội thoại")
                for idx, conv in enumerate(history):
                    if st.button(f"Cuộc hội thoại: {conv['name']}", key=f"conv_{idx}"):
                        st.session_state.current_conversation = conv["messages"]
                        st.session_state.current_conversation_name = conv["name"]
                        st.session_state.show_history = False
                        st.session_state.waiting_for_answer = False
                        st.rerun()
            else:
                st.write("Chưa có cuộc hội thoại nào.")
        st.markdown("<h3 style='margin-top: 20px;'>Tìm kiếm lịch sử</h3>", unsafe_allow_html=True)
        search_query = st.text_input(
            label="Tìm kiếm tin nhắn",
            placeholder="Nhập từ khóa",
            key="search_input",
            label_visibility="hidden"
        )
        if search_query:
            st.session_state.show_search = True
            st.session_state.show_history = False
            history = load_chat_history()
            found_conversations = []
            for conv in history:
                for msg in conv["messages"]:
                    if search_query.lower() in msg["message"].lower():
                        if conv not in found_conversations:
                            found_conversations.append(conv)
                        break
            if found_conversations:
                st.write("### Kết quả tìm kiếm")
                for idx, conv in enumerate(found_conversations):
                    if st.button(f"Cuộc hội thoại: {conv['name']}", key=f"search_conv_{idx}"):
                        st.session_state.current_conversation = conv["messages"]
                        st.session_state.current_conversation_name = conv["name"]
                        st.session_state.show_search = False
                        st.session_state.waiting_for_answer = False
                        st.rerun()
            else:
                st.write("Không tìm thấy kết quả.")
        else:
            st.session_state.show_search = False
        st.markdown("<h3 style='margin-top: 20px;'>Cuộc trò chuyện mới</h3>", unsafe_allow_html=True)
        if st.button("➕ Cuộc trò chuyện mới"):
            save_current_conversation()
            st.session_state.current_conversation = []
            st.session_state.current_conversation_name = None
            st.session_state.show_history = False
            st.session_state.show_search = False
            st.session_state.waiting_for_answer = False
            st.success("Đã tạo cuộc trò chuyện mới!")

def load_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_current_conversation():
    if st.session_state.current_conversation:
        history = load_chat_history()
        conv_exists = False
        for conv in history:
            if conv["name"] == st.session_state.current_conversation_name:
                conv["messages"] = st.session_state.current_conversation
                conv_exists = True
                break
        if not conv_exists:
            history.append({
                "name": st.session_state.current_conversation_name,
                "messages": st.session_state.current_conversation
            })
        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=4)