from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import time
from dotenv import load_dotenv
from Chatbot.chatbot import get_pdf_text, get_vector_store, user_input
from database import get_db, PDFDocument
import shutil
import json

load_dotenv()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}
        self.message_counts: dict = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.message_counts[client_id] = {"count": 0, "last_reset": time.time()}

    async def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            del self.message_counts[client_id]

    def can_send_message(self, client_id: str) -> bool:
        now = time.time()
        client_data = self.message_counts.get(client_id, {"count": 0, "last_reset": now})
        
        if now - client_data["last_reset"] > 60:
            client_data = {"count": 0, "last_reset": now}
            self.message_counts[client_id] = client_data

        if client_data["count"] >= 5:
            return False

        client_data["count"] += 1
        self.message_counts[client_id] = client_data
        return True

manager = ConnectionManager()

# Add this function before creating the FastAPI app
def cleanup_faiss_directory():
    try:
        if os.path.exists("faiss"):
            shutil.rmtree("faiss")
        os.makedirs("faiss", exist_ok=True)
        print("FAISS directory cleaned up successfully")
    except Exception as e:
        print(f"Warning: Could not clean up FAISS directory: {str(e)}")

# Add this right after creating the FastAPI app
cleanup_faiss_directory()  # Clean up at startup

# Endpoint for PDF upload with rate limit
@app.post("/upload/")
@limiter.limit("5/minute")
async def upload_file(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    print(f"Received file: {file.filename}, type: {type(file)}")
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400, 
            detail="Only PDF files are allowed"
        )
    
    try:
        print("Reading file content...")
        content = await file.read()
        print(f"File size: {len(content)} bytes")
        
        if len(content) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file uploaded"
            )
        
        # Extract text from PDF
        print("Extracting text from PDF...")
        text = get_pdf_text(content)
        print(f"Extracted text length: {len(text)} characters")
        
        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF"
            )
        
        # Save to database
        print("Saving to database...")
        try:
            pdf_doc = PDFDocument(
                filename=file.filename,
                text_content=text
            )
            db.add(pdf_doc)
            db.commit()
            db.refresh(pdf_doc)
            print("Saved to database successfully")
        except Exception as db_error:
            db.rollback()
            print(f"Database error: {str(db_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Database error: {str(db_error)}"
            )
        
        # Create vector store
        print("Creating vector store...")
        try:
            get_vector_store(text)
            print("Vector store created successfully")
        except Exception as vs_error:
            print(f"Vector store error: {str(vs_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Vector store error: {str(vs_error)}"
            )
        
        return {
            "filename": file.filename,
            "message": "PDF uploaded and processed successfully",
            "text_length": len(text)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing upload: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )

# WebSocket endpoint for Q&A
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection established")
    
    try:
        while True:
            # Receive question
            question = await websocket.receive_text()
            print(f"\nReceived question: {question}")
            
            try:
                if not os.path.exists("faiss/index.faiss"):
                    await websocket.send_text(json.dumps({
                        "error": "Please upload a PDF document first."
                    }))
                    continue

                # Get response from chatbot
                print("Processing question through user_input...")
                response, docs = user_input(question)
                print(f"Response received: {response}")

                # Send response back to client
                await websocket.send_text(json.dumps({
                    "response": response
                }))
                
            except Exception as e:
                print(f"Error processing question: {str(e)}")
                await websocket.send_text(json.dumps({
                    "error": f"Error: {str(e)}"
                }))
                
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")

