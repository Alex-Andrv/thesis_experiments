from compression.simplification import simplification
from compression.simplification_v_2 import simplification_v_2
from util.DIMACS_parser import parse_cnf
from util.stats import print_stats

from util.validate import validate_ans

file = open("../snake-in-the-box/cnfs/s-n-b_8_96.cnf")
out = open("../s-n-b_8_96.opb", "w")

clause, var, clause_size = parse_cnf(file)

glues, remainder, result_glues = simplification(clause)

# 100
# 540
# 5

validate_ans(glues, result_glues)

cons = len(remainder) + sum(map(len, result_glues))

assert len(remainder) + sum(map(len, glues)) == clause_size

out.writelines(f"* #variable= {var} #constraint= {cons} \n")

def print_clause(clause, out):
    line = ""
    de = 1
    for lit in clause:
        if lit > 0:
            line += "1 x" + str(lit) + " "
        elif lit < 0:
            line += "-1 x" + str(abs(lit)) + " "
            de -= 1
    line += ">= " + str(de) + ";"
    out.writelines(line + '\n')


def print_glue_res(res, out):
    line = ""
    val_b, name_b = res.pop()
    assert name_b[:-2] == 'b'
    for val, name in res:
        line += str(val) + "  " + "x" + name[:-2] + " "
    line += ">= " + str(val_b) + ";"
    out.writelines(line + '\n')


for clause in remainder:
    print_clause(clause, out)


for pb_constraints in result_glues:
    for pb_constraint in pb_constraints:
        print_glue_res(pb_constraint, out)



print_stats(glues, remainder, result_glues)



