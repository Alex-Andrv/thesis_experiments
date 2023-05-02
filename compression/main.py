from compression.simplification import simplification
from compression.simplification_v_3 import simplification_v_3
from compression.simplification_v_4 import simplification_v_4
from util.DIMACS_parser import parse_cnf
from util.OPB_writer import print_pb_to_opb, print_clause_to_opb
from util.stats import print_stats

from util.validate import validate_ans

for file_name in ['cvd', 'cvk', 'cvw', 'dvk', 'dvw', 'kvw']:
    file = open(f"../diplom_cnf/{file_name}.cnf")
    out = open(f"../diplom_opb_v_1_new/{file_name}.opb", "w")

    clause, var, clause_size = parse_cnf(file)

    glues, remainder, result_glues = simplification(clause)

    validate_ans(glues, result_glues)

    cons = len(remainder) + sum(map(len, result_glues))

    assert len(remainder) + sum(map(len, glues)) == clause_size

    out.writelines(f"* #variable= {var} #constraint= {cons} \n")

    for clause in remainder:
        print_clause_to_opb(clause, out)

    for pb_constraints in result_glues:
        for pb_constraint in pb_constraints:
            print_pb_to_opb(pb_constraint, out)

    print_stats(glues, remainder, result_glues)



