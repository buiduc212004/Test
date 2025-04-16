# home.py
import streamlit as st
import sys
import os

# Thêm thư mục gốc (Project/) vào sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.authenticate import authenticate_user

st.set_page_config(page_title="Trang chủ", layout="wide")
st.markdown("<h1 style='text-align: center;'>Chào mừng đến với Chatbot Tâm Lý</h1>", unsafe_allow_html=True)

username = st.text_input("Tên đăng nhập")
password = st.text_input("Mật khẩu", type="password")
if st.button("Đăng nhập"):
    if authenticate_user(username, password):
        st.success("Đăng nhập thành công! Đang chuyển sang trang Trò chuyện...")
        st.session_state["logged_in"] = True
        st.session_state["username"] = username
        st.switch_page("pages/chat.py")
    else:
        st.error("Sai tên đăng nhập hoặc mật khẩu.")