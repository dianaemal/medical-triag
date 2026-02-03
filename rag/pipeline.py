import ollama
from retriever import loader, embedding, find_similarity, filter_by_metadata
from state import TriagState
import json
import re
from safety import SafetyDetector


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
    print(f"Context : {context}")
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
        model= "qwen2.5:7b-instruct",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"]

if __name__ == "__main__":
    confidence = 0.75
    safety = SafetyDetector(
    embed_fn=lambda t: embedding(t, "all-MiniLM-L6-v2"),
    threshold=0.85
)
    index, documents = loader(
        "../embeddings/vector_store/faiss.index",
        "../embeddings/vector_store/documents.json"
    )

    state = TriagState()

    user_query = input("Describe your symptoms: ")
    safety_level = safety.check(user_query)

    if safety_level:
        print({
            "type": "triage",
            "level": safety_level,
            "confidence": "high",
            "what_to_do": ["Call emergency services immediately"],
            "watch_for": []
        })
        exit()
    
    state.add_turn("What are your symptoms?", user_query)

   
    
    while state.should_continue():
       
        prompt = build_prompt( user_query, state)
        output = ask_llm(prompt)

        print("\nMODEL OUTPUT:\n", output)

        match = extract_json(output)
        if match:

            try:
                result = json.loads(match)
            except json.JSONDecodeError:
                print("Invalid JSON from model.")
             
        else:
            result = None

        if result["type"] == "escalate":
            break

        if result["type"] == "ask":
            answer = input(result["question"] + " ")
            state.add_turn(result["question"], answer)
            user_query = answer  # feed answer back to LLM

        if result["type"] == "stop":
            if result["confidence"] >= confidence:
                break
    
        
    
    retrieval_prompt = build_retrieval_query(state)
    retrieval_query = ask_llm(retrieval_prompt).strip()
    clean_retrieval_query = clean_query(retrieval_query)

    print(clean_retrieval_query)
    print(retrieval_query)

    vector = embedding(clean_retrieval_query, "all-MiniLM-L6-v2")
    retrieved = find_similarity(vector, 5, index, documents)
    retrieved = filter_by_metadata(retrieved)

    context = build_context(retrieved)


    #if state.num_questions == state.max_questions:
    print("\nReaching final triage...\n")

    final_prompt = build_final_prompt(context, retrieval_query)
    final_output = ask_llm(final_prompt)

        #final_result = json.loads(final_output)

    print("\nFINAL TRIAGE RESULT:")
    print(final_output)
