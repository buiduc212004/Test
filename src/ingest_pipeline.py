# src/ingest_pipeline.py
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.global_settings import INGESTION_STORAGE_PATH

def create_nodes():
    loader = DirectoryLoader(INGESTION_STORAGE_PATH, glob="*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
    nodes = text_splitter.split_documents(documents)
    return nodes