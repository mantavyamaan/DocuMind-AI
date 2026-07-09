import os
import boto3
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

load_dotenv()

def create_vector_database():
    # Load Environment Variables
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

    if not all([PINECONE_API_KEY, PINECONE_INDEX_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME]):
        print("Error: Missing required cloud API keys. Please configure your .env file.")
        return

    print("Connecting to Pinecone and Amazon S3...")

    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vector_store = PineconeVectorStore(index_name=PINECONE_INDEX_NAME, embedding=embeddings)

    # Initialize S3 Client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=120
    )

    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME)
        files = [item['Key'] for item in response.get('Contents', []) if item['Key'].endswith('.txt')]
    except Exception as e:
        print(f"Error accessing S3 bucket: {e}")
        return

    if not files:
        print(f"No .txt files found in S3 Bucket: {S3_BUCKET_NAME}")
        return

    total_chunks_added = 0

    for filename in files:
        print(f"Streaming {filename} from Amazon S3...")
        
        # Read file in streaming chunks directly from S3 to prevent OOM errors
        s3_object = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=filename)
        body = s3_object['Body']
        
        batch_number = 1
        # Read in safe 5MB chunks from the cloud stream
        for text_chunk_bytes in body.iter_chunks(chunk_size=5000000):
            text_chunk = text_chunk_bytes.decode('utf-8', errors='ignore')
            doc = Document(page_content=text_chunk, metadata={"source": filename})
            split_chunks = splitter.split_documents([doc])
            
            if split_chunks:
                # Push directly to Pinecone Cloud
                vector_store.add_documents(split_chunks)
                total_chunks_added += len(split_chunks)
                print(f"  -> Uploaded batch {batch_number} to Pinecone ({len(split_chunks)} chunks)")
            
            batch_number += 1

    print(f"\nCloud Vector database ingestion completed! Total chunks indexed: {total_chunks_added}")

if __name__ == "__main__":
    create_vector_database()
