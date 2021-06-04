import argparse
import heapq
from collections import deque


parser = argparse.ArgumentParser()
parser.add_argument('--alg', metavar='a', nargs=1, choices=['bfs', 'ucs', 'astar'],
                    help='state space search algorithm (values: bfs, ucs, or astar)')
parser.add_argument('--ss', metavar='ssd_path', required=True, nargs=1,
                    help='path to state space descriptor file')
parser.add_argument('--h', metavar='hd_path', nargs=1,
                    help='path to heuristic descriptor file')
parser.add_argument('--check-optimistic', action='store_true',
                    help='flag for checking if given heuristic is optimistic')
parser.add_argument('--check-consistent', action='store_true',
                    help='flag for checking if given heuristic is consistent')


def ucs(init_state, goal_states, transitions):
    init_state = (0.0, init_state, None)

    open_q = [init_state]
    closed = set()
    cheaper = dict()
    cheaper.update({init_state[1]: init_state[0]})

    while open_q:
        n = heapq.heappop(open_q)
        closed.add(n[1])

        if n[1] in goal_states:
            return n[0], len(closed), get_path(n)

        successors = transitions.get(n[1])
        for s in successors:
            s = (n[0] + float(s[1]), s[0], n)
            if s[1] in closed: continue
            if s[1] not in cheaper.keys() or s[0] < cheaper.get(s[1]):
                cheaper.update({s[1]: s[0]})
                heapq.heappush(open_q, s)
    failed()


def bfs(init_state, goal_states, transitions):
    init_state = (0.0, init_state, None)
    if init_state[1] in goal_states:
        return init_state[0], 1, get_path(init_state)

    open_q = deque()
    open_q.append(init_state)
    closed = set()

    while open_q:
        n = open_q.popleft()
        successors = transitions.get(n[1])
        for s in successors:
            s = (n[0] + s[1], s[0], n) 
            if s[1] in closed: continue
            closed.add(s[1])
            if s[1] in goal_states:
                return s[0], len(closed), get_path(s)
            open_q.append(s)
    failed()


def astar(init_state, goal_states, transitions, state_est_cost):
    open_q = [(state_est_cost.get(init_state), init_state, None, 0.0)]
    closed = set()
    cheaper = dict()
    cheaper.update({init_state: 0})

    while open_q:
        n = heapq.heappop(open_q)
        closed.add(n[1])

        if n[1] in goal_states:
            return n[3], len(closed), get_path(n)

        successors = transitions.get(n[1])
        for s in successors:
            s = (n[3] + float(s[1]) + state_est_cost.get(s[0]), s[0], n, n[3] + float(s[1]))
            if s[1] in closed: continue
            if s[1] not in cheaper.keys() or s[3] < cheaper.get(s[1]):
                cheaper.update({s[1]: s[3]})
                heapq.heappush(open_q, (max(n[0], s[0]), s[1], n, s[3]))
    failed()


def check_optimistic(goal_states, transitions, state_est_cost):
    res = ['OK', '']
    for st in state_est_cost.items():
        real_cost = ucs(st[0], goal_states, transitions)[0]
        if st[1] <= real_cost: res[0] = 'OK'
        else: res = ['ERR', 'not ']
        print(f'[CONDITION]: [{res[0]}] h({st[0]}) <= h*: {st[1]} <= {real_cost}')
    print(f'[CONCLUSION]: Heuristic is {res[1]}optimistic.')


def check_consistent(transitions, state_est_cost):
    res = ['OK', '']
    for st in state_est_cost.items():
        for child in transitions.get(st[0]):
            child_h = state_est_cost.get(child[0])
            if st[1] <= child_h + child[1]: res[0] = 'OK'
            else: res = ['ERR', 'not ']
            print(f'[CONDITION]: [{res[0]}] h({st[0]}) <= h({child[0]}) + c: {st[1]} <= {child_h} + {child[1]}')
    print(f'[CONCLUSION]: Heuristic is {res[1]}consistent.')


def parse_ss_file(file):
    data = [line.rstrip('\n') for line in file.readlines() if not line.startswith('#')]
    transitions = {}
    for t in data[2:]:
        t = t.split(':')
        children = [(i.split(',')[0], float(i.split(',')[1])) for i in t[1].strip().split()]
        children.sort(key=lambda x: x[0])
        transitions.update({t[0]: children})
    return data[0].strip(), set(data[1].strip().split()), transitions


def parse_hd_file(file):
    data = [line.rstrip('\n') for line in file.readlines() if not line.startswith('#')]
    state_est_cost = dict()
    for state in data:
        state = state.split(':')
        state_est_cost.update({state[0].strip(): float(state[1].strip())})
    return dict(sorted(state_est_cost.items()))


def get_path(node):
    return get_path_rec('', node)


def get_path_rec(path, node):
    if node[2] is not None:
        path += get_path_rec(path, node[2]) + ' => '
    return path + node[1]

def failed():
    print('[FOUND_SOLUTION]: no')
    exit(1)

def print_res(cost, closed, path):
    print('yes'),
    print('[STATES_VISITED]:', closed)
    print('[PATH_LENGTH]:', len(path.split('=>')))
    print('[TOTAL_COST]:', cost)
    print('[PATH]:', path)


def main():
    args = parser.parse_args()
    ssd_path = args.ss[0]

    try:
        with open(ssd_path, 'r', encoding='utf8') as file:
            init_state, goal_states, transitions = parse_ss_file(file)
    except OSError:
        print("State space descriptor file path does not exist.")
        exit(1)

    alg = ''
    if args.alg is not None:
        alg = args.alg[0]
    if alg == 'bfs':
        print('# BFS')
        goal, closed, path = bfs(init_state, goal_states, transitions)
    elif alg == 'ucs':
        print('# UCS')
        goal, closed, path = ucs(init_state, goal_states, transitions)
    elif alg == 'astar' or args.check_optimistic or args.check_consistent:
        if args.h is None:
            print("Path to heuristic description file not provided.")
            parser.print_usage()
            exit(1)
        try:
            hd_file_path = args.h[0]
            with open(hd_file_path, 'r', encoding='utf-8') as hd_file:
                state_est_cost = parse_hd_file(hd_file)
        except OSError:
            print("Heuristic description file path does not exist.")
            exit(1)

        if alg == 'astar':
            print('# A-STAR', hd_file_path)
            goal, closed, path = astar(init_state, goal_states, transitions, state_est_cost)
        elif args.check_optimistic:
            print('# HEURISTIC-OPTIMISTIC', hd_file_path)
            check_optimistic(goal_states, transitions, state_est_cost)
        else:
            print('# HEURISTIC-CONSISTENT', hd_file_path)
            check_consistent(transitions, state_est_cost)

    if alg != '':
        print('[FOUND_SOLUTION]: ', end='')
        print_res(goal, closed, path)


if __name__ == '__main__':
    main()
