from prettytable import PrettyTable

from util.DIMACS_parser import parse_cnf
from espresso_minimizer import espresso_minimizer

file = open("../cnf/BvP_5_4.cnf")
out = open("../mini/BvP_5_4.cnf", "w")

clause, var, clause_size = parse_cnf(file)

glues, remainder, result_glues = espresso_minimizer(clause)

cons = len(remainder) + sum(map(len, result_glues))

assert len(remainder) + sum(map(len, glues)) == clause_size

out.writelines(f"p cnf {var} {cons} \n")

def print_clause(clause, out):
    line = ""
    for lit in clause:
        line += str(lit) + " "
    line += "0"
    out.writelines(line + '\n')


for clause in remainder:
    print_clause(clause, out)


for clauses in result_glues:
    for clause in clauses:
        print_clause(clause, out)

# for clauses in glues:
#     for clause in clauses:
#         print_clause(clause, out)


def print_matrix(matrix):
    my_table = PrettyTable()
    my_table.field_names = ["--"] + list(range(1, len(matrix[0]) + 1))
    for i, line in enumerate(matrix):
        my_table.add_row([i + 1] + line)
    print(my_table)



def print_info_table(glues, result_glues):
    matrix = []
    max_glue = max(map(len, glues))
    max_result_glues = max(map(len, result_glues))
    for _ in range(max_result_glues):
        matrix.append([0] * max_glue)
    for glue, result_glue in zip(glues, result_glues):
        glue_len = len(glue)
        result_glue_len = len(result_glue)
        matrix[result_glue_len - 1][glue_len - 1] += 1
    print_matrix(matrix)


def print_stats(glues, remainder, result_glues):
    before = len(remainder) + sum(map(len, glues))
    after = len(remainder) + sum(map(len, result_glues))
    new = sum(map(len, result_glues))
    print(f"there were {before} clause")
    print(f"now {after} constraint")
    print(f"new pb_constraint: {new}")
    print(f"old clause: {after - new}")
    print_info_table(glues, result_glues)


print_stats(glues, remainder, result_glues)