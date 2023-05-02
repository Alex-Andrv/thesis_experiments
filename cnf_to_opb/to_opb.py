from util.DIMACS_parser import parse_cnf
from util.OPB_writer import print_clause_to_opb, print_opb_header

file = open("../cnf/wallace12x12.cnf")
out = open("wallace12x12.opb", "w")

clause, var, clause_size = parse_cnf(file)
print_opb_header(var, clause_size, out)
for c in clause:
    print_clause_to_opb(c, out)