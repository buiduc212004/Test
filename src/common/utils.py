# src/common/utils.py
import logging
import streamlit as st
import json
import os
from src.global_settings import CHAT_HISTORY_FILE

# Cấu hình logger
logger = logging.getLogger("mental_health_chatbot")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Hàm hiển thị tin nhắn
def display_message(chat_store, container, key):
    for msg in chat_store:
        with container.chat_message(name=msg["role"]):
            st.markdown(f"**{msg['time']}**: {msg['content']}")