# Root endpoint with HTML interface
@app.get("/")
async def get():
    return HTMLResponse("""
        <html>
            <head>
                <title>AI PDF Assistant</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        background-color: #f0f2f5;
                        margin: 0;
                        padding: 20px;
                    }
                    
                    .container {
                        max-width: 1000px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        padding: 20px;
                    }
                    
                    h1 {
                        color: #1a1a1a;
                        text-align: center;
                        margin-bottom: 20px;
                    }
                    
                    .upload-section {
                        background: #f8f9fa;
                        padding: 20px;
                        border-radius: 8px;
                        margin-bottom: 20px;
                        border: 2px dashed #dee2e6;
                        text-align: center;
                    }

                    /* Custom file input styling */
                    .file-input-container {
                        position: relative;
                        display: inline-block;
                        margin-right: 10px;
                    }

                    .file-input-container input[type="file"] {
                        position: absolute;
                        left: 0;
                        top: 0;
                        opacity: 0;
                        width: 100%;
                        height: 100%;
                        cursor: pointer;
                    }

                    .file-input-button {
                        background: #4a90e2;
                        color: white;
                        padding: 10px 20px;
                        border-radius: 5px;
                        cursor: pointer;
                        display: inline-block;
                    }

                    .file-name-display {
                        margin-top: 10px;
                        padding: 10px;
                        background: #e9ecef;
                        border-radius: 5px;
                        display: inline-block;
                        max-width: 300px;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        white-space: nowrap;
                    }
                    
                    #uploadForm {
                        display: flex;
                        gap: 10px;
                        justify-content: center;
                        align-items: center;
                        flex-wrap: wrap;
                    }
                    
                    .input-group {
                        display: flex;
                        gap: 10px;
                        margin-bottom: 20px;
                    }
                    
                    input[type="text"] {
                        flex: 1;
                        padding: 10px;
                        border: 1px solid #dee2e6;
                        border-radius: 5px;
                        font-size: 16px;
                    }
                    
                    input[type="text"]:focus {
                        outline: none;
                        border-color: #4a90e2;
                    }
                    
                    button {
                        background: #4a90e2;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        cursor: pointer;
                    }
                    
                    button:hover {
                        background: #357abd;
                    }
                    
                    #chatHistory {
                        height: 500px;
                        overflow-y: auto;
                        padding: 20px;
                        background: #f8f9fa;
                        border-radius: 8px;
                    }
                    
                    .chat-message {
                        margin-bottom: 10px;
                        padding: 10px;
                        border-radius: 8px;
                        max-width: 80%;
                    }
                    
                    .question {
                        background: #4a90e2;
                        color: white;
                        margin-left: auto;
                    }
                    
                    .answer {
                        background: #e9ecef;
                        color: #1a1a1a;
                        margin-right: auto;
                    }
                    
                    #uploadStatus {
                        margin-top: 10px;
                        text-align: center;
                    }
                    
                    .success {
                        color: #28a745;
                    }
                    
                    .error {
                        color: #dc3545;
                    }

                    .current-pdf {
                        margin-top: 15px;
                        padding: 10px;
                        background: #e3f2fd;
                        border-radius: 5px;
                        display: inline-block;
                    }

                    .pdf-icon {
                        color: #dc3545;
                        margin-right: 5px;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>AI PDF Assistant</h1>
                    
                    <div class="upload-section">
                        <form id="uploadForm">
                            <div class="file-input-container">
                                <div class="file-input-button">Choose PDF</div>
                                <input type="file" id="pdfFile" accept=".pdf" required>
                            </div>
                            <button type="submit">Upload PDF</button>
                        </form>
                        <div id="selectedFile" class="file-name-display" style="display: none;"></div>
                        <div id="uploadStatus"></div>
                        <div id="currentPdf" class="current-pdf" style="display: none;">
                            <span class="pdf-icon">📄</span>
                            <span id="pdfName"></span>
                        </div>
                    </div>

                    <div class="qa-section">
                        <div class="input-group">
                            <input id="questionInput" type="text" 
                                   placeholder="Ask a question about your PDF...">
                            <button onclick="askQuestion()">Ask</button>
                        </div>
                        <div id="chatHistory"></div>
                    </div>
                </div>

                <script>
                    const socket = new WebSocket("ws://localhost:8000/ws");
                    const chatHistory = document.getElementById("chatHistory");
                    const uploadStatus = document.getElementById("uploadStatus");
                    const pdfFile = document.getElementById("pdfFile");
                    const selectedFile = document.getElementById("selectedFile");
                    const currentPdf = document.getElementById("currentPdf");
                    const pdfName = document.getElementById("pdfName");

                    // Show selected filename
                    pdfFile.addEventListener('change', function() {
                        if (this.files[0]) {
                            selectedFile.style.display = 'inline-block';
                            selectedFile.textContent = this.files[0].name;
                        } else {
                            selectedFile.style.display = 'none';
                        }
                    });
                    
                    document.getElementById("uploadForm").onsubmit = async (e) => {
                        e.preventDefault();
                        const formData = new FormData();
                        const fileInput = document.getElementById("pdfFile");
                        
                        if (!fileInput.files[0]) {
                            uploadStatus.innerHTML = '<div class="error">Please select a PDF file</div>';
                            return;
                        }
                        
                        formData.append("file", fileInput.files[0]);
                        uploadStatus.innerHTML = '<div>Uploading...</div>';
                        
                        try {
                            const response = await fetch("/upload/", {
                                method: "POST",
                                body: formData
                            });
                            const result = await response.json();
                            
                            if (response.ok) {
                                uploadStatus.innerHTML = `<div class="success">${result.message}</div>`;
                                chatHistory.innerHTML = '';
                                // Show current PDF name
                                currentPdf.style.display = 'inline-block';
                                pdfName.textContent = fileInput.files[0].name;
                            } else {
                                uploadStatus.innerHTML = `<div class="error">${result.detail}</div>`;
                            }
                        } catch (error) {
                            uploadStatus.innerHTML = `<div class="error">Error: ${error.message}</div>`;
                        }
                    };
                    
                    function addMessage(text, isQuestion) {
                        const div = document.createElement('div');
                        div.className = `chat-message ${isQuestion ? 'question' : 'answer'}`;
                        div.textContent = text;
                        chatHistory.appendChild(div);
                        chatHistory.scrollTop = chatHistory.scrollHeight;
                    }
                    
                    function askQuestion() {
                        const input = document.getElementById("questionInput");
                        const question = input.value.trim();
                        
                        if (question) {
                            addMessage(question, true);
                            socket.send(question);
                            input.value = '';
                        }
                    }
                    
                    document.getElementById("questionInput").onkeypress = (e) => {
                        if (e.key === "Enter") {
                            askQuestion();
                        }
                    };
                    
                    socket.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        if (data.error) {
                            addMessage(`Error: ${data.error}`, false);
                        } else {
                            addMessage(data.response, false);
                        }
                    };
                    
                    socket.onerror = (error) => {
                        addMessage(`WebSocket Error: ${error.message}`, false);
                    };
                </script>
            </body>
        </html>
    """)
