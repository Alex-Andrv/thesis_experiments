def parse_cnf(file):
    clause = []

    var = 0
    clause_size = 0
    lines = file.readlines()
    for line in lines:
        words = line.split()
        if words[0] == "p":
            var = int(words[2])
            clause_size = int(words[3])
        elif words[0] != "c":
            assert words[len(words) - 1] == '0'
            words = list(map(int, words))
            clause.append(words[:-1])
    return clause, var, clause_size
