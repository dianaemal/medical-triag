#!/bin/bash

# Start the FastAPI backend server
echo "Starting Medical Triage API..."
echo "Make sure Ollama is running (ollama serve)"
echo ""

python -m uvicorn app.api:app --reload --port 8000

