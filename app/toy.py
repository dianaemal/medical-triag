from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import ollama
import json
import re
import sys
from pathlib import Path

# Add parent directory to path to import rag modules
sys.path.append(str(Path(__file__).parent.parent))

from rag.retriever import loader, embedding, find_similarity, filter_by_metadata
from rag.state import TriagState
from rag.safety import SafetyDetector

app = FastAPI(title="Medical Triage API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Session storage (in production, use Redis or database)
#session is a dictionary that have string as keys and dict as values
sessions: Dict[str, Dict] = {}

# Initialize components
CONFIDENCE_THRESHOLD = 0.75
safety = SafetyDetector(
    embed_fn=lambda t: embedding(t, "all-MiniLM-L6-v2"),
    threshold=0.85
)

# Load FAISS index and documents
INDEX_PATH = str(Path(__file__).parent.parent / "embeddings" / "vector_store" / "faiss.index")
DOCUMENTS_PATH = str(Path(__file__).parent.parent / "embeddings" / "vector_store" / "documents.json")

index, documents = loader(INDEX_PATH, DOCUMENTS_PATH)


# Request/Response models
class SymptomRequest(BaseModel):
    symptoms: str
    session_id: Optional[str] = None


class AnswerRequest(BaseModel):
    session_id: str
    answer: str


class SessionResponse(BaseModel):
    session_id: str
    type: str
    question: Optional[str] = None
    triage_result: Optional[Dict] = None
    message: Optional[str] = None


def build_context(retrieved_docs):
    context = ""
    for doc in retrieved_docs:
        meta = doc["metadata"]
        context += f"""
        Condition: {meta['condition']}
        Section: {meta['section']}
        Urgency: {meta['urgency']}
        Information: {doc['text']}
        ---
        """
    return context.strip()


def build_prompt(user_query, state: TriagState):
    return f"""
        You are a medical triage question generator.

    Your job:
    - Identify the SINGLE most important missing piece of information
    - Ask ONE concise question to reduce uncertainty
    - OR stop if enough info is available
    - OR escalate immediately if red flags are present

    Hard rules:
    - Ask only ONE question
    - Do NOT repeat or rephrase previous questions
    - Do NOT ask about symptoms already mentioned
    - Do NOT ask low-impact questions
    - If red flags from bellow are clearly present → escalate immediately and STOP asking further questions
    - If uncertainty is low → stop asking questions

    Red flags:
    {', '.join(state.red_flags)}

    Conversation summary:
    {state.build_summary()}

    Latest user input:
    {user_query}

    First decide internally:
    1. What critical information is missing?
    2. Does it affect urgency?

    Respond STRICTLY in JSON:

    If asking a question:
    {{
    "type": "ask",
    "reason": "what uncertainty this question resolves",
    "question": "one short, specific question",
    "confidence": 0.0–1.0
    }}

    If escalating immediately:
    {{
    "type": "escalate",
    "level": "call_911 | urgent_gp",
    "reason": "brief reason"
    }}

    If enough info is collected:
    {{
    "type": "stop",
    "confidence": 0.0–1.0
    }}
"""


def build_retrieval_query(state: TriagState):
    prompt = f"""
    You are a medical query generator.

    Given the conversation summary below, produce a concise medical
    search query that would retrieve relevant clinical triage information.
    Do not include the symptoms that are not present.

    Conversation:
    {state.build_memory()}

    Output ONLY the query.
    """
    return prompt


def build_final_prompt(context, summary):
    return f"""
    You are a medical triage assistant.

    IMPORTANT:
    - You are NOT allowed to ask questions
    - You MUST give a final triage decision
    - You MUST choose exactly one triage level
    - You do NOT diagnose
    - You MUST be brief and cautious
    - You MUST use the provided medical context
    - If context is insufficient, choose the safer triage level

    TRIAGE LEVELS:
    - stay_home
    - see_gp
    - urgent_gp
    - call_911

    Conversation summary:
    {summary}

    Medical context:
    {context}

    Respond STRICTLY in valid JSON:
{{
    "type": "triage",
    "level": "...",
    "confidence": "low | medium | high",
    "what_to_do": ["one short action"],
    "watch_for": ["one short warning"]
}}
"""


def extract_json(text):
    match = re.search(r'\{[\s\S]*\}', text)
    return match.group(0) if match else None


def clean_query(text):
    return re.sub(r'[^a-zA-Z0-9 ,\-]', '', text).strip()


def ask_llm(prompt):
    response = ollama.chat(
        model="qwen2.5:7b-instruct",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"]


def perform_final_triage(state: TriagState):
    """Perform final triage decision after collecting enough information"""
    retrieval_prompt = build_retrieval_query(state)
    retrieval_query = ask_llm(retrieval_prompt).strip()
    clean_retrieval_query = clean_query(retrieval_query)
    
    vector = embedding(clean_retrieval_query, "all-MiniLM-L6-v2")
    retrieved = find_similarity(vector, 5, index, documents)
    retrieved = filter_by_metadata(retrieved)
    
    context = build_context(retrieved)
    summary = state.build_memory()
    
    final_prompt = build_final_prompt(context, summary)
    final_output = ask_llm(final_prompt)
    
    match = extract_json(final_output)
    if match:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            return None
    return None


@app.get("/")
def root():
    return {"message": "Medical Triage API", "status": "running"}

@app.post("/api/triag/start", response_model= SessionResponse)
def start_triag(request: SymptomRequest):
    import uuid
    session_id = request.session_id or str(uuid.uuid4())

    user_query = request.symptoms

    safety_level = safety.check(user_query)

    if safety_level:
        result = {
            "type": "triage",
            "level": safety_level,
            "confidence": "high",
            "what_to_do": ["Call emergency services immediately"],
            "watch_for": []
        }

        sessions[session_id] = {
            "state" : None,
            "completed": True,
            "result": result
        }

        return SessionResponse(
            session_id= session_id,
            type= "Triag",
            triage_result= result
        )
    

    state = TriagState()

    state.add_turn("What are your symptoms?", user_query)
    prompt = build_prompt( user_query, state)
    output = ask_llm(prompt)
    match = extract_json(output)
    if match:
        try:
            result = json.loads(match)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON from model")
    else:
        raise HTTPException(status_code=500, detail="No JSON found in model response")
    
    sessions[session_id] = {
        "state": state,
        "completed": False,
        "result": None,
        "last_question": None
    }

    # if result is escalate:
    if result.get("type") == "escalate":

        triag_result = {
            "type": "triage",
            "level": result.get("level", "urgent_gp"),
            "confidence": "high",
            "what_to_do": [result.get("reason", "Seek immediate medical attention")],
            "watch_for": []
        }
        sessions[session_id]["completed"] = True
        sessions[session_id]["result"] = triag_result

        return SessionResponse(
            session_id= session_id,
            type= "Triag",
            triage_result= triag_result
        )
    
    if result.get("type") == "ask":
        sessions[session_id]["last_question"] = result.get("question")
        return SessionResponse(
            session_id=session_id,
            type= "ask",
            question=result.get("question")
        )
    
    elif result.get("type") == "stop":
        triag_result = perform_final_triage(state)
        sessions[session_id]["completed"] = True
        sessions[session_id]["result"] = triag_result

        return SessionResponse(
            session_id=session_id,
            type="Triag",
            triage_result=triag_result
        )
    

@app.post("/api/triage/answer", response_model=SessionResponse)
def answer_question(request : AnswerRequest):

    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[request.session_id]
    if session["completed"]:
        return SessionResponse(
            session_id=request.session_id,
            type = "Triag",
            triage_result=session["result"],
            message = "Session already completed."

        )

    state = session["state"]
    user_query = request.answer.strip()

    if "last_question" in session and session["last_question"]:
        state.add_turn(session["last-question"], request.answer)
        session["last_question"] = None

    if state.should_continue():
        prompt = build_prompt(user_query, state)
        output = ask_llm(prompt)
        match = extract_json(output)
        if match:
            try:
                result = json.loads(match)
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="Invalid JSON from model")
        else:
            raise HTTPException(status_code=500, detail="No JSON found in model response")

        if result.get("type") == "escalate":
            
            triag_result = {
                "type": "triage",
                "level": result.get("level", "urgent_gp"),
                "confidence": "high",
                "what_to_do": [result.get("reason", "Seek immediate medical attention")],
                "watch_for": []
            }

            session["completed"] = True
            session["result"] = triag_result

            return SessionResponse(
                session_id=request.session_id,
                type="Triag",
                triage_result=triag_result
            )
        
        elif result.get("type") == "ask":

            session["last_question"] = result.get("question")

            return SessionResponse(
                session_id=request.session_id,
                type="ask",
                question=result.get("question")
            )
        
        elif result.get("type") == "stop":

            triag_result = perform_final_triage(state)
            session["completed"] = True
            session["result"] = triag_result

            return SessionResponse(
                session_id=request.session_id,
                type="Triag",
                triage_result=triag_result
            )
        

    # stop condition or questions are over
    final_triag = perform_final_triage(state)
    session["completed"] = True
    session["result"] = final_triag

    return SessionResponse(
        session_id=request.session_id,
        type="Triag",
        triage_result=triag_result
    )

@app.get("/api/triag/sesssion/{session_id}")
def get_session(session_id : str):

    if session_id not in sessions:
        raise HTTPException()
    
    session = sessions.get(session_id)
    





        

    

    






        

    







