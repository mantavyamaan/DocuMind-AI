import os
os.environ['USE_CLOUD_SETUP'] = 'false'

from ingest import ingest_single_file_local
from rag import get_vector_store

print("Ingesting fake_mars_facts.txt...")
success = ingest_single_file_local("fake_mars_facts.txt", "fake_mars_facts.txt")
print(f"Ingestion success: {success}")

print("Testing retrieval immediately after ingestion...")
db = get_vector_store()
retriever = db.as_retriever(search_kwargs={"k": 4})
docs = retriever.invoke("What is the capital of Mars?")

print(f"Retrieved {len(docs)} documents.")
for doc in docs:
    print(f"Source: {doc.metadata.get('source')}")
    print(f"Content: {doc.page_content}")
