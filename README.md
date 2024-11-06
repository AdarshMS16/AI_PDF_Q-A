# AI_PDF_Q-A
The AI chatbot which does Q&amp;A on uploaded pdf
DOCUMENTATION FOR PDF ASSISTANT



 AI PDF Assistant

A web-based application that allows users to upload PDF documents and interact with them through natural language questions. The application uses Google's Generative AI to provide accurate responses based on the PDF content.

## Features

- PDF document upload and processing
- Real-time question-answering capabilities
- Interactive chat interface
- Document context maintenance
- Support for multiple document types
- WebSocket-based communication for real-time responses

## Prerequisites

Before running the application, ensure you have the following installed:

- Python 3.8 or higher
- pip (Python package installer)
- Google API key for Generative AI

## Installation

1. Clone the repository:

bash
git clone <repository-url>
cd AIplanet

2. Create a virtual environment:
bash
python -m venv venv

3. Activate the virtual environment:
- Windows:
bash
venv\Scripts\activate
bash
source venv/bin/activate
4. Install required packages:

bash
pip install -r requirements.txt

## Required Packages

Create a `requirements.txt` file with the following dependencies: fastapi
uvicorn
python-multipart
python-dotenv
langchain
langchain-google-genai
google-generativeai
PyPDF2
faiss-cpu
sqlalchemy


## Environment Setup

1. Create a `.env` file in the root directory
2. Add your Google API key:
## Running the Application

1. Start the server:
bash
uvicorn app:app –reload
2. Open your web browser and navigate to:
http://localhost:8000

## Usage

1. **Upload PDF**
   - Click "Choose PDF" button
   - Select your PDF file
   - Click "Upload PDF" button
   - Wait for confirmation message

2. **Ask Questions**
   - Type your question in the input field
   - Press Enter or click "Ask" button
   - Wait for the AI response

## Features in Detail

### PDF Processing
- Extracts text from PDF documents
- Creates embeddings for efficient searching
- Stores document context for future reference

### Question Answering
- Uses Google's Generative AI
- Maintains conversation context
- Provides relevant answers based on document content

### User Interface
- Clean, modern design
- Real-time response display
- Error handling and status updates
- PDF file name display
- Chat-like interface for Q&A

## Error Handling

The application includes error handling for:
- Invalid file types
- Upload failures
- Processing errors
- API connection issues
- Invalid questions

## Security Features

- Rate limiting on API endpoints
- File type validation
- Maximum file size restrictions
- Secure WebSocket connections

## Limitations

- Currently supports PDF files only
- Maximum file size limit
- Requires active internet connection
- API key rate limits apply

## Troubleshooting

1. **PDF Upload Fails**
   - Check file size
   - Ensure PDF is not corrupted
   - Verify file permissions

2. **No Response to Questions**
   - Check internet connection
   - Verify API key is valid

1  Ensure PDF was uploaded successfully
2  Server Won't Start
3  check if port 8000 is available
4  Verify all dependencies are installed
5  Ensure Python version is compatible
Contributing
1  Fork the repository
2  Create your feature branch
3  Commit your changes
4  Push to the branch
5  Create a new Pull Request
License
This project is licensed under the MIT License - see the LICENSE file for details
Acknowledgments
1  Google Generative AI

2  FastAPI framework
3  LangChain library
4  FAISS by Facebook Research
Support
For support, please open an issue in the repository or contact the maintainers.
Future Enhancements
1.Support for more document types
2.Multi-language support
3.Document comparison features
4.Enhanced error handling
5.User authentication
6.Document history tracking
7.Export conversation feature

This README provides:
1. Clear installation instructions
2. Usage guidelines
3. Project structure
4. Troubleshooting tips
5. Future enhancement plans
6. Security considerations
7. Detailed feature explanations

