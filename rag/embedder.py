from sentence_transformers import SentenceTransformer
import json
from pathlib import Path
import faiss

#model = SentenceTransformer("all-MiniLM-L6-v2")

def load_processed_docs(forlde_path):

    docs = []

    for file in Path(forlde_path).glob("*.json"):
        with open(file, "r") as f:
            docs.extend(json.load(f))

    return docs

documents = load_processed_docs("../data/processed")

def creat_embedding(documents):

    model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [doc["text"] for doc in documents]
    embedding = model.encode(
        texts,
        # has to be numpy array to be saved in FAISS
        convert_to_numpy=True
        )
    return embedding

def save_to_faiss(embeddings, documents):

    # create an empty vector space
    dimension = embeddings.shape[1]
    # Distance metric = L2 (Euclidean)
    index = faiss.IndexFlatL2(dimension)

    # add vectors
    index.add(embeddings)

    # store 
    faiss.write_index(index, "../embeddings/vector_store/faiss.index")

    with open("../embeddings/vector_store/documents.json", "w") as f:
        json.dump(documents, f, indent=2)

docs = load_processed_docs("../data/processed")
embeddings = creat_embedding(docs)
save_to_faiss(embeddings, docs)





