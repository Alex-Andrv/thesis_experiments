import itertools
import random
from math import factorial

from pyscipopt import Model
from tqdm import tqdm

from util.validate import validate_ans

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


def to_pb(glue, cnt_pb, max_sum=None):
    assert cnt_pb < 30, "see validate"
    vars: list = list(map(lambda x: abs(x), itertools.chain(*glue)))
    vars = list(set(vars))

    if not max_sum:
        max_sum = (len(vars) + 1) * ub

    if len(vars) > 16:
        return False, None

    model = Model()

    model.setParam('display/verblevel', 0)

    variables_list = []

    for i in range(cnt_pb):
        variables = dict()

        for var in vars:
            variables[var] = model.addVar(vtype="I", name=f"{var}", lb=lb, ub=ub)

        variables['b'] = (model.addVar(vtype="I", name=f"b", lb=lb, ub=ub))

        variables_list.append(variables)

    for comb in range(1 << len(vars)):
        assumptions = dict()
        comb_tmp = comb
        for var in vars:
            assumptions[var] = comb_tmp % 2
            assumptions[-var] = (comb_tmp + 1) % 2
            comb_tmp //= 2
        sum_lines = []
        for i in range(cnt_pb):
            sum_line = -variables_list[i]['b']
            sum_lines.append(sum_line)

        for var in vars:
            for j in range(cnt_pb):
                sum_lines[j] += variables_list[j][var] * assumptions[var]
        if check_assumptions(glue, assumptions):
            for i in range(cnt_pb):
                model.addCons(sum_lines[i] >= 0)
        # else:
        #     z_i = []
        #     for i in range(cnt_pb):
        #         z_i.append(model.addVar(vtype="I", lb=0, ub=1))
        #     for i in range(cnt_pb):
        #         model.addCons(sum_lines[i] - (1 - z_i[i]) * max_sum <= -1)
        #     sum = 0
        #     for z in z_i:
        #         sum += z
        #     model.addCons(sum >= 1)

    for cnf in glue:
        sum_lines = []
        negative_var = list(map(lambda v: abs(v), filter(lambda c: c < 0, cnf)))
        free_var = set(vars) - set(map(lambda c: abs(c), cnf))
        for i in range(cnt_pb):
            sum_line = -variables_list[i]['b'] # -b
            for var in negative_var:
                sum_line += variables_list[i][var] # sum coeff
            fi = dict()
            for var in free_var:
                fi[var] = model.addVar(vtype="I", lb=0, ub=1)
                model.addCons(variables_list[i][var] * fi[var] >= 0)
                model.addCons(variables_list[i][var] * (1 - fi[var]) <= 0)
                sum_line += fi[var] * variables_list[i][var]
            sum_lines.append(sum_line)

        z_i = []
        for i in range(cnt_pb):
            z_i.append(model.addVar(vtype="I", lb=0, ub=1))
        for i in range(cnt_pb):
            model.addCons(sum_lines[i] - (1 - z_i[i]) * max_sum <= -1)
        sum = 0
        for z in z_i:
            sum += z
        model.addCons(sum >= 1)

    model.optimize()

    if model.getStatus() == "optimal":
        pb_constraints = []
        for variables in variables_list:
            pb_constraint = []
            for v in variables.values():
                pb_constraint.append((round(model.getVal(v)), v.name))
            pb_constraints.append(pb_constraint)
        return True, pb_constraints
    else:
        return False, None


def c_n_k(n, k):
    return int(factorial(n) / factorial(k) / factorial(n - k))


def minimize_max_sum(glue, cnt_pb):
    vars: list = list(map(lambda x: abs(x), itertools.chain(*glue)))
    l = 0
    r = (len(vars) + 1) * ub
    status = False
    res = None
    while l + 1 < r:
        mid = (l + r) // 2
        status, res = to_pb(glue, cnt_pb, mid)
        if not status:
            l = mid
        else:
            r = mid
    # print(r)
    status, res = to_pb(glue, cnt_pb, r)
    return status, res


def simplification_v_4(clauses: list, diff=2, max_diff_var=5, compression_percentage=0.6, restart=3, debug=False):
    clauses = clauses
    was_glue = [False] * len(clauses)
    len_clauses = len(clauses)

    glues = []
    result_glues = []

    for _ in range(restart):
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
                if len(vj - vars) <= diff: # можно вычитать наоборот
                    indexes.append(j)
                    vars.update(vj)
                    glue.append(clauses[j])
                j += 1
            cnt_pb = 1
            status, res = to_pb(glue, cnt_pb, max_sum=(len(vars) + 1) * ub)
            if not status:
                while cnt_pb < (1 - compression_percentage) * len(glue):
                    cnt_pb += 1
                    status, res = to_pb(glue, cnt_pb, max_sum=(len(vars) + 1) * ub)
                    if status:
                        break

            if status:
                # validate_ans([glue], [res])
                status, res = minimize_max_sum(glue, cnt_pb)
                assert status == True
                if debug:
                    print(f"new glue {len(glue)}, to {cnt_pb} pb")
                    print(glue)
                    print(res)
                for ind in indexes:
                    was_glue[ind] = True
                glues.append(glue)
                result_glues.append(res)
            else:
                if debug:
                    print("cant simp")
        compression_percentage -= 0.2
        diff += 1
        max_diff_var += 1

    remainder = []

    for is_used, clause in zip(was_glue, clauses):
        if not is_used:
            remainder.append(clause)

    return glues, remainder, result_glues
