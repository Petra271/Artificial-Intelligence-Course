import argparse
import copy
from literal import Literal
from clause import Clause
import time
import itertools

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest="command")

res_parser = subparsers.add_parser("resolution")
res_parser.add_argument("claus_path")

cook_parser = subparsers.add_parser("cooking")
cook_parser.add_argument("claus_path")
cook_parser.add_argument("us_cmd_path")


def resolution(goal, initial):

    clauses = copy.deepcopy(initial)
    resolved = set()
    sos = goal.negate()

    while True:
        remove_redundant(clauses, sos)
        remove_tautologies(clauses, sos)

        selected = select_clauses(clauses, sos, resolved)
        if selected is None:
            return False, goal, initial

        c1, c2 = selected
        if len(c1.get_literals()) == 1 and len(c2.get_literals()) == 1:
            return True, Clause(goal.get_literals(), (c1, c2)), initial
        res = resolve(c1, c2)
        resolved |= {(c1, c2), (c2, c1)}
        sos.add(res)


def remove_redundant(clauses, sos):
    [clauses.remove(c) for c in set(clauses) if c.isRedundant(clauses | sos)]
    [sos.remove(c) for c in set(sos) if c.isRedundant(clauses | sos)]


def remove_tautologies(clauses, sos):
    [clauses.remove(c) for c in set(clauses) if c.isResolvable(c)]
    [sos.remove(c) for c in set(sos) if c.isResolvable(c)]


def select_clauses(clauses, sos, res):
    pairs = set(itertools.product(sos, sos | clauses)) - res
    for c1, c2 in pairs:
        if c1 != c2 and c1.isResolvable(c2):
            return (c1, c2)


def resolve(c1, c2):
    new = set()
    c2_cp = copy.deepcopy(c2.get_literals())
    for l in c1.get_literals():
        neg_l = l.negate()
        if neg_l in c2.get_literals():
            c2_cp.remove(neg_l)
        else:
            new.add(l)
    return Clause(new | c2_cp, (c1, c2))


def parse_res_file(path):
    try:
        with open(path, "r", encoding="utf8") as file:
            data = [
                line.rstrip("\n")
                for line in file.readlines()
                if not line.startswith("#")
            ]
            clauses = []
            for l in data:
                literals = [
                    Literal(literal.replace("~", ""), literal.startswith("~"))
                    for literal in l.lower().split()
                    if literal != "v"
                ]
                clauses.append(Clause(literals, None))
            return data, clauses[-1], set(clauses[:-1])
    except OSError:
        print("State space descriptor file path does not exist.")
        exit(1)


def parse_cmd_file(path):
    with open(path, "r", encoding="utf8") as file:
        commands = [
            [line[:-2].lower().strip(), line.strip()[-1]] for line in file.readlines()
        ]
    return commands


def cooking(commands, data):
    print("Constructed with knowledge:")
    [print(line.lower().rstrip("\n")) for line in data]
    print()

    for clause, cmd in commands:
        print("User's command:", clause, cmd)

        if cmd == "?":
            literals = [
                Literal(literal.replace("~", ""), literal.startswith("~"))
                for literal in clause.lower().split()
                if literal != "v"
            ]
            goal, initial = parse_res_file(args.claus_path)[1:]
            initial.add(goal)
            found, goal, clauses = resolution(Clause(literals, None), initial)
            print_res(found, goal, clauses)

        elif cmd == "-":
            with open(args.claus_path, "r+") as file:
                cl_data = [line.lower().rstrip("\n") for line in file.readlines()]
                if clause in cl_data:
                    file.seek(0)
                    cl_data.remove(clause)
                    file.write("\n".join(cl_data) + "\n")
                    print("removed", clause)
                    file.truncate()
                else:
                    print(clause, "not present in database")

        elif cmd == "+":
            with open(args.claus_path, "a") as file:
                file.write(clause + "\n")
            print("added", clause)

        print()


def print_res(found, goal, clauses):
    if found:
        print_fun(goal, clauses)
    else:
        print_init(clauses, goal.negate(), None)
    print("[CONCLUSION]: ", end="")
    print(f"{goal} is true") if found else print(f"{goal} is unknown")


def print_fun(goal, clauses):
    used = [goal]
    parents = []
    used_initial = set()
    used_goal = set()
    parents.extend(goal.get_parents())
    negated_goal = goal.negate()
    for p in parents:
        if p.get_parents() is not None:
            used.append(p)
            parents.extend(p.get_parents())
        if p in clauses and p not in negated_goal:
            used_initial.add(p)
        if p in negated_goal:
            used_goal.add(p)

    clause_line = dict()
    index, clause_line = print_init(used_initial, used_goal, clause_line)

    used.reverse()
    for i, clause in enumerate(used, start=index):
        p1, p2 = clause.get_parents()
        if i == len(used) + index - 1:
            print(f"{i}. NIL ({clause_line.get(p1)}, {clause_line.get(p2)})")
            continue
        print(f"{i}. {clause} ({clause_line.get(p1)}, {clause_line.get(p2)})")
        clause_line.update({clause: i})
    print("===============")


def print_clauses(i, clauses, clause_line):
    for i, clause in enumerate(clauses, start=i):
        print(f"{i}. {clause}")
        if clause_line is not None:
            clause_line.update({clause: i})
    return i + 1, clause_line


def print_init(clauses, goal, clause_line):
    index, clause_line = print_clauses(1, sorted(clauses), clause_line)
    index, clause_line = print_clauses(index, goal, clause_line)
    print("===============")
    return index, clause_line


if __name__ == "__main__":
    args = parser.parse_args()
    data, goal, initial = parse_res_file(args.claus_path)
    if args.command == "resolution":
        found, goal, clauses = resolution(goal, initial)
        print_res(found, goal, clauses)
    elif args.command == "cooking":
        commands = parse_cmd_file(args.us_cmd_path)
        cooking(commands, data)
