import numpy as np

def cosine_similarity(a, b):
 
    a = np.asarray(a).flatten()
    b = np.asarray(b).flatten()
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))



class SafetyDetector:
    def __init__(self, embed_fn, threshold=0.85):
        self.embed_fn = embed_fn
        self.threshold = threshold

        # High-level emergency concepts (NOT user phrases)
        self.emergency_concepts = {
            "call_911": [
                "severe chest pain and shortness of breath",
                "heart attack symptoms",
                "cannot breathe",
                "sudden loss of consciousness",
                "suicidal thoughts or intent",
                "paralysis or sudden numbness",
                "severe uncontrolled bleeding"
            ]
        }

        # Precompute embeddings ONCE
        self.emergency_vectors = {
            level: [self.embed_fn(text) for text in texts]
            for level, texts in self.emergency_concepts.items()
        }

    def check(self, text: str):
        vec = self.embed_fn(text)

        for level, vectors in self.emergency_vectors.items():
            for ref_vec in vectors:
                if cosine_similarity(vec, ref_vec) >= self.threshold:
                    return level

        return None
