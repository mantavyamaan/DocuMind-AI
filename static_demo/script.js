document.addEventListener("DOMContentLoaded", () => {
    
    // --- Elements ---
    const fileInput = document.getElementById("fileInput");
    const uploadZone = document.getElementById("uploadZone");
    const uploadStatus = document.getElementById("uploadStatus");
    
    const chatForm = document.getElementById("chatForm");
    const questionInput = document.getElementById("questionInput");
    const sendBtn = document.getElementById("sendBtn");
    const ragChatBox = document.getElementById("ragChatBox");
    const baseChatBox = document.getElementById("baseChatBox");
    const loadHistoryBtn = document.getElementById("loadHistoryBtn");
    
    // --- Load/Hide History Logic (Mocked) ---
    let historyLoaded = false;
    
    function toggleHistory() {
        if (historyLoaded) {
            // Hide history
            ragChatBox.innerHTML = '<div class="message system-msg">Hello! I am DocuMind AI. Upload documents and ask me questions about them. I will only answer based on your securely provided knowledge.</div>';
            baseChatBox.innerHTML = '<div class="message system-msg">I am the standard base model. I answer purely based on my general pre-training, without access to your private documents.</div>';
            loadHistoryBtn.innerText = "Load Past Chats";
            historyLoaded = false;
            return;
        }
        
        loadHistoryBtn.innerText = "Loading...";
        loadHistoryBtn.disabled = true;
        
        // Mock delay for UI showcasing
        setTimeout(() => {
            ragChatBox.innerHTML = "";
            baseChatBox.innerHTML = "";
            
            // Mock History Data
            const mockHistory = [
                {
                    question: "What is the summary?",
                    rag_answer: "The system uses a 'RAG' architecture to act as an expert on internal HR policies. Instead of retraining a massive AI model, it searches actual policy documents in real-time to provide accurate answers with source citations. Everything runs locally to ensure data privacy and security.",
                    base_answer: "I am the standard base model. I answer purely based on my general pre-training, without access to your private documents. Could you provide the text you would like summarized?",
                    sources: "project_overview.txt",
                    context: "This document provides an overview of a Proof of Concept (POC) for an Enterprise HR Policy Assistant using a 'RAG' architecture. The assistant uses a locally running LLM engine, LangChain for orchestration, and ChromaDB as the database to answer employee questions by searching through actual policy documents in real-time. The workflow involves document ingestion where large policies are loaded and broken down into smaller chunks before the AI can provide answers with exact source citations."
                }
            ];
            
            mockHistory.forEach(item => {
                // Populate RAG
                appendMessage(ragChatBox, item.question, "user-msg");
                let ragAiHtml = item.rag_answer.replace(/\n/g, "<br>");
                if (item.sources) {
                    const sourcesList = item.sources.split(", ").map(s => `<li>${s}</li>`).join("");
                    const ctx = item.context.replace(/\n/g, "<br>");
                    ragAiHtml += `
                    <details class="sources-expander">
                        <summary>View Source Documents & Context</summary>
                        <div class="expander-content">
                            <strong>Sources:</strong>
                            <ul>${sourcesList}</ul>
                            <strong>Retrieved Context:</strong>
                            <div>${ctx}</div>
                        </div>
                    </details>`;
                }
                const ragDiv = appendMessage(ragChatBox, "", "ai-msg");
                ragDiv.innerHTML = ragAiHtml;
                
                // Populate Base
                appendMessage(baseChatBox, item.question, "user-msg");
                const baseDiv = appendMessage(baseChatBox, "", "ai-msg");
                baseDiv.innerHTML = item.base_answer.replace(/\n/g, "<br>");
            });
            
            ragChatBox.scrollTop = ragChatBox.scrollHeight;
            baseChatBox.scrollTop = baseChatBox.scrollHeight;
            
            loadHistoryBtn.innerText = "Hide Past Chats";
            historyLoaded = true;
            loadHistoryBtn.disabled = false;
        }, 800);
    }
    
    if (loadHistoryBtn) {
        loadHistoryBtn.addEventListener("click", toggleHistory);
    }
    
    // --- Mock File Upload Logic ---
    uploadZone.addEventListener("click", () => fileInput.click());
    
    uploadZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        uploadZone.style.borderColor = "var(--primary)";
        uploadZone.style.background = "rgba(79, 70, 229, 0.1)";
    });
    
    uploadZone.addEventListener("dragleave", () => {
        uploadZone.style.borderColor = "var(--border-glass)";
        uploadZone.style.background = "rgba(255, 255, 255, 0.02)";
    });
    
    uploadZone.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadZone.style.borderColor = "var(--border-glass)";
        uploadZone.style.background = "rgba(255, 255, 255, 0.02)";
        if (e.dataTransfer.files.length) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });
    
    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length) {
            handleFileUpload(e.target.files[0]);
        }
    });
    
    function handleFileUpload(file) {
        uploadStatus.className = "status-msg";
        uploadStatus.innerText = `Ingesting ${file.name}... ⏳`;
        
        // Mock delay for UI showcasing
        setTimeout(() => {
            uploadStatus.className = "status-msg success";
            uploadStatus.innerText = `✅ Automated Ingestion Complete for ${file.name}!`;
        }, 1500);
    }
    
    // --- Mock Chat Logic ---
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const question = questionInput.value.trim();
        if (!question) return;
        
        // Disable input
        questionInput.disabled = true;
        if (sendBtn) sendBtn.disabled = true;
        
        // Add user messages
        appendMessage(ragChatBox, question, "user-msg");
        appendMessage(baseChatBox, question, "user-msg");
        
        // Clear input
        questionInput.value = "";
        
        // Sequential mock streaming
        mockStreamResponse(question, ragChatBox, true, () => {
            // Once RAG is done, do Base
            mockStreamResponse(question, baseChatBox, false, () => {
                // Once Base is done, re-enable input
                questionInput.disabled = false;
                if (sendBtn) sendBtn.disabled = false;
                questionInput.focus();
            });
        });
    });
    
    function appendMessage(container, text, className) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${className}`;
        msgDiv.innerText = text;
        container.appendChild(msgDiv);
        container.scrollTop = container.scrollHeight;
        return msgDiv;
    }
    
    function mockStreamResponse(question, container, isRag, callback) {
        const aiMsgDiv = appendMessage(container, "...", "ai-msg");
        let currentText = "";
        aiMsgDiv.innerText = "";
        
        let fullResponse = "";
        let sourcesHTML = "";
        
        if (isRag) {
            fullResponse = "Note: This is a static UI demonstration for portfolio purposes. To interact with the real RAG model and query your own private documents, please visit the GitHub repository, follow the README instructions, and run the complete model locally!";
            sourcesHTML = `
            <details class="sources-expander">
                <summary>View Source Documents & Context</summary>
                <div class="expander-content">
                    <strong>Sources:</strong>
                    <ul><li>project_overview.txt</li><li>hr_policies_2026.pdf</li></ul>
                    <strong>Retrieved Context:</strong>
                    <div>This document provides an overview of a Proof of Concept (POC) for an Enterprise HR Policy Assistant using a 'RAG' architecture...</div>
                </div>
            </details>`;
        } else {
            fullResponse = "Note: This is a static UI demonstration. The real base model (Qwen2.5:7b) runs locally on your machine for complete privacy. Visit the GitHub repo to run the full application!";
        }
        
        const words = fullResponse.split(" ");
        let i = 0;
        
        const interval = setInterval(() => {
            if (i < words.length) {
                currentText += (i > 0 ? " " : "") + words[i];
                aiMsgDiv.innerText = currentText;
                container.scrollTop = container.scrollHeight;
                i++;
            } else {
                clearInterval(interval);
                if (isRag) {
                    aiMsgDiv.innerHTML = currentText + sourcesHTML;
                } else {
                    aiMsgDiv.innerHTML = currentText;
                }
                container.scrollTop = container.scrollHeight;
                
                if (callback) callback();
            }
        }, 50); // 50ms per word to simulate streaming
    }
    
});
