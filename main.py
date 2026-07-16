import os
import json
import tempfile
import boto3
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import db
from rag import stream_base_model, stream_rag_model
from ingest import ingest_single_file_local, ingest_single_file_cloud

app = FastAPI(title="DocuMind AI API")

# Setup CORS for frontend to communicate if separated, though we will serve from static
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint to handle document uploads
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    use_cloud = os.getenv("USE_CLOUD_SETUP", "false").lower() == "true"
    
    try:
        if use_cloud:
            AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
            AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
            AWS_REGION = os.getenv("AWS_REGION")
            S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
            
            s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)
            ext = os.path.splitext(file.filename)[1].lower()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_filepath = tmp_file.name
                
            s3_client.upload_file(tmp_filepath, S3_BUCKET_NAME, file.filename)
            result = ingest_single_file_cloud(tmp_filepath, file.filename)
            os.remove(tmp_filepath)
        else:
            if not os.path.exists("data"):
                os.makedirs("data")
            filepath = os.path.join("data", file.filename)
            with open(filepath, "wb") as f:
                content = await file.read()
                f.write(content)
                
            result = ingest_single_file_local(filepath, file.filename)
            
        if result == True:
            return {"status": "success", "message": f"Successfully ingested {file.filename}"}
        elif result == "NO_TEXT":
            return {"status": "warning", "message": f"{file.filename} is a scanned image. No text extracted."}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to ingest {file.filename}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    question: str

# RAG Chat Stream
@app.post("/chat/rag")
async def chat_rag(request: ChatRequest):
    try:
        rag_result = stream_rag_model(request.question)
        
        async def event_stream():
            # Send the sources and context so the UI can display them in an expander
            sources_data = json.dumps({
                "type": "sources", 
                "data": rag_result["sources"],
                "context": rag_result["retrieved_context"]
            })
            yield f"data: {sources_data}\n\n"
            
            # Stream the answer tokens
            for chunk in rag_result["answer_stream"]:
                chunk_data = json.dumps({"type": "chunk", "data": chunk})
                yield f"data: {chunk_data}\n\n"
                
            # Send an end event
            end_data = json.dumps({"type": "end"})
            yield f"data: {end_data}\n\n"
            
        return StreamingResponse(event_stream(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Base Chat Stream
@app.post("/chat/base")
async def chat_base(request: ChatRequest):
    try:
        base_stream = stream_base_model(request.question)
        
        async def event_stream():
            for chunk in base_stream:
                chunk_data = json.dumps({"type": "chunk", "data": chunk})
                yield f"data: {chunk_data}\n\n"
            
            end_data = json.dumps({"type": "end"})
            yield f"data: {end_data}\n\n"
            
        return StreamingResponse(event_stream(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_history():
    history = db.get_all_history()
    return {"history": history}

class SaveHistoryRequest(BaseModel):
    question: str
    base_answer: str
    rag_answer: str
    sources: list
    context: str = ""

@app.post("/history/save")
async def save_history(request: SaveHistoryRequest):
    try:
        db.save_interaction(request.question, request.base_answer, request.rag_answer, request.sources, request.context)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve the static frontend
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
