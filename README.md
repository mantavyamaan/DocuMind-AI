# Enterprise Open-Source LLM Optimization (RAG POC)

## Overview
This Proof of Concept (POC) demonstrates how a general-purpose, open-source Large Language Model (LLM) can be optimized for a specific enterprise use case—an **HR Policy Assistant**. 

Instead of relying on computationally expensive fine-tuning, this project utilizes **Retrieval-Augmented Generation (RAG)** to ground the LLM in internal company documents. This approach significantly improves factual accuracy, reduces hallucinations, allows for explicit source citations, and keeps data private by running the model locally.

## Features
* **Local Open-Source AI:** Uses `Qwen2.5:7b` via Ollama for fast, secure, and private on-device inference.
* **Real-time UI Streaming:** Answers are streamed word-by-word into the UI (just like ChatGPT) for zero perceived latency.
* **Enterprise Cloud Data Pipeline (100 GB+):** Connects directly to Amazon S3 to stream massive datasets without downloading them, and embeds them straight into Pinecone Vector Database for lightning-fast, highly scalable search.
* **Chat Logging:** All questions, generated answers, and source citations are silently logged to an SQLite database (`chat_history.db`) for auditing.
* **Source Citation:** The optimized model explicitly cites the exact internal document used to generate its answer.
* **Hallucination Mitigation:** Strict prompt engineering ensures the model refuses to answer if the information is not present in the internal documents.
* **Automated Evaluation Matrix:** Includes a benchmarking script that tests for Factual Accuracy, Hallucination Prevention, and Source Grounding. The results are displayed live in a beautiful matrix in the Streamlit UI.
* **Interactive UI:** Built with Streamlit for a clean, user-friendly chat interface with a sidebar for Document Management and Live Analytics.

## Tech Stack
* **Language:** Python 3.10+
* **LLM Engine:** Ollama
* **Models:** `qwen2.5:7b` (Text Generation), `nomic-embed-text` (Embeddings)
* **Orchestration:** LangChain
* **Databases:** SQLite (Chat Logging), Pinecone (Cloud Vector Search), Amazon S3 (Cloud Document Storage)
* **Frontend:** Streamlit

---

## 🚀 Setup & Installation Guide

Follow these steps to get the project running on your local machine.

### 1. Prerequisites
Before you begin, you must have [Ollama](https://ollama.com/) installed on your machine.
Once Ollama is installed, open your terminal and pull the required models:
```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

### 2. Clone the Repository
```bash
git clone https://github.com/mantavyamaan/open-source-llm-rag-poc.git
cd open-source-llm-rag-poc
```

### 3. Create a Virtual Environment
It is highly recommended to use a virtual environment to manage dependencies.
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
Install the required Python packages using the provided requirements file:
```bash
pip install -r requirements.txt
```

### 5. Enterprise Cloud Setup (.env)
This project requires AWS S3 and Pinecone to handle massive datasets.
1. Create a file named `.env` in the root directory.
2. Copy the contents of `.env.example` into your new `.env` file.
3. Fill in your private API keys:
   * **AWS S3**: Your Access Key, Secret Key, Region, and Bucket Name.
   * **Pinecone**: Your API Key and Index Name.

---

## 🏃‍♂️ Running the Application

### Launch the Web Interface
Start the Streamlit application to interact with the HR Assistant and manage documents:
```bash
streamlit run app.py
```
*This will open a browser window (usually at `http://localhost:8501`).*

### How to Use
1. **Upload Policies to S3:** Upload your massive `.txt` policy files directly into your Amazon S3 bucket.
2. **Ingest the Data:** Open your terminal and run `python ingest.py`. This script will safely stream and process the files in small 5MB batches from S3 directly into Pinecone.
3. **Ask Questions:** Type a question in the main chat input of the Streamlit app. It will fetch context from Pinecone in milliseconds.
4. **View Logs:** All chats are securely logged in the local `chat_history.db` file.

---

## 📊 Running Evaluations (Optional)
To benchmark the accuracy of the Base Model versus the RAG Model against a predefined set of questions, run the evaluation script:
```bash
python evaluate.py
```
*This will output the accuracy percentages directly in the terminal and save detailed results to `eval/results.json`.*

---

## Project Structure
```text
open-source-llm-rag-poc/
├── app.py                  # Streamlit frontend UI
├── db.py                   # SQLite database manager (documents & chat history)
├── ingest.py               # Document chunking and ChromaDB ingestion script
├── rag.py                  # Core logic for Base LLM and RAG-optimized LLM pipelines
├── evaluate.py             # Script to benchmark Base vs. RAG accuracy
├── requirements.txt        # Python dependencies
├── chat_history.db         # Auto-generated SQLite database
├── vector_db/              # Auto-generated by ChromaDB to store embeddings
└── eval/
    └── questions.json      # Test dataset for evaluate.py
```