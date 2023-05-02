def print_clause(clause, out_file = None):
    line = ""
    de = 1
    for lit in clause:
        line += " " + str(lit)
    line += " 0"
    if out_file:
        out_file.writelines(line + '\n')
    else:
        print(line)