def parse_opb(input_f):
    lines = input_f.readlines()
    pb_constraints = []
    for line in lines:
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