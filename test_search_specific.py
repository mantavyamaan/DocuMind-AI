from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(model='nomic-embed-text')
db = Chroma(persist_directory='vector_db', embedding_function=embeddings)

query = "How many casual leaves are allowed per year?"
print(f"Querying: {query}")
results = db.similarity_search_with_score(query, k=10)

for doc, score in results:
    print(f"Score: {score} | Source: {doc.metadata.get('source')} | Content: {doc.page_content[:150]}...")
