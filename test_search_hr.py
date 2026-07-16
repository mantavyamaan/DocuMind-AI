from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
import pprint

embeddings = OllamaEmbeddings(model='nomic-embed-text')
db = Chroma(persist_directory='vector_db', embedding_function=embeddings)

query = "what are key capabilities"
print(f"Querying: {query}")
# Try to find the exact chunk containing "Key Capabilities"
results = db.similarity_search_with_score(query, k=100) # Increased K just in case

hr_chunks = [(doc, score) for doc, score in results if doc.metadata.get('source') == 'Project Overview HR Policy Assistan.txt']

print(f'Found {len(hr_chunks)} chunks from HR file in top 100.')
for doc, score in hr_chunks[:5]:
    print(f"Score: {score} | Content: {doc.page_content[:150]}...")
