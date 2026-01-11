import ollama
from retriever import loader, embedding, find_similarity, filter_by_metadata
from state import TriagState
import json



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


def build_prompt(context, user_query, state: TriagState):

    return f"""
    You are a medical triage assistant.
You do NOT diagnose.
You assess urgency only.

Your goal is to assign a triage level as early as possible.

Before responding, silently decide:
- Is the information sufficient to assign a triage level with reasonable uncertainty?

If YES → output FINAL TRIAGE immediately.
If NO → ask ONE follow-up question.

Rules:
- Ask at most {state.max_questions} total questions
- If you have 0 questions remaining, you MUST output FINAL TRIAGE
- Do NOT ask questions already asked
- Be concise
- No paragraphs
- Always express uncertainty
- Use ONLY the provided medical context

CRITICAL SAFETY RULE:
If ANY retrieved medical context has urgency = "high",
you must immediately output FINAL TRIAGE.
Do NOT ask follow-up questions.

Triage levels:
- stay_home
- see_gp
- urgent_gp
- call_911

Conversation so far:
{state.build_memory()}

Medical context:
{context}

User input:
{user_query}

Respond ONLY in valid JSON.

If asking a question:

  "type": "question",
  "question": "..."


If giving final triage:

  "type": "triage",
  "level": "...",
  "confidence": "low | medium | high",
  "what_to_do": ["..."],
  "watch_for": ["..."]


   
    """

def build_final_prompt(context, state: TriagState):
    return f"""
You are a medical triage assistant.

IMPORTANT:
- You are NOT allowed to ask questions
- You MUST give a final triage decision
- You MUST choose exactly one triage level
- You do NOT diagnose
- You MUST be brief and cautious

TRIAGE LEVELS:
- stay_home
- see_gp
- urgent_gp
- call_911

Conversation summary:
{state.build_memory()}

Medical context:
{context}

Respond ONLY in valid JSON:

"type": "triage",
"level": "...",
"confidence": "low | medium | high",
"what_to_do": ["one short action"],
"watch_for": ["one short warning"]
"""


def ask_llm(prompt):
    response = ollama.chat(
        model= "qwen2.5:7b-instruct",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"]

if __name__ == "__main__":

    index, documents = loader(
        "../embeddings/vector_store/faiss.index",
        "../embeddings/vector_store/documents.json"
    )

    state = TriagState()

    user_query = input("Describe your symptoms: ")

    # 🔹 RAG ONCE
    vector = embedding(user_query, "all-MiniLM-L6-v2")
    retrieved = find_similarity(vector, 5, index, documents)
    retrieved = filter_by_metadata(retrieved)

    context = build_context(retrieved)

    while state.should_continue():
       
        prompt = build_prompt(context, user_query, state)
        output = ask_llm(prompt)

        print("\nMODEL OUTPUT:\n", output)

        try:
            result = json.loads(output)
        except json.JSONDecodeError:
            print("Invalid JSON from model.")
            break

        if result["type"] == "triage":
            print("\nFINAL TRIAGE RESULT:")
            print(result)
            break

        if result["type"] == "question":
            answer = input(result["question"] + " ")
            state.add_turn(result["question"], answer)
            user_query = answer  # feed answer back to LLM
        

    if state.num_questions == state.max_questions:
        print("\nReaching final triage...\n")

        final_prompt = build_final_prompt(context, state)
        final_output = ask_llm(final_prompt)

            #final_result = json.loads(final_output)

        print("\nFINAL TRIAGE RESULT:")
        print(final_output)
