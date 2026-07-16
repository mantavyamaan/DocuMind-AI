from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

try:
    embeddings = OllamaEmbeddings(model='nomic-embed-text')
    db = Chroma(persist_directory='vector_db', embedding_function=embeddings)
    db.delete_collection()
    print("Collection successfully deleted.")
except Exception as e:
    print(f"Error: {e}")
