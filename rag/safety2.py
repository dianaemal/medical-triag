
def vector(dict, fun):
    vec = {}
    for level, risk in dict.items():
        vec[level] = fun(risk)
    return vec


class Safety:
    def __init__(self, embd_fn, threshhold):
        self.threshhold = threshhold
        self.embd_fn = embd_fn

        self.risks = {
            "call_911":
            ["heart attack",
             "suicide"
             
             ]
        }

        self.vectors = vector(self.risks, embd_fn)

    def similary(self, user_text):

        user_vector = self.embd_fn(user_text)

        for i, j in self.vectors.items():
            for k in j:
                sim = cos(user_vector, k)
                if sim >= self.threshhold:
                    return i
                    
        return None






        
