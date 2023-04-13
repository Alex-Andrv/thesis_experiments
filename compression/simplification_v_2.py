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
    assert cnt_pb < 10, "see validate"
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
        pb_constraints = []
        for variables in variables_list:
            pb_constraint = []
            for v in variables:
                pb_constraint.append((round(model.getVal(v)), v.name))
            pb_constraints.append(pb_constraint)
        return True, pb_constraints
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


def simplification_v_2(clauses: list, diff=3, max_diff_var=8, compression_percentage=0.5, debug=False):
    clauses = clauses
    was_glue = [False] * len(clauses)
    len_clauses = len(clauses)

    glues = []
    result_glues = []

    for i in tqdm(range(len_clauses)):
        indexes = [i]
        if was_glue[i]:
            continue
        vars = set([abs(c) for c in clauses[i]])
        glue = [clauses[i]]
        j = i + 1
        while len(vars) < max_diff_var and j < len_clauses:
            if was_glue[j]:
                j += 1
                continue
            vj = set([abs(c) for c in clauses[j]])
            if len(vars - vj) <= diff:
                indexes.append(j)
                vars.update(vj)
                glue.append(clauses[j])
            j += 1
        cnt_pb = 1
        status, res = to_pb(glue, cnt_pb)
        if not status:
            while cnt_pb < (1 - compression_percentage) * len(glue):
                cnt_pb += 1
                status, res = to_pb(glue, cnt_pb)
                if status:
                    break


        if status:
            if debug:
                print(f"new glue {len(glue)}, to {cnt_pb} pb")
            for ind in indexes:
                was_glue[ind] = True
            indexes = []
            glues.append(glue)
            result_glues.append(res)
        else:
            if debug:
                print("cant simp")

    remainder = []

    for is_used, clause in zip(was_glue, clauses):
        if not is_used:
            remainder.append(clause)

    return glues, remainder, result_glues
