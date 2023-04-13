from pyscipopt.scip import Model


def parse_cnf(file_name):
    f = open(file_name)
    lines = f.readlines()
    clauses = []
    for line in lines:
        words = line.split()
        if words[0] != 'p' and words[0] != 'c':
            i = 0
            clause = []
            while words[i] != "0" and i < len(words):
                clause.append(int(words[i]))
                i += 1
            assert words[i] == "0"
            i += 1
            clauses.append(clause)
    return clauses


cnf = parse_cnf("../../cnf/PvS_8_4.cnf")


def solve_scip_cnf(clauses):
    model = Model()

    model.setParam('display/verblevel', 4)

    variables = dict()

    for clause in clauses:
        line = -1
        for c in clause:
            if not abs(c) in variables:
                variables[abs(c)] = model.addVar(vtype="B", name=str(abs(c)), lb=0, ub=1)
            if c < 0:
                line += (1 - variables[abs(c)])
            else:
                line += variables[abs(c)]
        model.addCons(line >= 0)



    model.optimize()

    return model.getStatus() == "optimal"


print("SAT" if solve_scip_cnf(cnf) else "UNSAT")
