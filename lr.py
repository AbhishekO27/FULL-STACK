from collections import defaultdict, deque

class LR1Parser:
    def __init__(self, grammar, start_symbol):
        self.grammar = grammar
        self.start_symbol = start_symbol
        self.non_terminals = list(grammar.keys())
        self.terminals = self.get_terminals()
        self.first = defaultdict(set)
        self.states = []
        self.action = {}
        self.goto_table = {}

        self.compute_first()
        self.build_canonical_collection()
        self.build_parsing_table()

    # -----------------------------
    # Find Terminals
    # -----------------------------
    def get_terminals(self):
        terminals = set()
        for prods in self.grammar.values():
            for prod in prods:
                for symbol in prod:
                    if symbol not in self.grammar:
                        terminals.add(symbol)
        terminals.add("$")
        return list(terminals)

    # -----------------------------
    # FIRST Set
    # -----------------------------
    def compute_first(self):
        for t in self.terminals:
            self.first[t].add(t)

        changed = True
        while changed:
            changed = False
            for nt in self.non_terminals:
                for prod in self.grammar[nt]:
                    for symbol in prod:
                        before = len(self.first[nt])
                        self.first[nt] |= self.first[symbol]
                        after = len(self.first[nt])
                        if after > before:
                            changed = True
                        break

    # -----------------------------
    # FIRST of sequence
    # -----------------------------
    def first_of_string(self, symbols):
        result = set()
        for symbol in symbols:
            result |= self.first[symbol]
            break
        return result

    # -----------------------------
    # Closure
    # -----------------------------
    def closure(self, items):
        closure_set = set(items)
        while True:
            new_items = set()
            for (lhs, rhs, dot, lookahead) in closure_set:
                if dot < len(rhs):
                    B = rhs[dot]
                    if B in self.grammar:
                        beta = rhs[dot+1:]
                        beta_lookahead = list(beta) + [lookahead]
                        first_beta = self.first_of_string(beta_lookahead)

                        for prod in self.grammar[B]:
                            for b in first_beta:
                                new_items.add((B, tuple(prod), 0, b))

            if new_items.issubset(closure_set):
                break
            closure_set |= new_items

        return frozenset(closure_set)

    # -----------------------------
    # GOTO
    # -----------------------------
    def goto(self, items, symbol):
        moved = set()
        for (lhs, rhs, dot, lookahead) in items:
            if dot < len(rhs) and rhs[dot] == symbol:
                moved.add((lhs, rhs, dot+1, lookahead))
        return self.closure(moved)

    # -----------------------------
    # Canonical Collection
    # -----------------------------
    def build_canonical_collection(self):
        augmented_start = self.start_symbol + "'"
        self.grammar[augmented_start] = [[self.start_symbol]]

        start_item = (augmented_start, tuple([self.start_symbol]), 0, "$")
        start_state = self.closure([start_item])

        self.states.append(start_state)
        queue = deque([start_state])

        while queue:
            state = queue.popleft()
            for symbol in self.terminals + self.non_terminals:
                next_state = self.goto(state, symbol)
                if next_state and next_state not in self.states:
                    self.states.append(next_state)
                    queue.append(next_state)

    # -----------------------------
    # Parsing Table
    # -----------------------------
    def build_parsing_table(self):
        for i, state in enumerate(self.states):
            for (lhs, rhs, dot, lookahead) in state:

                if dot < len(rhs):
                    symbol = rhs[dot]
                    next_state = self.goto(state, symbol)
                    j = self.states.index(next_state)

                    if symbol in self.terminals:
                        self.action[(i, symbol)] = ("shift", j)
                    else:
                        self.goto_table[(i, symbol)] = j

                else:
                    if lhs == self.start_symbol + "'":
                        self.action[(i, "$")] = ("accept",)
                    else:
                        self.action[(i, lookahead)] = ("reduce", lhs, rhs)

    # -----------------------------
    # Parse Input
    # -----------------------------
    def parse(self, tokens):
        stack = [0]
        tokens.append("$")
        pointer = 0

        while True:
            state = stack[-1]
            token = tokens[pointer]

            if (state, token) not in self.action:
                print("❌ ERROR")
                return False

            action = self.action[(state, token)]

            if action[0] == "shift":
                stack.append(action[1])
                pointer += 1

            elif action[0] == "reduce":
                lhs, rhs = action[1], action[2]
                for _ in rhs:
                    stack.pop()
                state = stack[-1]
                stack.append(self.goto_table[(state, lhs)])

            elif action[0] == "accept":
                print("✅ ACCEPTED")
                return True


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":

    grammar = {
        "E": [["E", "+", "T"], ["T"]],
        "T": [["T", "*", "F"], ["F"]],
        "F": [["(", "E", ")"], ["id"]]
    }

    parser = LR1Parser(grammar, "E")

    user_input = input("Enter input string (tokens separated by space): ")
    tokens = user_input.strip().split()
    parser.parse(tokens)
