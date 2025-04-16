# pages/user.py
import streamlit as st
import sys
import os

# Thêm thư mục gốc (Project/) vào sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

st.set_page_config(page_title="Kết quả đánh giá", layout="wide", initial_sidebar_state="expanded")
st.markdown("<h1 style='text-align: center;'>Kết quả đánh giá</h1>", unsafe_allow_html=True)

# Kiểm tra trạng thái đăng nhập
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("Vui lòng đăng nhập trước khi truy cập trang kết quả.")
    st.markdown("[Quay lại Trang chủ](./home.py)")  # Sửa thành home.py
    st.stop()

st.write("Chưa có dữ liệu đánh giá. Vui lòng trò chuyện để nhận kết quả.")