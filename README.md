# Medical Triage Assistant

A professional medical triage system with an AI-powered symptom assessment tool. The system uses RAG (Retrieval Augmented Generation) to provide accurate triage recommendations based on user symptoms.

## Features

-  AI-powered symptom assessment using Ollama
-  RAG-based medical context retrieval using FAISS
-  Emergency detection and immediate escalation
-  Interactive Q&A to gather comprehensive symptom information
-  Four-level triage system:
  - `stay_home` - Self-care recommended
  - `see_gp` - Schedule appointment with GP
  - `urgent_gp` - Urgent care needed
  - `call_911` - Emergency, call 911 immediately
-  Modern, responsive frontend built with React and Tailwind CSS
-  Fast API backend built with FastAPI

## Project Structure

```
medical-triag/
├── app/
│   └── api.py              # FastAPI backend
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── ChatMessage.jsx
│   │   │   ├── TriageResult.jsx
│   │   │   └── InputForm.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── rag/                    # RAG pipeline components
│   ├── pipeline.py
│   ├── retriever.py
│   ├── safety.py
│   └── state.py
├── data/                   # Medical data
│   ├── raw/
│   └── processed/
├── embeddings/             # Vector store
│   └── vector_store/
└── requirements.txt
```

## Prerequisites

- Python 3.8+
- Node.js 16+ and npm
- Ollama installed and running with `qwen2.5:7b-instruct` model

### Installing Ollama and Model

1. Install Ollama from https://ollama.ai
2. Pull the required model:
```bash
ollama pull qwen2.5:7b-instruct
```

## Installation

### Backend Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

## Running the Application

### Start the Backend

1. Make sure Ollama is running:
```bash
ollama serve
```

2. Start the FastAPI server:
```bash
# From the project root
python -m uvicorn app.api:app --reload --port 8000
```

The API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

### Start the Frontend

1. From the `frontend` directory:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Usage

1. Open your browser and navigate to `http://localhost:3000`
2. Enter your symptoms in the input field
3. Answer any follow-up questions from the AI
4. Receive a triage assessment with recommended actions

## API Endpoints

### POST `/api/triage/start`
Start a new triage session.

**Request:**
```json
{
  "symptoms": "I have chest pain and shortness of breath"
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "type": "ask" | "triage",
  "question": "string (if type is ask)",
  "triage_result": { ... } (if type is triage)
}
```

### POST `/api/triage/answer`
Answer a question in an ongoing session.

**Request:**
```json
{
  "session_id": "uuid",
  "answer": "Yes, the pain started 30 minutes ago"
}
```

### GET `/api/triage/session/{session_id}`
Get the status of a session.

## Development

### Backend Development

The FastAPI backend includes:
- Automatic API documentation at `/docs`
- CORS middleware configured for frontend communication
- Session management for triage conversations
- Integration with Ollama for LLM inference
- FAISS-based vector search for medical context retrieval

### Frontend Development

The React frontend is built with:
- Vite for fast development and building
- Tailwind CSS for styling
- Axios for API communication
- Modern React hooks for state management

## Important Notes

⚠️ **Disclaimer**: This is an AI-powered triage assistant and should **NOT** replace professional medical advice. In case of emergency, call 911 immediately.

## Troubleshooting

### Ollama Connection Issues
- Ensure Ollama is running: `ollama serve`
- Verify the model is installed: `ollama list`
- Check the model name matches `qwen2.5:7b-instruct`

### CORS Issues
- Verify the frontend URL is in the CORS allowed origins in `app/api.py`
- Default: `http://localhost:3000` and `http://localhost:5173`

### Vector Store Issues
- Ensure `embeddings/vector_store/faiss.index` and `documents.json` exist
- If missing, you may need to run the embedding generation script

## License

This project is for educational purposes.

