import itertools
from math import factorial
from sys import argv

from tqdm import tqdm

from compression.simplification import to_pb
from heuristic_logic_minimizer.espresso_minimizer import mini
from util.DIMACS_writer import print_clause
from util.OPB_writer import print_pb_to_opb


n = int(argv[1])

def combinations(arr, k):
    if k == 0:
        yield []
        return
    if not arr:
        return
    for i in range(len(arr)):
        elem = arr[i]
        rest = arr[i+1:]
        for c in combinations(rest, k-1):
            yield [elem] + c

def c_n_k(n, k):
    return int(factorial(n) / factorial(k) / factorial(n - k))

stats = []

cnt_row = 1 << n


def truth_table_to_clauses(cnt_var, profile):
    clauses = []
    for comb, value in zip(range(1 << cnt_var), profile):
        if value == 1:
            continue
        clause = []
        comb_tmp = comb
        for i in range(n, 0, -1):
            if comb_tmp % 2 == 0:
                clause.append(i)
            else:
                clause.append(-i)
            comb_tmp //= 2
        clause.reverse()
        clauses.append(clause)
    return clauses


def print_truth_table(cnt_var, profile):
    for comb, value in zip(range(1 << cnt_var), profile):
        comb_tmp = comb
        line = []
        for i in range(1, n + 1):
            line.append(comb_tmp % 2)
            comb_tmp //= 2
        line.reverse()
        line.append("|")
        line.append(value)
        line = map(str, line)
        print("".join(line))


def check_resolutions(mini_clauses):
    if len(mini_clauses) > 2:
        for v1 in mini_clauses:
            for v2 in mini_clauses:
                v1_set = set(v1)
                v2_set = set(v2)
                dif_v1 = v1_set - v2_set
                dif_v2 = v2_set - v1_set
                dif_v1 = set(map(lambda x: abs(x), dif_v1))
                dif_v2 = set(map(lambda x: abs(x), dif_v2))
                if len(dif_v2.intersection(dif_v1)) == 1:
                    print("gg")


for k in tqdm(range(0, cnt_row + 1)):
    cnt_ok = 0
    cnt_probs = c_n_k(1 << n, k)
    for i, zero in enumerate(combinations(list(range(1 << n)), k)):

        shuffle = [1] * (1 << n)
        for zero_i in zero:
            shuffle[zero_i] = 0

        clauses = truth_table_to_clauses(n, shuffle)

        status, pb = to_pb(clauses, cnt_pb=1)

        if status:
            # print("profile: " + str(shuffle) + "\n")
            # print_pb_to_opb(pb)
            # print("truth table:")
            # print_truth_table(n, shuffle)
            # print("perfect truth table: ")
            # for cnf in clauses:
            #     print_clause(cnf)
            # print("min cnf:")
            mini_clauses = mini(clauses)
            # for cnf in mini_clauses:
            #     print_clause(cnf)
            check_resolutions(mini_clauses)
            # print("---------" + "\n")
            cnt_ok += 1
        else:
            mini_clauses = mini(clauses)
            # for cnf in mini_clauses:
            #     print_clause(cnf)
            check_resolutions(mini_clauses)


    stats.append((cnt_probs, cnt_ok, str(cnt_ok / (cnt_probs) * 100) + "%"))

for s in stats:
    print(s[2], end=' ')
