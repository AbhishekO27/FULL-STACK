from collections import defaultdict, deque


# ─── Grammar utilities ────────────────────────────────────────────────────────

def get_terminals(grammar):
    terminals = set()
    for prods in grammar.values():
        for prod in prods:
            for symbol in prod:
                if symbol not in grammar:
                    terminals.add(symbol)
    terminals.add("$")
    return list(terminals)


def compute_first(grammar, terminals):
    first = defaultdict(set)
    for t in terminals:
        first[t].add(t)
    changed = True
    while changed:
        changed = False
        for nt in grammar:
            for prod in grammar[nt]:
                for symbol in prod:
                    before = len(first[nt])
                    first[nt] |= first[symbol]
                    if len(first[nt]) > before:
                        changed = True
                    break
    return first


def first_of_string(symbols, first):
    result = set()
    for symbol in symbols:
        result |= first[symbol]
        break
    return result


# ─── LR(1) item sets ─────────────────────────────────────────────────────────

def closure(items, grammar, first):
    closure_set = set(items)
    while True:
        new_items = set()
        for (lhs, rhs, dot, lookahead) in closure_set:
            if dot < len(rhs):
                B = rhs[dot]
                if B in grammar:
                    beta = rhs[dot + 1:]
                    beta_lookahead = list(beta) + [lookahead]
                    first_beta = first_of_string(beta_lookahead, first)
                    for prod in grammar[B]:
                        for b in first_beta:
                            new_items.add((B, tuple(prod), 0, b))
        if new_items.issubset(closure_set):
            break
        closure_set |= new_items
    return frozenset(closure_set)


def goto(items, symbol, grammar, first):
    moved = set()
    for (lhs, rhs, dot, lookahead) in items:
        if dot < len(rhs) and rhs[dot] == symbol:
            moved.add((lhs, rhs, dot + 1, lookahead))
    return closure(moved, grammar, first)


def build_canonical_collection(grammar, start_symbol, terminals, non_terminals, first):
    augmented_start = start_symbol + "'"
    grammar[augmented_start] = [[start_symbol]]
    non_terminals = [augmented_start] + non_terminals

    start_item = (augmented_start, tuple([start_symbol]), 0, "$")
    start_state = closure([start_item], grammar, first)

    states = [start_state]
    queue = deque([start_state])

    while queue:
        state = queue.popleft()
        for symbol in terminals + non_terminals:
            next_state = goto(state, symbol, grammar, first)
            if next_state and next_state not in states:
                states.append(next_state)
                queue.append(next_state)

    return states, augmented_start


# ─── Parsing table ───────────────────────────────────────────────────────────

def build_parsing_table(states, grammar, terminals, non_terminals, start_symbol, augmented_start):
    action = {}
    goto_table = {}
    conflicts = []

    for i, state in enumerate(states):
        for (lhs, rhs, dot, lookahead) in state:
            if dot < len(rhs):
                symbol = rhs[dot]
                next_state = None
                for j, s in enumerate(states):
                    from collections import defaultdict, deque
                    # recompute goto inline (states already built)
                    pass
                # find next state index
                for j, s in enumerate(states):
                    moved = frozenset(
                        (l2, r2, d2 + 1, la2)
                        for (l2, r2, d2, la2) in state
                        if d2 < len(r2) and r2[d2] == symbol
                    )
                    # check closure match — skip, use pre-built states
                    break

                # find j by matching
                moved_items = set()
                for (l2, r2, d2, la2) in state:
                    if d2 < len(r2) and r2[d2] == symbol:
                        moved_items.add((l2, r2, d2 + 1, la2))

                # find which state the closure of moved_items matches
                j = None
                for idx, s in enumerate(states):
                    if moved_items and all(item in s for item in moved_items):
                        j = idx
                        break

                if j is None:
                    continue

                if symbol in terminals:
                    entry = ("shift", j)
                    if (i, symbol) in action and action[(i, symbol)] != entry:
                        conflicts.append((i, symbol, action[(i, symbol)], entry))
                    action[(i, symbol)] = entry
                elif symbol in grammar:
                    goto_table[(i, symbol)] = j

            else:
                if lhs == augmented_start:
                    action[(i, "$")] = ("accept",)
                else:
                    entry = ("reduce", lhs, rhs)
                    if (i, lookahead) in action and action[(i, lookahead)] != entry:
                        conflicts.append((i, lookahead, action[(i, lookahead)], entry))
                    action[(i, lookahead)] = entry

    return action, goto_table, conflicts


# ─── Parser driver ───────────────────────────────────────────────────────────

def parse(tokens, action, goto_table):
    stack = [0]
    tokens = list(tokens) + ["$"]
    pointer = 0
    steps = []

    while True:
        state = stack[-1]
        token = tokens[pointer]
        step = {
            "stack": list(stack),
            "input": tokens[pointer:],
            "action": None,
            "status": "running"
        }

        if (state, token) not in action:
            step["action"] = f"ERROR: no action for state {state}, token '{token}'"
            step["status"] = "error"
            steps.append(step)
            return False, steps

        act = action[(state, token)]

        if act[0] == "shift":
            step["action"] = f"Shift {act[1]}"
            steps.append(step)
            stack.append(act[1])
            pointer += 1

        elif act[0] == "reduce":
            lhs, rhs = act[1], act[2]
            step["action"] = f"Reduce {lhs} → {' '.join(rhs) if rhs else 'ε'}"
            steps.append(step)
            for _ in rhs:
                stack.pop()
            top = stack[-1]
            stack.append(goto_table[(top, lhs)])

        elif act[0] == "accept":
            step["action"] = "Accept"
            step["status"] = "accept"
            steps.append(step)
            return True, steps


# ─── Public API ──────────────────────────────────────────────────────────────

class LR1Parser:
    def __init__(self, grammar, start_symbol):
        self.grammar = {k: [list(p) for p in v] for k, v in grammar.items()}
        self.start_symbol = start_symbol
        self.non_terminals = list(grammar.keys())
        self.terminals = get_terminals(self.grammar)
        self.first = compute_first(self.grammar, self.terminals)
        self.states, self.augmented_start = build_canonical_collection(
            self.grammar, start_symbol, self.terminals, self.non_terminals, self.first
        )
        self.action, self.goto_table, self.conflicts = build_parsing_table(
            self.states, self.grammar, self.terminals, self.non_terminals,
            start_symbol, self.augmented_start
        )

    def parse(self, tokens):
        return parse(tokens, self.action, self.goto_table)

    def get_table_summary(self):
        return {
            "states": len(self.states),
            "action_entries": len(self.action),
            "goto_entries": len(self.goto_table),
            "conflicts": self.conflicts,
        }