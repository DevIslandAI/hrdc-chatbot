# HRDC Document Assistant

A RAG (Retrieval-Augmented Generation) chatbot for the HRDC Training Grant System.

## 🌟 Overview

This project scrapes the HRDC website for publication documents, processes them into high-quality text chunks, and stores them in a PostgreSQL database with vector embeddings. It provides a conversational interface for users to ask questions about the training grant system, citing specific source documents in its answers.

## 🛠️ Components

- **`scraper.py`**: Web scraper for HRDC documents.
- **`document_processor.py`**: PDF/Word text extraction and intelligent chunking.
- **`database.py`**: PostgreSQL management with metadata and JSONB support.
- **`chatbot.py`**: Embedding generation and semantic search logic.
- **`main.py`**: End-to-end pipeline orchestrator.
- **`app.py`**: Flask web application and UI.

## 🚀 Quick Start

1. **Install Dependencies**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configuration**:
   Copy `.env.example` to `.env` and fill in your PostgreSQL credentials from EasyPanel.

3. **Initalize & Run Pipeline**:
   ```bash
   python main.py
   ```

4. **Launch Chatbot**:
   ```bash
   python app.py
   ```
   Access at `http://localhost:5001`.

## 📄 Documentation

For a detailed technical deep-dive into the architecture and implementation, see the [Project Walkthrough](file:///Users/ryan/.gemini/antigravity/brain/9120afbf-de26-4809-8b35-302f0f9dd83b/walkthrough.md).

## 🚀 Deployment

### 1. Push to GitHub
```bash
# Initialize git (if not done)
git init
git add .
git commit -m "Initial commit"

# Add your repository (Replace URL with your own)
git remote add origin https://github.com/YOUR_USERNAME/hrdc-chatbot.git
git push -u origin main
```

### 2. Deploy on EasyPanel
1. Create a new "App" service in your project.
2. Select your GitHub repository.
3. Choose **Docker** as the build method.
4. Set the **Environment Variables**:
   - `OPENAI_API_KEY`: sk-proj-...
   - `DATABASE_HOST`: "postgres" (internal service name)
   - `DATABASE_USER`: "postgres"
   - `DATABASE_PASSWORD`: "password"
   - `DATABASE_NAME`: "hrdc2"
   - `EMBEDDING_MODEL_NAME`: "text-embedding-3-small"
   - `LLM_MODEL`: "gpt-4o-mini"
5. Deploy!

### 3. Initialize Production Database
Since your local documents are not uploaded (thankfully!), the production database starts **empty**.
To fill it:
1. Go to your **App Service** in EasyPanel.
2. Click the **Console** tab.
3. Type: `python main.py` and hit Enter.
   *(This will scrape the documents, process them, and upload them to your live database. It takes about 1-2 minutes.)*
