from PyPDF2 import PdfReader
from dotenv import load_dotenv
import os
import io
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate 
import shutil
import time

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

def get_pdf_text(pdf_content: bytes) -> str:
    try:
        # Create BytesIO object from bytes
        pdf_stream = io.BytesIO(pdf_content)
        
        # Create PDF reader
        pdf_reader = PdfReader(pdf_stream)
        
        # Extract text
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
            
        return text
    except Exception as e:
        print(f"Error in get_pdf_text: {str(e)}")
        raise

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=500)
    return text_splitter.split_text(text)

def get_vector_store(text: str):
    try:
        text_chunks = get_text_chunks(text)
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        
        # Create faiss directory if it doesn't exist
        os.makedirs("faiss", exist_ok=True)
        
        # Remove existing files with error handling
        faiss_files = ["faiss/index.faiss", "faiss/index.faiss.pkl"]
        for file_path in faiss_files:
            if os.path.exists(file_path):
                try:
                    # Try to remove file
                    os.remove(file_path)
                except (PermissionError, OSError):
                    try:
                        # If remove fails, try to rename/move it
                        backup_path = f"{file_path}.{int(time.time())}.bak"
                        shutil.move(file_path, backup_path)
                    except Exception as e:
                        print(f"Failed to handle existing file {file_path}: {str(e)}")
                        # If both attempts fail, try to clear the file contents
                        with open(file_path, 'w') as f:
                            f.truncate(0)

        # Small delay to ensure file system operations are complete
        time.sleep(0.1)
        
        # Create new vector store
        vector_store = FAISS.from_texts(text_chunks, embeddings)
        
        # Save the new vector store
        try:
            vector_store.save_local("faiss/index.faiss")
            print("Vector store updated successfully")
        except Exception as save_error:
            print(f"Error saving vector store: {str(save_error)}")
            raise
            
        return text_chunks
        
    except Exception as e:
        print(f"Error in get_vector_store: {str(e)}")
        raise

def get_conversational_chain():
    prompt_template = """
    You are a QA bot that answers questions based solely on the provided document. If you are confident in your answer based on the 
    context retrieved from the document, provide a detailed response. If the context does not provide enough information or you are 
    unsure, respond with, 'The information is not available in the document.'
    Context :\n {context}\n
    Question :\n {question}\n
    
    Answer :
    """
    model = ChatGoogleGenerativeAI(model='gemini-pro', temperature=0.4)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    return load_qa_chain(model, chain_type="stuff", prompt=prompt)

def user_input(user_question):
    try:
        print("\n=== Processing User Input ===")
        print(f"Question received: {user_question}")
        
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        print("✓ Created embeddings")
        
        if not os.path.exists("faiss/index.faiss"):
            print("✗ FAISS index not found!")
            return "Error: Please upload a PDF document first.", []
            
        print("Loading vector store...")
        vector_store = FAISS.load_local("faiss/index.faiss", embeddings, allow_dangerous_deserialization=True)
        print("✓ Vector store loaded successfully")
        
        print("\nSearching for relevant documents...")
        docs = vector_store.similarity_search(user_question, k=7)
        print(f"✓ Found {len(docs)} relevant documents")
        
        if not docs:
            print("✗ No relevant documents found!")
            return "No relevant information found in the document.", []
            
        matched_docs = [doc.page_content for doc in docs]
        print("\nGenerating response...")
        chain = get_conversational_chain()
        
        print("Processing through LLM...")
        response = chain(
            {"input_documents": docs, "question": user_question}, 
            return_only_outputs=True
        )
        
        print("\n=== Response Generated ===")
        print(f"Response: {response['output_text']}")
        print("=" * 50)
        
        return response['output_text'], matched_docs
        
    except Exception as e:
        print(f"\n✗ Error in user_input: {str(e)}")
        return f"Error: {str(e)}", []
