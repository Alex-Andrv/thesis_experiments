from prettytable import PrettyTable


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
    var_with_zero_coeff = 0
    for pb_constraints in result_glues:
        for pb_constraint in pb_constraints:
            for coeff, name in pb_constraint:
                if coeff == 0:
                    var_with_zero_coeff += 1
    max_glue = max(map(len, glues))
    avg_glue = sum(map(len, glues)) / len(glues)
    min_glue = min(map(len, glues))
    print(f"there were {before} clause")
    print(f"now {after} constraint")
    print(f"new pb_constraint: {new}")
    print(f"old clause: {after - new}")
    print(f"variables with zero coefficient: {var_with_zero_coeff}")
    print(f"max compression clauses: {max_glue}")
    print(f"min_glue compression clauses: {min_glue}")
    print(f"avg_glue compression clauses: {avg_glue}")
    print_info_table(glues, result_glues)