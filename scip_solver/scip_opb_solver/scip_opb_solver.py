from pyscipopt.scip import Model

def parse_opb(file_name):
    f = open(file_name)
    lines = f.readlines()
    pb_constraints = []
    for line in lines:
        pb_constraint = None
        words = line.split()
        if words[0] != '*':
            i = 0
            terms = []
            while words[i] != ">=" and i < len(words):
                terms.append((int(words[i]), words[i + 1]))
                i += 2
            assert words[i] == ">="
            i += 1
            b = int(words[i][:-1])
            pb_constraint = (terms, b)
            pb_constraints.append(pb_constraint)
    return pb_constraints

pb_constraints = parse_opb("../../diplom_opb_v_4_with_restart/cvd.opb")


def solve_scip(pb_constraints):
    model = Model()

    model.setParam('display/verblevel', 5)

    variables = dict()

    for pb_constraint in pb_constraints:
        terms, b = pb_constraint
        line = -b
        for term in terms:
            if not term[1] in variables:
                variables[term[1]] = model.addVar(vtype="B", name=term[1], lb=0, ub=1)
            line += term[0] * variables[term[1]]
        model.addCons(line >= 0)

    model.optimize()

    return model.getStatus() == "optimal"


print("SAT" if solve_scip(pb_constraints) else "UNSAT")