import ollama
from retriever import loader, embedding, find_similarity, filter_by_metadata
from state import TriagState
import json
import re



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


def build_prompt( user_query, state: TriagState):

    return f"""
    You are a medical triage assistant.

    Your role:
    - Decide if you need MORE information
    - Or if symptoms suggest IMMEDIATE danger
    - Or if enough info is collected

    Rules:
    - Ask ONLY one question
    - Ask at most {state.max_questions - state.num_questions} more questions
    - Do NOT diagnose
    - Do NOT explain
    - Do NOT ask questions that you have already asked based on the conversation summary bellow
    - If red flags appear → escalate immediately and STOP asking further questions

    Red flags:
    {', '.join(state.red_flags)}


    Conversation so far:
    {state.build_memory()}

    User input:
    {user_query}

    Respond STRICTLY in JSON.

    If asking a question:
    {{
    "type": "ask",
    "question": "...",
    "confidence": 0.0–1.0,
    }}

    If escalating immediately:
    {{
    "type": "escalate",
    "level": "call_911 | urgent_gp"
    }}

    If enough info:
    {{
    "type": "stop",
    "confidence": 0.0–1.0,
    }}

"""
def build_retrieval_query(state: TriagState):
    prompt = f"""
    You are a medical query generator.

    Given the conversation summary below, produce a concise medical
    search query that would retrieve relevant clinical triage information.

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
    - If the conversation summary and medical context were not relevent to each other, ignore the context

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

    "type": "triage",
    "level": "...",
    "confidence": "low | medium | high",
    "what_to_do": ["one short action"],
    "watch_for": ["one short warning"]
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
    index, documents = loader(
        "../embeddings/vector_store/faiss.index",
        "../embeddings/vector_store/documents.json"
    )

    state = TriagState()

    user_query = input("Describe your symptoms: ")

   
    
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
