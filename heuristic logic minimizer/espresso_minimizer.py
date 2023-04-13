import random
from functools import reduce

from pyeda.boolalg.expr import Complement
from pyeda.inter import *
from tqdm import tqdm


def cnt_vars(clauses):
    return sum(map(len, clauses))


def parse_var(v):
    assert isinstance(v, Variable) | isinstance(v, Complement)
    if isinstance(v, Complement):
        assert v.top.name.startswith('x')
        var = -1 * int(v.top.name[1:])
    else:
        assert v.name.startswith('x')
        var = int(v.name[1:])
    return var


def to_clauses(new_clause_min):
    clauses = []
    if isinstance(new_clause_min, Variable) | isinstance(new_clause_min, Complement):
        return [[parse_var(new_clause_min)]]
    for new_clause in new_clause_min.xs:
        clause = []
        if isinstance(new_clause, Variable) | isinstance(new_clause, Complement):
            clause = [parse_var(new_clause)]
        else:
            for v in new_clause.xs:
                clause.append(parse_var(v))

        clauses.append(clause)
    return clauses


def mini(clauses):
    vars = dict()
    new_clause = []
    for clause in clauses:
        conjunct = []
        for c in clause:
            var = abs(c)
            if var not in vars:
                vars[var] = exprvar('x' + str(var))
            if c < 0:
                conjunct.append(vars[var])
            else:
                conjunct.append(~vars[var])

        new_clause.append(reduce(lambda a, b: a & b, conjunct))

    new_clause = reduce(lambda a, b: a | b, new_clause)

    new_clause_min, = espresso_exprs(new_clause.to_dnf())
    new_clause_min = ~new_clause_min
    new_clause_min = new_clause_min.to_cnf()

    return to_clauses(new_clause_min)


def return_glue(glue, res, indexes):
    glue_copy = glue.copy()
    res_copy = res.copy()
    glue_copy = [sorted(c) for c in glue_copy]
    res_copy = [sorted(c) for c in res_copy]
    glue_ans = []
    indexes_ans = []
    for glue, ind in zip(glue_copy, indexes):
        skip = False
        for res in res_copy:
            if glue == res:
                skip = True
                break
        if not skip:
            glue_ans.append(glue)
            indexes_ans.append(ind)

    res_ans = []
    for res in res_copy:
        skip = False
        for glue in glue_copy:
            if glue == res:
                skip = True
                break
        if not skip:
            res_ans.append(res)

    return glue_ans, res_ans, indexes_ans


def espresso_minimizer(clauses: list, diff=10, max_diff_var=25, restart=1, debug=False):
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
            while j < len_clauses:
                if was_glue[j]:
                    j += 1
                    continue
                vj = set([abs(c) for c in clauses[j]])
                if (len(vj - vars) <= diff and len(vars) < max_diff_var) or (len(vj - vars) == 0):
                    indexes.append(j)
                    vars.update(vj)
                    glue.append(clauses[j])
                j += 1

            res = mini(glue)

            g_glue, g_res, indexes = return_glue(glue, res, indexes)

            if cnt_vars(g_res) < cnt_vars(g_glue):
                if debug:
                    print(f"new glue {len(glue)}, to {len(res)}. Was var {cnt_vars(glue)}, now {cnt_vars(res)}")
                for ind in indexes:
                    was_glue[ind] = True

                glues.append(g_glue)
                result_glues.append(g_res)

        new_clauses = []
        for is_used, clause in zip(was_glue, clauses):
            if not is_used:
                new_clauses.append(clause)
        clauses = new_clauses
        random.shuffle(clauses)
        was_glue = [False] * len(clauses)
        len_clauses = len(clauses)


    remainder = []

    for is_used, clause in zip(was_glue, clauses):
        if not is_used:
            remainder.append(clause)

    return glues, remainder, result_glues
