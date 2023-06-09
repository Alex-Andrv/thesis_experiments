def f_cng(glue, assumptions):
    ans = True
    for clause in glue:
        clause_val = False
        for v in clause:
            clause_val |= assumptions[v]
        ans &= clause_val
    return ans


def f_pb(pb_constraints, assumptions):
    ans = True

    for pb_constraint in pb_constraints:
        sum = 0
        b = None
        for coeff, name in pb_constraint:
            if name.startswith('b'):
                b = coeff
            else:
                sum += coeff * assumptions[int(name)]
        assert b is not None
        ans &= (sum >= b)


    return ans


def validate_ans(glues, result_glues):
    for glue, result_glue in zip(glues, result_glues):
        vars = list(set([abs(var) for c in glue for var in c]))
        for comb in range(1 << len(vars)):
            assumptions = dict()
            comb_tmp = comb
            for i in range(len(vars)):
                assumptions[vars[i]] = comb_tmp % 2
                assumptions[-vars[i]] = (comb_tmp + 1) % 2
                comb_tmp //= 2
            res_cnf = f_cng(glue, assumptions)
            res_pb = f_pb(result_glue, assumptions)
            assert res_cnf == res_pb


def validate_ans_cnf(glues, result_glues):
    for glue, result_glue in zip(glues, result_glues):
        vars = list(set([abs(var) for c in glue for var in c]))
        for comb in range(1 << len(vars)):
            assumptions = dict()
            comb_tmp = comb
            for i in range(len(vars)):
                assumptions[vars[i]] = comb_tmp % 2
                assumptions[-vars[i]] = (comb_tmp + 1) % 2
                comb_tmp //= 2
            res_cnf = f_cng(glue, assumptions)
            res_pb = f_cng(result_glue, assumptions)
            assert res_cnf == res_pb


def f_cs(cs, assumptions):
    terms, b, ref = cs
    sum = 0
    for var in terms:
        sum += assumptions[var]
    assert b is not None
    ans = (sum >= b)

    return ans == assumptions[ref]


def validate_ans_cs(cs, pbs):
    vars = list(set([abs(int(term[1])) for pb in pbs for term in pb[:-1]]))
    for comb in range(1 << len(vars)):
        assumptions = dict()
        comb_tmp = comb
        for i in range(len(vars)):
            assumptions[vars[i]] = comb_tmp % 2
            assumptions[-vars[i]] = (comb_tmp + 1) % 2
            comb_tmp //= 2
        res_pb = f_pb(pbs, assumptions)
        res_cs = f_cs(cs, assumptions)
        assert res_cs == res_pb