import math
import argparse
import csv
from collections import Counter, defaultdict, deque
import itertools
import copy
import imaplib

parser = argparse.ArgumentParser()
parser.add_argument("train", metavar="train_path", nargs=1)
parser.add_argument("test", metavar="test_path", nargs=1)
parser.add_argument("d", metavar="tree_depth", nargs="*")


class Node:
    def __init__(self, attr=None, subtrees=None, value=None, data=None):
        self.__attr = attr
        self.__subtrees = subtrees
        self.__value = value
        self.__data = data

    @property
    def subtrees(self):
        return self.__subtrees

    @property
    def attr(self):
        return self.__attr

    @property
    def value(self):
        return self.__value

    @property
    def data(self):
        return self.__data

    def is_leaf(self):
        return self.__value != None


class ID3:
    def __init__(self, max_depth=None):
        self.__model = None
        self.__max_depth = max_depth

    def fit(self, train_set):
        if len(train_set) == 0:
            exit("Train set is empty.")
        attrs = list(train_set[0].keys())
        D = train_set
        D_parent = train_set
        X = sorted(attrs[:-1])
        y = attrs[-1]
        self.__model = self.id3(D=D, D_parent=D_parent, X=X, y=y)
        return self.__model

    def predict(self, test_set):
        goal = list(test_set[0].keys())[-1]
        print("[PREDICTIONS]:", end=" ")
        node = self.__model
        correct = 0
        exp_values = []
        pred_values = []

        for inst in test_set:
            expected = inst[goal]
            exp_values.append(expected)
            predicted = self.predict_inst(node, inst)
            pred_values.append(predicted)
            if predicted == expected:
                correct += 1
            print(predicted, end=" ")

        print(f"\n[ACCURACY]: {accuracy(correct, len(test_set)):0.5f}")
        print(f"[CONFUSION_MATRIX]:")
        matrix = conf_matrix(exp_values, pred_values)
        [print(" ".join(map(str, row))) for row in matrix]

    def predict_inst(self, node: Node, instance):
        if node.is_leaf():
            return node.value
        val = instance[node.attr]
        found = 0
        attr_values = list(node.subtrees.keys())
        if val in attr_values:
            return self.predict_inst(node.subtrees[val], instance)
        else:
            return argmax(node.data)

    def id3(self, D, D_parent, X, y, depth=0):
        if not D:
            v = argmax(D_parent)
            return Node(value=v)

        v = argmax(D)
        D_yv = [inst for inst in D if inst[y] == v]

        if not X or D == D_yv or depth == self.__max_depth:
            return Node(value=v)

        ent = entropy([inst[y] for inst in D])
        max_ig, max_x = 0, X[0]
        igs = []
        for x in X:
            ig = IG(D, x, ent, y)
            print(f"IG({x})={ig:.4f}", end=" ")
            if ig > max_ig:
                max_ig = ig
                max_x = x
        print()

        subtrees = {}
        x_vals = set([inst[max_x] for inst in D])
        for x_val in x_vals:
            D_xv = [inst for inst in D if inst[max_x] == x_val]
            new_X = copy.deepcopy(X)
            new_X.remove(max_x)
            t = self.id3(D_xv, D, new_X, y, depth=depth + 1)
            subtrees.update({x_val: t})

        return Node(attr=max_x, subtrees=subtrees, data=D)


def IG(data, x, ent, y):
    vals = {}
    for row in data:
        key = row[x]
        if key not in list(vals.keys()):
            vals[key] = [row[y]]
        else:
            vals[key].extend([row[y]])

    sum = 0
    for key, value in vals.items():
        sum += entropy(value) * len(value) / len(data)
    return ent - sum


def entropy(values):
    length = len(values)
    if length <= 1:
        return 0

    count = Counter()
    for d in values:
        count[d] += 1
    probs = [float(c) / length for c in count.values()]

    sum = 0
    for p in probs:
        if p > 0.0:
            sum -= p * math.log2(p)
    return sum


def argmax(data):
    classes = []
    key = list(data[0].keys())[-1]
    for row in data:
        classes.append(row[key])
    return Counter(sorted(classes)).most_common(1)[0][0]


def accuracy(corrects, length):
    return corrects / length


def conf_matrix(expected, predicted):
    classes = sorted(set(expected))
    num = len(classes)
    m = [[0] * num for i in range(num)]
    map_label = {key: i for i, key in enumerate(classes)}
    for pred, exp in zip(predicted, expected):
        m[map_label[exp]][map_label[pred]] += 1
    return m


def parse(path):
    data = []
    with open(path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader)


def print_result(tree):
    print("[BRANCHES]:")
    print_paths(tree)


def print_paths(node, path=[], value=None, level=1):
    if value is not None:
        path.append(f"{value} ")
    if not node.is_leaf():
        path.append(f"{level}:{node.attr}=")
        level += 1
    else:
        path.append(f"{node.value}")
        print("".join(path))
        path.pop()
        return
    for value, tree in node.subtrees.items():
        print_paths(tree, path, value, level)
        path.pop()
    path.pop()


if __name__ == "__main__":
    args = parser.parse_args()
    train_set = parse(path=args.train[0])
    test_set = parse(args.test[0])

    depth = None
    if args.d:
        depth = int(args.d[0])

    model = ID3(max_depth=depth)
    tree = model.fit(train_set)
    print_result(tree)

    model.predict(test_set)
