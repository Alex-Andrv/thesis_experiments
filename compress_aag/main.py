from tqdm import tqdm

from compression.simplification_v_3 import to_pb, minimize_max_sum
from util.AAG_parser import parse_aag
from util.stats import print_stats
from util.validate import validate_ans

file = open("../aag/BvP_7_4.aag")
out = open("../aag_to_cnf/BvP_7_4_simple.opb", "w")

inputs, outputs, gates, max_var = parse_aag(file)

used = set()
queue = [o // 2 for o in outputs]
simple = True

def reformat(var):
    return (var // 2) * (-1 if var % 2 == 1 else 1)


def gate_to_cnf(z, a, b):
    z = reformat(z)
    a = reformat(a)
    b = reformat(b)
    return [[-z, a], [-z, b], [-a, -b, z]]


result_glues = []
glues = []


def _to_pb(clauses):
    cnt_pb = 1
    status, res = to_pb(clauses, cnt_pb)
    if not status:
        while cnt_pb < 5:
            cnt_pb += 1
            status, res = to_pb(clauses, cnt_pb)
            if status:
                status, res = minimize_max_sum(clauses, cnt_pb)
                break
    assert status == True
    return res


def check_and_get(a, used, gates, clauses, queue, pbar):
    val_a = a // 2
    if (val_a not in used) and (val_a in gates):
        pbar.update(1)
        used.add(val_a)
        a1, a2, a_nt = gates[val_a]
        clauses.extend(gate_to_cnf(val_a * 2 + nt, a1, a2))
        val_a1 = a1 // 2
        val_a2 = a2 // 2
        if (val_a1 not in used) and (val_a1 in gates):
            queue.append(val_a1)
        if (val_a2 not in used) and (val_a2 in gates):
            queue.append(val_a2)


pbar = tqdm(total=len(gates))

while queue:
    clauses = []
    z = queue.pop(0)
    if z in used:
        print("kek")
        continue
    used.add(z)
    a, b, nt = gates[z]
    pbar.update(1)
    clauses.extend(gate_to_cnf(z * 2 + nt, a, b))
    if simple:
        val_a = a // 2
        val_b = b // 2
        if (val_a not in used) and (val_a in gates):
            queue.append(val_a)
        if (val_b not in used) and (val_b in gates):
            queue.append(val_b)
    else:
        check_and_get(a, used, gates, clauses, queue, pbar)
        check_and_get(b, used, gates, clauses, queue, pbar)
    glues.append(clauses)
    print(clauses)
    result_glues.append(_to_pb(clauses))


def print_glue_res(res, out):
    line = ""
    val_b, name_b = res.pop()
    assert name_b[:-2] == 'b'
    for val, name in res:
        line += str(val) + "  " + "x" + name[:-2] + " "
    line += ">= " + str(val_b) + ";"
    out.writelines(line + '\n')

assert len(used) == len(gates)

validate_ans(glues, result_glues)

constraints = sum(map(len, result_glues))

out.writelines(f"* #variable= {max_var} #constraint= {constraints} \n")

for pb_constraints in result_glues:
    for pb_constraint in pb_constraints:
        print_glue_res(pb_constraint, out)

print_stats(glues, [], result_glues)
