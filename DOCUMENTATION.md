# HRDC Document Assistant - Full Technical Documentation

## 📋 Project Overview
The HRDC Document Assistant is a high-performance Retrieval-Augmented Generation (RAG) system. It automates the extraction of official documents from the HRDC website, processes them into a searchable knowledge base, and provides an interactive AI chatbot to answer queries regarding the Training Grant System.

---

## �️ Technologies & Tools Used

### Core Infrastructure
- **Python 3.9**: Principal programming language.
- **PostgreSQL**: Relational database for metadata and document storage.
- **EasyPanel**: Used for hosting and managing the PostgreSQL instance.
- **Flask**: Web framework used for the chatbot interface and API.

### AI & Natural Language Processing
- **Sentence-Transformers (`all-MiniLM-L6-v2`)**: Used for generating 384-dimensional vector embeddings locally (no external API calls needed for retrieval).
- **LangChain**: Framework used to orchestrate the RAG (Retrieval-Augmented Generation) flow.
- **NumPy**: Used for performing manual cosine similarity calculations for semantic search.

### Data Extraction & Processing
- **BeautifulSoup4 & Requests**: Used for initial website crawling and metadata extraction.
- **Browser Automation**: Used to bypass advanced anti-bot protections to extract document dates and titles.
- **PyPDF2 / pdfplumber**: Used for extracting clean text from PDF documents.
- **python-docx**: Used for extracting text from Microsoft Word documents.

---

## 🏗️ Technical Architecture

### 1. Advanced Web Scraper (`scraper.py`)
- **Anti-Bot Navigation**: Implements custom browser headers and session management.
- **Metadata Extraction**: Scrapes the publication date of documents by interacting with "Details" buttons.
- **Categorization**: Groups the 31 documents by their specific release dates:
  - 25 April 2024 (21 documents)
  - 29 July 2024 (5 documents)
  - 30 January 2026 (4 documents + 1 summary)

### 2. Intelligent Document Processor (`document_processor.py`)
- **Cleaning**: Removes redundant whitespace and noise from extracted text.
- **Recursive Chunking**: Splits large documents into segments of ~1000 characters with a 100-character overlap. This ensures the AI model has enough context for each snippet while staying within token limits.

### 3. Database Layer (`database.py`)
- **Fresh Instance**: Configured on a new PostgreSQL host (`hrdc2`) for a clean production start.
- **JSONB Vector Storage**: Implemented a custom solution to store embeddings in JSONB format because the server lacked the `pgvector` extension.
- **Schema Design**:
  - `documents` table: ID, Title, Filename, Date, Download URL, Local Path.
  - `document_content` table: ID, Document Link, Chunk Index, Content, Embedding (JSONB).

### 4. Semantic Search & Chatbot (`chatbot.py` & `app.py`)
- **Embeddings**: Text queries are converted into vectors in real-time.
- **Cosine Similarity**: The system performs a mathematical similarity check between the user's query and the 160+ stored chunks.
- **RAG Response**: The chatbot identifies the top-3 most relevant chunks, retrieves the original PDFs, and generates a response that includes clickable source links and document dates.

---

## 📁 Project Directory Structure

```text
hrdc_chatbot/
├── app.py              # Flask Web Server
├── chatbot.py          # RAG & AI Logic
├── config.py           # Configuration Management
├── database.py         # PostgreSQL Interface
├── document_processor.py# Text Extraction Engine
├── main.py             # Full Pipeline Orchestrator (Run this first)
├── scraper.py          # HRDC Web Scraper
├── test_chatbot.py     # Terminal-based test script
├── .env                # Environment Credentials
├── README.md           # Quick-start guide
├── DOCUMENTATION.md    # This file
├── downloads/          # Local storage for 31 official documents
├── static/             # CSS & JavaScript for UI
└── templates/          # HTML templates for Chatbot
```

---

## � Deployment & Usage

### 1. Installation
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Running the Full Pipeline
The pipeline handles scraping (if needed), document processing, and database uploading in one command:
```bash
python main.py
```

### 3. Starting the Web UI
```bash
python app.py
```
*Note: The server runs on **port 5001** by default to avoid system conflicts on macOS.*

---

## 💡 Technical Decisions & Solutions
- **Port 5001**: Changed from 5000 to avoid conflicts with macOS AirPlay Receiver.
- **JSONB Similarity**: Developed a custom Python-based similarity engine to overcome the absence of `pgvector` on the hosted PostgreSQL instance, ensuring the project remains portable and functional on standard database images.
- **Local Embeddings**: Chose `all-MiniLM-L6-v2` for a balance of speed and accuracy, allowing the system to run without expensive GPU requirements or API costs.
