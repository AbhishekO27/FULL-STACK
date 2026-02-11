from collections import defaultdict

class LR1Parser:
    def __init__(self):
       
        self.grammar = {
            "E'": [["E"]],
            "E": [["E", "+", "T"], ["T"]],
            "T": [["T", "*", "F"], ["F"]],
            "F": [["(", "E", ")"], ["id"]]
        }
        self.action = {
            (0, "id"): ("shift", 5),
            (0, "("): ("shift", 4),

            (1, "+"): ("shift", 6),
            (1, "$"): ("accept",),

            (2, "+"): ("reduce", "E", ["T"]),
            (2, "*"): ("shift", 7),
            (2, ")"): ("reduce", "E", ["T"]),
            (2, "$"): ("reduce", "E", ["T"]),

            (3, "+"): ("reduce", "T", ["F"]),
            (3, "*"): ("reduce", "T", ["F"]),
            (3, ")"): ("reduce", "T", ["F"]),
            (3, "$"): ("reduce", "T", ["F"]),

            (4, "id"): ("shift", 5),
            (4, "("): ("shift", 4),

            (5, "+"): ("reduce", "F", ["id"]),
            (5, "*"): ("reduce", "F", ["id"]),
            (5, ")"): ("reduce", "F", ["id"]),
            (5, "$"): ("reduce", "F", ["id"]),

            (6, "id"): ("shift", 5),
            (6, "("): ("shift", 4),

            (7, "id"): ("shift", 5),
            (7, "("): ("shift", 4),

            (8, "+"): ("shift", 6),
            (8, ")"): ("shift", 11),

            (9, "+"): ("reduce", "E", ["E", "+", "T"]),
            (9, "*"): ("shift", 7),
            (9, ")"): ("reduce", "E", ["E", "+", "T"]),
            (9, "$"): ("reduce", "E", ["E", "+", "T"]),

            (10, "+"): ("reduce", "T", ["T", "*", "F"]),
            (10, "*"): ("reduce", "T", ["T", "*", "F"]),
            (10, ")"): ("reduce", "T", ["T", "*", "F"]),
            (10, "$"): ("reduce", "T", ["T", "*", "F"]),

            (11, "+"): ("reduce", "F", ["(", "E", ")"]),
            (11, "*"): ("reduce", "F", ["(", "E", ")"]),
            (11, ")"): ("reduce", "F", ["(", "E", ")"]),
            (11, "$"): ("reduce", "F", ["(", "E", ")"]),
        }

        self.goto = {
            (0, "E"): 1,
            (0, "T"): 2,
            (0, "F"): 3,

            (4, "E"): 8,
            (4, "T"): 2,
            (4, "F"): 3,

            (6, "T"): 9,
            (6, "F"): 3,

            (7, "F"): 10,
        }

    def parse(self, tokens):
        stack = [0]
        tokens.append("$")
        pointer = 0

        while True:
            state = stack[-1]
            current_token = tokens[pointer]

            if (state, current_token) not in self.action:
                print("❌ ERROR")
                return

            action = self.action[(state, current_token)]

            if action[0] == "shift":
                stack.append(action[1])
                pointer += 1

            elif action[0] == "reduce":
                lhs = action[1]
                rhs = action[2]

                for _ in rhs:
                    stack.pop()

                state = stack[-1]
                stack.append(self.goto[(state, lhs)])

            elif action[0] == "accept":
                print("✅ ACCEPTED")
                return


if __name__ == "__main__":
    parser = LR1Parser()
    user_input = input("Enter input string (tokens separated by space): ")
    tokens = user_input.strip().split()
    parser.parse(tokens)
