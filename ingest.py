import os
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

DB_DIR = "vector_db"
DATA_DIR = "data"

def process_file_in_chunks(filepath, chunk_size=5000000):
    """Generator to read a massive file in safe chunks to prevent OOM errors."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        while True:
            text = f.read(chunk_size)
            if not text:
                break
            yield text

def create_vector_database():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Created {DATA_DIR}/ directory. Please place your large files there.")
        return

    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    # Do not delete collection automatically, allow appending for massive datasets
    vector_store = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=120
    )

    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.txt')]
    if not files:
        print(f"No .txt files found in {DATA_DIR}/ directory.")
        return

    total_chunks_added = 0

    for filename in files:
        filepath = os.path.join(DATA_DIR, filename)
        print(f"Processing {filename}...")
        
        # Read file in 5MB chunks to prevent memory crash
        batch_number = 1
        for text_chunk in process_file_in_chunks(filepath):
            doc = Document(page_content=text_chunk, metadata={"source": filename})
            split_chunks = splitter.split_documents([doc])
            
            if split_chunks:
                vector_store.add_documents(split_chunks)
                total_chunks_added += len(split_chunks)
                print(f"  -> Added batch {batch_number} ({len(split_chunks)} chunks)")
            
            batch_number += 1

    print(f"\\nVector database ingestion completed! Total chunks indexed: {total_chunks_added}")

if __name__ == "__main__":
    create_vector_database()
