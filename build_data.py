# build_data.py
from src.index_builder import build_index
from src.ingest_pipeline import create_nodes

def build_data():
    nodes = create_nodes()
    db = build_index()
    return nodes, db

if __name__ == "__main__":
    nodes, db = build_data()
    print("Đã tạo nodes và index.")