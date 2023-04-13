import itertools
import random
from math import factorial

from pyscipopt.scip import Model
from tqdm import tqdm

out = open("out.txt", "w")

vars = [3, 2, 1]

n = len(vars)

cnt_zero = 0

stats = []

cnt_row = 1 << len(vars)

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

def table(param):
    for x1 in range(2):
        for x2 in range(2):
            for x3 in range(2):
                    print(x1, x2, x3, param[x1 * 4 + x2 * 2 + x3])


for k in tqdm(range(0, cnt_row + 1)):
    cnt_ok = 0
    cnt_probs = c_n_k(1 << len(vars), k)
    for i, zero in enumerate(combinations(list(range(1 << len(vars))), k)):

        model = Model(f"{i}")

        shuffle = [1] * (1 << len(vars))

        for zero_i in zero:
            shuffle[zero_i] = 0

        model.setParam('display/verblevel', 0)

        # # create a SCIP model and add some constraints
        # x = model.addVar(vtype="I", name="1", lb=-1000)
        # y = model.addVar(vtype="I", name="2", lb=-1000)
        # c1 = model.addCons(x + y <= 1)
        # c2 = model.addCons(x - y >= 0)
        #
        # # optimize the model
        # model.optimize()
        #
        # # retrieve the solution
        # if model.getStatus() == "optimal":
        #     print("Optimal solution found")
        #     print("x =", model.getVal(x))
        #     print("y =", model.getVal(y))
        # else:
        #     print("No solution found")

        variables = []
        for var in vars:
            variables.append(model.addVar(vtype="I", name=f"{var}", lb=-1000, ub=1000))

        variables.append(model.addVar(vtype="I", name=f"b", lb=-1000, ub=1000))


        for comb in range(1 << len(vars)):
            assumptions = dict()
            comb_tmp = comb
            for i in range(len(vars)):
                assumptions[vars[i]] = comb_tmp % 2
                assumptions[-vars[i]] = (comb_tmp + 1) % 2
                comb_tmp //= 2
            sum_line = -variables[len(variables) - 1]
            for i in range(len(vars)):
                sum_line += variables[i] * assumptions[vars[i]]
            if shuffle[comb] == 1:
                assert type(assumptions[vars[1]]) == int
                model.addCons(sum_line >= 0)
            else:
                model.addCons(sum_line <= -1)

        model.optimize()

        if model.getStatus() == "optimal":
            vals = model.getVars()
            print(str(shuffle) + "\n")
            x3 = model.getVal(variables[0])
            x2 = model.getVal(variables[1])
            x1 = model.getVal(variables[2])
            # x4 = model.getVal(variables[3])
            b = model.getVal(variables[3])
            print(f"x1 = {x1}")
            print(f"x2 = {x2}")
            print(f"x3 = {x3}")
            # print(f"x4 = {x4}")
            print(f"b = {b}")
            table(shuffle)
            print("---------" + "\n")
            cnt_ok += 1
    # print(k, cnt_prob, cnt_ok, str(cnt_ok / (cnt_prob + 1) * 100) + "%")

    stats.append((cnt_probs, cnt_ok, str(cnt_ok / (cnt_probs) * 100) + "%"))

for s in stats:
    print(s[2], end=' ')