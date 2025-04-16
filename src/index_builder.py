# src/index_builder.py
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import GPT4AllEmbeddings
from src.global_settings import INGESTION_STORAGE_PATH, VECTOR_DB_PATH, EMBEDDING_MODEL_FILE

def build_index():
    loader = DirectoryLoader(INGESTION_STORAGE_PATH, glob="*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)
    # Sử dụng GPT4AllEmbeddings với file .gguf
    embedding_model = GPT4AllEmbeddings(model_file=EMBEDDING_MODEL_FILE)
    db = FAISS.from_documents(chunks, embedding_model)
    db.save_local(VECTOR_DB_PATH)
    return db