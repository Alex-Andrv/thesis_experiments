def print_clause_to_opb(clause, out_file=None):
    line = ""
    de = 1
    for lit in clause:
        if lit > 0:
            line += "1 x" + str(lit) + " "
        elif lit < 0:
            line += "-1 x" + str(abs(lit)) + " "
            de -= 1
    line += ">= " + str(de) + ";"
    if out_file:
        out_file.writelines(line + '\n')
    else:
        print(line)

def print_opb_header(var, clause_size, out=None):
    if out:
        out.writelines(f"* #variable= {var} #constraint= {clause_size} \n")
    else:
        print(f"* #variable= {var} #constraint= {clause_size} \n")


def print_pb_to_opb(pb, out_file=None):
    line = ""
    val_b, name_b = pb.pop()
    assert name_b == 'b'
    for val, name in pb:
        line += str(val) + " " + "x" + name + " "
    line += ">= " + str(val_b) + ";"
    if out_file:
        out_file.writelines(line + '\n')
    else:
        print(line)