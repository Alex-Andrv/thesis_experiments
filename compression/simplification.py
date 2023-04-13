import itertools
import random
from math import factorial

from pyscipopt import Model
from tqdm import tqdm

lb = -1000
ub = 1000


def check_assumptions(glue, assumptions):
    res = True
    for gl in glue:
        ans = False
        for var in gl:
            ans |= bool(assumptions[var])
        res &= ans
    return res


def to_pb(glue, cnt_pb=1):
    vars: list = list(map(lambda x: abs(x), itertools.chain(*glue)))
    vars = list(set(vars))

    if len(vars) > 14:
        return False, None

    model = Model()

    model.setParam('display/verblevel', 0)

    variables_list = []

    for i in range(cnt_pb):
        variables = []

        for var in vars:
            variables.append(model.addVar(vtype="I", name=f"{var}_{i}", lb=lb, ub=ub))

        variables.append(model.addVar(vtype="I", name=f"b_{i}", lb=lb, ub=ub))

        variables_list.append(variables)

    for comb in range(1 << len(vars)):
        assumptions = dict()
        comb_tmp = comb
        for i in range(len(vars)):
            assumptions[vars[i]] = comb_tmp % 2
            assumptions[-vars[i]] = (comb_tmp + 1) % 2
            comb_tmp //= 2
        sum_lines = []
        for i in range(cnt_pb):
            sum_line = -variables_list[i][len(variables_list[i]) - 1]
            sum_lines.append(sum_line)

        for i in range(len(vars)):
            for j in range(cnt_pb):
                sum_lines[j] += variables_list[j][i] * assumptions[vars[i]]
        if check_assumptions(glue, assumptions):
            for i in range(cnt_pb):
                model.addCons(sum_lines[i] >= 0)
        else:
            z_i = []
            for i in range(cnt_pb):
                z_i.append(model.addVar(vtype="I", lb=0, ub=1))
            MAX_SUM = (len(vars) + 1) * ub
            for i in range(cnt_pb):
                model.addCons(sum_lines[i] - (1 - z_i[i]) * MAX_SUM <= -1)
            sum = 0
            for z in z_i:
                sum += z
            model.addCons(sum >= 1)

    model.optimize()

    if model.getStatus() == "optimal":
        res = []
        for variables in variables_list:
            for v in variables:
                res.append((model.getVal(v), v.name))

        return True, res
    else:
        return False, None


def c_n_k(n, k):
    return int(factorial(n) / factorial(k) / factorial(n - k))


def random_subset(glue, count_random=60):
    subsets = []
    for i in range(len(glue) + 1):
        subsets.extend(list(itertools.combinations(glue, i)))
    stat_pos = len(glue) + c_n_k(len(glue), 2) + 1
    end_pos = stat_pos + c_n_k(len(glue), 3) + c_n_k(len(glue), 4) + 1
    while count_random > 0:
        subset_num = random.randint(stat_pos, end_pos)
        stat, new_res = to_pb(subsets[subset_num])
        if stat:
            return stat, new_res, subsets[subset_num]
        count_random -= 1
    return False, None, None


def simplification(clauses: list, window=2, cnt_mistakes=4):
    glues = []
    result_glues = []
    i = 0
    pbar = tqdm(total=len(clauses))
    while i + window < len(clauses):
        tmp_window = window

        res = None

        cnt_mistakes_tmp = cnt_mistakes

        right_glue = None
        i_tmp = i
        while True:
            glue = clauses[i_tmp: i_tmp + tmp_window]
            stat, new_res = to_pb(glue)
            if not stat:
                if cnt_mistakes_tmp > 0 and i_tmp + tmp_window < len(clauses):
                    cnt_mistakes_tmp -= 1
                    tmp_window += 1
                else:
                    if cnt_mistakes_tmp == 0:
                        stat, new_res, subset = random_subset(glue)
                        if stat and cnt_mistakes_tmp == 0:
                            # print("HUE")
                            right_glue = subset
                            res = new_res
                            tmp_window += 1
                            i_tmp += (tmp_window - 1)
                            break
                        else:
                            i_tmp += (tmp_window - 1)
                            break
                    else:
                        i_tmp += (tmp_window - 1)
                        break
            else:
                right_glue = glue
                res = new_res
                tmp_window += 1

        assert i < i_tmp
        pbar.update(i_tmp - i)
        i = i_tmp


        if res:
            # print(f"new glue {len(right_glue)}")
            vars_set = list(map(lambda x: x, itertools.chain(*right_glue)))
            # print(res)
            # print(right_glue)
            # for v1 in vars_set:
            #     for v2 in vars_set:
            #         if v1 == v2 * -1:
            #             print(res)
            #             print(right_glue)
            # if len(right_glue) >= 4:
            #     print(right_glue)
            glues.append(right_glue)
            result_glues.append([res])

    remainder = []

    for clause in clauses:
        skip = False
        for glue in itertools.chain(*glues):
            if clause == glue:
                skip = True
        if not skip:
            remainder.append(clause)

    return glues, remainder, result_glues
