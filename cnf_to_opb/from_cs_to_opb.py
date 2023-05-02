from tqdm import tqdm

from util.DIMACS_parser import parse_cs_cnf
from util.OPB_writer import print_opb_header, print_clause_to_opb, print_pb_to_opb
from util.validate import validate_ans_cs

file = open("../neural_networks/cifar10-l-advnone-ternweight/Formula.cnf")
out = open("../neural_networks/cifar10-l-advnone-ternweight/Formula.opb", "w")
# file = open("../neural_networks/simple3.cnf")
# out = open("../neural_networks/simple3.opb", "w")

clauses, cardinality_constraints, var, all_clause_size, clause_size, cardinality_constraint_size = parse_cs_cnf(file)
print_opb_header(var, clause_size + cardinality_constraint_size * 2, out)
for clauses in clauses:
    print_clause_to_opb(clauses, out)

for terms, b, ref in tqdm(cardinality_constraints):
    de = 0
    _term = []
    for i in range(len(terms)):
        if terms[i] < 0:
            _term.append((-1, str(abs(terms[i]))))
            de += 1
        else:
            _term.append((1, str(abs(terms[i]))))
    n = len(_term)
    first = _term.copy()
    second = _term.copy()
    second = list(map(lambda x: (x[0] * -1, x[1]), second))
    if ref > 0:
        first.append((-b, str(ref)))
        first.append((-de, "b"))
        second.append((n, str(ref)))
        second.append((de - b + 1, "b"))
    else:
        first.append((b, str(abs(ref))))
        first.append((-de + b, "b"))
        second.append((-n, str(abs(ref))))
        second.append((de - b + 1 - n, "b"))
    # validate_ans_cs((terms, b, ref), [first, second])
    print_pb_to_opb(first, out)
    print_pb_to_opb(second, out)
