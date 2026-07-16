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
    
    // --- Load/Hide History Logic ---
    let historyLoaded = false;
    
    async function toggleHistory() {
        if (historyLoaded) {
            // Hide history
            ragChatBox.innerHTML = '<div class="message system-msg">Hello! I am DocuMind AI. Upload documents and ask me questions about them. I will only answer based on your securely provided knowledge.</div>';
            baseChatBox.innerHTML = '<div class="message system-msg">I am the standard base model. I answer purely based on my general pre-training, without access to your private documents.</div>';
            loadHistoryBtn.innerText = "Load Past Chats";
            historyLoaded = false;
            return;
        }
        
        try {
            loadHistoryBtn.innerText = "Loading...";
            loadHistoryBtn.disabled = true;
            
            const res = await fetch("/history");
            const data = await res.json();
            if (data.history && data.history.length > 0) {
                ragChatBox.innerHTML = "";
                baseChatBox.innerHTML = "";
                
                data.history.forEach(item => {
                    // Populate RAG
                    appendMessage(ragChatBox, item.question, "user-msg");
                    let ragAiHtml = item.rag_answer.replace(/\n/g, "<br>");
                    if (item.sources && item.sources !== "None") {
                        const sourcesList = item.sources.split(", ").map(s => `<li>${s}</li>`).join("");
                        const ctx = item.context ? item.context.replace(/\n/g, "<br>") : "No context saved.";
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
            }
            loadHistoryBtn.innerText = "Hide Past Chats";
            historyLoaded = true;
            loadHistoryBtn.disabled = false;
        } catch (e) {
            console.error("Failed to load history", e);
            loadHistoryBtn.innerText = "Error Loading";
            loadHistoryBtn.disabled = false;
        }
    }
    
    if (loadHistoryBtn) {
        loadHistoryBtn.addEventListener("click", toggleHistory);
    }
    
    // --- File Upload Logic ---
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
    
    async function handleFileUpload(file) {
        const formData = new FormData();
        formData.append("file", file);
        
        uploadStatus.className = "status-msg";
        uploadStatus.innerText = `Ingesting ${file.name}... ⏳`;
        
        try {
            const res = await fetch("/upload", {
                method: "POST",
                body: formData
            });
            const data = await res.json();
            
            if (res.ok) {
                if (data.status === "warning") {
                    uploadStatus.className = "status-msg warning";
                    uploadStatus.innerText = data.message;
                } else {
                    uploadStatus.className = "status-msg success";
                    uploadStatus.innerText = data.message;
                }
            } else {
                uploadStatus.className = "status-msg error";
                uploadStatus.innerText = data.detail || "Upload failed.";
            }
        } catch (err) {
            uploadStatus.className = "status-msg error";
            uploadStatus.innerText = "Network error during upload.";
        }
    }
    
    // --- Chat Logic ---
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const question = questionInput.value.trim();
        if (!question) return;
        
        // Disable input
        questionInput.disabled = true;
        sendBtn.disabled = true;
        
        // Add user messages
        appendMessage(ragChatBox, question, "user-msg");
        appendMessage(baseChatBox, question, "user-msg");
        
        // Clear input
        questionInput.value = "";
        
        // 1. RAG Model First
        const ragResult = await streamResponse("/chat/rag", question, ragChatBox, true);
        
        // 2. Base Model Second
        const baseResult = await streamResponse("/chat/base", question, baseChatBox, false);
        
        // 3. Save History
        try {
            await fetch("/history/save", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    question: question,
                    rag_answer: ragResult.text,
                    base_answer: baseResult.text,
                    sources: ragResult.sources || [],
                    context: ragResult.context || ""
                })
            });
        } catch (e) {
            console.error("Failed to save history:", e);
        }
        
        // Re-enable input
        questionInput.disabled = false;
        sendBtn.disabled = false;
        questionInput.focus();
    });
    
    function appendMessage(container, text, className) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${className}`;
        msgDiv.innerText = text;
        container.appendChild(msgDiv);
        container.scrollTop = container.scrollHeight;
        return msgDiv;
    }
    
    async function streamResponse(url, question, container, isRag) {
        const aiMsgDiv = appendMessage(container, "...", "ai-msg");
        let currentText = "";
        aiMsgDiv.innerText = "";
        
        let sourcesList = [];
        let finalContext = "";
        
        try {
            const res = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question })
            });
            
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";
            let sourcesHTML = "";
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                
                const parts = buffer.split("\n\n");
                buffer = parts.pop(); 
                
                for (const part of parts) {
                    if (part.startsWith("data: ")) {
                        const jsonStr = part.substring(6);
                        try {
                            const data = JSON.parse(jsonStr);
                            
                            if (data.type === "chunk") {
                                currentText += data.data;
                                aiMsgDiv.innerText = currentText;
                                container.scrollTop = container.scrollHeight;
                            } else if (data.type === "sources") {
                                if (data.data && data.data.length > 0) {
                                    sourcesList = data.data;
                                    finalContext = data.context || "";
                                    let liHtml = "";
                                    data.data.forEach(src => { liHtml += `<li>${src}</li>`; });
                                    
                                    sourcesHTML = `
                                    <details class="sources-expander">
                                        <summary>View Source Documents & Context</summary>
                                        <div class="expander-content">
                                            <strong>Sources:</strong>
                                            <ul>${liHtml}</ul>
                                            <strong>Retrieved Context:</strong>
                                            <div>${finalContext.replace(/\n/g, "<br>")}</div>
                                        </div>
                                    </details>`;
                                }
                            } else if (data.type === "end") {
                                if (sourcesHTML) {
                                    aiMsgDiv.innerHTML = currentText.replace(/\n/g, "<br>") + sourcesHTML;
                                } else {
                                    aiMsgDiv.innerHTML = currentText.replace(/\n/g, "<br>");
                                }
                                container.scrollTop = container.scrollHeight;
                            }
                        } catch (e) {
                            console.error("JSON Parse error for part:", jsonStr, e);
                        }
                    }
                }
            }
            return { text: currentText, sources: sourcesList, context: finalContext };
        } catch (err) {
            aiMsgDiv.innerText = "Error connecting to the AI.";
            console.error(err);
            return { text: "Error connecting to the AI.", sources: [], context: "" };
        }
    }
    
});
