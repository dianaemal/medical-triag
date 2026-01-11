class TriagState:
    def __init__(self):
        self.history = []          # [(question, answer)]
        self.num_questions = 0
        self.max_questions = 2
        self.finished = False

    def add_turn(self, question, answer):
        self.history.append((question, answer))
        self.num_questions += 1
       

    def should_continue(self):
        return self.num_questions < self.max_questions and not self.finished

    def build_memory(self):
        if not self.history:
            return "None"
        return "\n".join(
            f"Q: {q}\nA: {a}" for q, a in self.history
        )
