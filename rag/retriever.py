import faiss
import json
from sentence_transformers import SentenceTransformer
import os
os.environ["TRANSFORMERS_NO_TF"] = "1"
def loader(index_path, documents_path):
    index = faiss.read_index(index_path)

    with open(documents_path, "r") as f:
        documents = json.load(f)

    return index, documents


def embedding(query, model):

    model = SentenceTransformer(model)
    # FAISS expected 2D array so query has to be shape:(1,dim)
    query_vector = model.encode([query], convert_to_numpy=True)
    return query_vector

def find_similarity(query_vector, k, index, documents):

    distances, indices = index.search(query_vector, k)
    result = []
    for ind in indices[0]:
        document = documents[ind]
        result.append(document)

    return result

def filter_by_metadata(results, max_docs = 6):
    high = []
    low = []
    mid = []

    for doc in results:

        urgency = doc["metadata"]["urgency"]

        if urgency == "high":
            high.append(doc)
        elif urgency == "medium":
            mid.append(doc)
        else:
            low.append(doc)

    final = high.copy()

    for g in [mid, low]:
        for doc in g:
            if len(final) < max_docs:
                final.append(doc)

    
    return final




index, document = loader("../embeddings/vector_store/faiss.index", "../embeddings/vector_store/documents.json" )
vector = embedding("I am not feeling well", "all-MiniLM-L6-v2")
results1 = find_similarity(vector, 6, index, document)
results = filter_by_metadata(results1)

for r in results:

    print("----")
    print("TEXT:", r["text"])
    print("METADATA:", r["metadata"])

