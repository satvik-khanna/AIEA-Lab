from logic_lm_implementation import LOGIC_LM, Var, SymbolicReasoner

family_kb = {
    ('parent', 'homer', 'bart'): True,
    ('parent', 'homer', 'lisa'): True,
    ('parent', 'homer', 'maggie'): True,
    ('parent', 'marge', 'bart'): True,
    ('parent', 'marge', 'lisa'): True,
    ('parent', 'marge', 'maggie'): True,
    ('parent', 'abraham', 'homer'): True,
    ('parent', 'mona', 'homer'): True,
    ('parent', 'clancy', 'marge'): True,
    ('parent', 'jackie', 'marge'): True,
    ('parent', 'clancy', 'patty'): True,
    ('parent', 'jackie', 'patty'): True,
    ('parent', 'clancy', 'selma'): True,
    ('parent', 'jackie', 'selma'): True,
    ('male', 'homer'): True,
    ('male', 'bart'): True,
    ('male', 'abraham'): True,
    ('male', 'clancy'): True,
    ('female', 'marge'): True,
    ('female', 'lisa'): True,
    ('female', 'maggie'): True,
    ('female', 'mona'): True,
    ('female', 'jackie'): True,
    ('female', 'patty'): True,
    ('female', 'selma'): True,
}

def find_all_father(X, Y):
    results = []
    if isinstance(X, str) and isinstance(Y, str):
        if ('parent', X, Y) in family_kb and ('male', X) in family_kb:
            results.append({})
    elif not isinstance(X, str) and isinstance(Y, str):
        for key in family_kb:
            if key[0] == 'parent' and key[2] == Y and ('male', key[1]) in family_kb:
                results.append({X.name: key[1]})
    elif isinstance(X, str) and not isinstance(Y, str):
        if ('male', X) in family_kb:
            for key in family_kb:
                if key[0] == 'parent' and key[1] == X:
                    results.append({Y.name: key[2]})
    else:
        for key in family_kb:
            if key[0] == 'parent' and ('male', key[1]) in family_kb:
                results.append({X.name: key[1], Y.name: key[2]})
    return results

def find_all_mother(X, Y):
    results = []
    if isinstance(X, str) and isinstance(Y, str):
        if ('parent', X, Y) in family_kb and ('female', X) in family_kb:
            results.append({})
    elif not isinstance(X, str) and isinstance(Y, str):
        for key in family_kb:
            if key[0] == 'parent' and key[2] == Y and ('female', key[1]) in family_kb:
                results.append({X.name: key[1]})
    elif isinstance(X, str) and not isinstance(Y, str):
        if ('female', X) in family_kb:
            for key in family_kb:
                if key[0] == 'parent' and key[1] == X:
                    results.append({Y.name: key[2]})
    else:
        for key in family_kb:
            if key[0] == 'parent' and ('female', key[1]) in family_kb:
                results.append({X.name: key[1], Y.name: key[2]})
    return results

def find_all_child(X, Y):
    results = []
    if isinstance(X, str) and isinstance(Y, str):
        if ('parent', Y, X) in family_kb:
            results.append({})
    elif not isinstance(X, str) and isinstance(Y, str):
        for key in family_kb:
            if key[0] == 'parent' and key[1] == Y:
                results.append({X.name: key[2]})
    elif isinstance(X, str) and not isinstance(Y, str):
        for key in family_kb:
            if key[0] == 'parent' and key[2] == X:
                results.append({Y.name: key[1]})
    else:
        for key in family_kb:
            if key[0] == 'parent':
                results.append({X.name: key[2], Y.name: key[1]})
    return results

def find_all_grandparent(X, Z):
    results = []
    if isinstance(X, str) and isinstance(Z, str):
        for key1 in family_kb:
            if key1[0] == 'parent' and key1[1] == X:
                Y = key1[2]
                if ('parent', Y, Z) in family_kb:
                    results.append({})
    elif not isinstance(X, str) and isinstance(Z, str):
        for key2 in family_kb:
            if key2[0] == 'parent' and key2[2] == Z:
                Y = key2[1]
                for key1 in family_kb:
                    if key1[0] == 'parent' and key1[2] == Y:
                        results.append({X.name: key1[1]})
    elif isinstance(X, str) and not isinstance(Z, str):
        for key1 in family_kb:
            if key1[0] == 'parent' and key1[1] == X:
                Y = key1[2]
                for key2 in family_kb:
                    if key2[0] == 'parent' and key2[1] == Y:
                        results.append({Z.name: key2[2]})
    else:
        for key1 in family_kb:
            if key1[0] == 'parent':
                X_val = key1[1]
                Y = key1[2]
                for key2 in family_kb:
                    if key2[0] == 'parent' and key2[1] == Y:
                        results.append({X.name: X_val, Z.name: key2[2]})
    return results

def find_all_sibling(X, Y):
    results = []
    if isinstance(X, str) and isinstance(Y, str) and X != Y:
        for key1 in family_kb:
            if key1[0] == 'parent' and key1[2] == X:
                Z = key1[1]
                if ('parent', Z, Y) in family_kb:
                    results.append({})
                    break
    elif isinstance(X, str) and not isinstance(Y, str):
        siblings_set = set()
        for key1 in family_kb:
            if key1[0] == 'parent' and key1[2] == X:
                Z = key1[1]
                for key2 in family_kb:
                    if key2[0] == 'parent' and key2[1] == Z and key2[2] != X:
                        siblings_set.add(key2[2])
        for sibling in siblings_set:
            results.append({Y.name: sibling})
    elif not isinstance(X, str) and isinstance(Y, str):
        siblings_set = set()
        for key1 in family_kb:
            if key1[0] == 'parent' and key1[2] == Y:
                Z = key1[1]
                for key2 in family_kb:
                    if key2[0] == 'parent' and key2[1] == Z and key2[2] != Y:
                        siblings_set.add(key2[2])
        for sibling in siblings_set:
            results.append({X.name: sibling})
    else:
        sibling_pairs = set()
        for key1 in family_kb:
            if key1[0] == 'parent':
                parent = key1[1]
                child1 = key1[2]
                for key2 in family_kb:
                    if key2[0] == 'parent' and key2[1] == parent and key2[2] != child1:
                        if (child1, key2[2]) not in sibling_pairs and (key2[2], child1) not in sibling_pairs:
                            sibling_pairs.add((child1, key2[2]))
        for child1, child2 in sibling_pairs:
            results.append({X.name: child1, Y.name: child2})
            results.append({X.name: child2, Y.name: child1})
    return results

logic_lm = LOGIC_LM(family_kb)

logic_lm.query_handlers = {
    "father": find_all_father,
    "mother": find_all_mother,
    "child": find_all_child,
    "grandparent": find_all_grandparent,
    "sibling": find_all_sibling
}

logic_lm.symbolic_reasoner = SymbolicReasoner(family_kb, logic_lm.query_handlers)

questions = [
    "Who is the father of bart?",
    "Is marge the mother of lisa?",
    "Who are the children of homer?",
    "Are bart and lisa siblings?",
    "Who are the grandparents of bart?",
    "Is abraham a grandparent of lisa?",
    "Who is the mother of maggie?",
    "Are patty and selma siblings?",
    "Who are the children of marge?",
    "Is clancy a grandparent of bart?"
]

print("Testing LOGIC-LM with the Simpsons family knowledge base:")
print("-" * 70)

for question in questions:
    print(f"Question: {question}")
    answer = logic_lm.answer_question(question)
    print(f"Answer: {answer}")
    print("-" * 70)