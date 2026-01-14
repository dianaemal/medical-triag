class TriagState:
    def __init__(self):
        self.history = []          # [(question, answer)]
        self.num_questions = 0
        self.max_questions = 3
      

        # red flag / urgent keywords
        self.red_flags = [
            "chest pain", "shortness of breath", "difficulty breathing",
            "loss of consciousness", "suicidal", "self harm",
            "severe bleeding", "uncontrolled pain"
        ]

    def add_turn(self, question, answer):
        self.history.append((question, answer))
        self.num_questions += 1
       

    def should_continue(self):
        return self.num_questions < self.max_questions 

    def build_memory(self):
        if not self.history:
            return "None"
        return "\n".join(
            f"Q: {q}\nA: {a}" for q, a in self.history
        )
    
    def build_summary(self):
        return " ".join([a for q, a in self.history])
