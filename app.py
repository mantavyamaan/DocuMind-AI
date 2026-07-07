import streamlit as st

st.set_page_config(
    page_title="Open-source LLM RAG POC",
    page_icon="🤖",
    layout="wide"
)

from rag import ask_base_model, ask_rag_model
import db

st.title("Open-source LLM Optimization POC")
st.subheader("HR Policy Assistant using Qwen + RAG")

st.write(
    """
This POC compares a base open-source LLM with a RAG-optimized version.
The optimized version retrieves relevant HR policy documents before answering.
"""
)

from ingest import create_vector_database

# --- Sidebar: Document Management ---
with st.sidebar:
    st.header("📄 Document Management")
    st.write("Upload HR policies here. The AI will automatically ingest them.")
    
    uploaded_file = st.file_uploader("Upload a .txt policy", type=["txt"])
    if uploaded_file is not None:
        file_hash = hash(uploaded_file.getvalue())
        if st.session_state.get("last_uploaded_hash") != file_hash:
            filename = uploaded_file.name
            content = uploaded_file.getvalue().decode("utf-8")
            
            with st.spinner("Saving and indexing document..."):
                db.save_document(filename, content)
                create_vector_database()
            st.success(f"Successfully added {filename}!")
            st.session_state["last_uploaded_hash"] = file_hash
        
    st.markdown("---")
    st.subheader("📚 Currently Stored Policies")
    docs = db.get_all_documents()
    if docs:
        for doc in docs:
            st.write(f"- {doc['filename']}")
    else:
        st.write("No documents stored yet.")

    st.markdown("---")
    st.subheader("📜 Chat Logs")
    
    # We use a button to refresh logs, or they update when the script reruns.
    history = db.get_all_history()
    if history:
        with st.expander("View Past Conversations"):
            for entry in history:
                st.markdown(f"**Q: {entry['question']}**")
                st.markdown(f"*A: {entry['rag_answer']}*")
                st.caption(f"Sources: {entry['sources']} | {entry['timestamp']}")
                st.divider()
    else:
        st.write("No history yet.")

# --- Main App ---
question = st.text_input(
    "Ask an HR policy question:",
    placeholder="Example: How many casual leaves are allowed per year?"
)

if st.button("Ask") and question:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Base Open-source LLM")
        with st.spinner("Generating base model answer..."):
            base_answer = ask_base_model(question)
        st.write(base_answer)

    with col2:
        st.markdown("### RAG-Optimized LLM")
        with st.spinner("Retrieving documents and generating answer..."):
            rag_result = ask_rag_model(question)
        st.write(rag_result["answer"])

        st.markdown("### Sources")
        for source in rag_result["sources"]:
            st.write(f"- {source}")

    with st.expander("Retrieved Context"):
        st.text(rag_result["retrieved_context"])
        
    # Save to database
    db.save_interaction(
        question=question,
        base_answer=base_answer,
        rag_answer=rag_result["answer"],
        sources=rag_result["sources"]
    )
