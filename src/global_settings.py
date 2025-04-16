# src/global_settings.py
import os

# Đường dẫn
DATA_PATH = "data"
CACHE_PATH = os.path.join(DATA_PATH, "cache")
IMAGES_PATH = os.path.join(DATA_PATH, "images")
INDEX_STORAGE_PATH = os.path.join(DATA_PATH, "index_storage")
INGESTION_STORAGE_PATH = os.path.join(DATA_PATH, "ingestion_storage")
USER_STORAGE_PATH = os.path.join(DATA_PATH, "user_storage")
VECTOR_DB_PATH = os.path.join(INDEX_STORAGE_PATH, "db_faiss")
CHAT_HISTORY_FILE = os.path.join(CACHE_PATH, "chat_history.json")
MODELS_PATH = "models"
# Cập nhật tên file mô hình chính xác
EMBEDDING_MODEL_FILE = os.path.join(MODELS_PATH, "all-MiniLM-L6-v2-f16.gguf")
LLM_MODEL_FILE = os.path.join(MODELS_PATH, "Meta-Llama-3-8B-Instruct-Q4_K_M.gguf")