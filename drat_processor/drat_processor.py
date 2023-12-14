import click
from pysat.formula import CNF
from tqdm import tqdm

MAX_INT = 10_000_000

@click.command()
@click.argument('drat_path', type=click.Path(exists=True))
@click.argument('task_path', type=click.Path(exists=True))
@click.argument('result_task_path', type=click.Path(exists=False))
@click.argument('max_clause_len', type=int, default=MAX_INT)
def run(drat_path, task_path, result_task_path, max_clause_len):
    clauses = set()
    with open(drat_path, "r") as drat:
        for line in tqdm(drat):
            line = line.strip()
            if line.startswith('d'):
                line = line[1:].strip()
                lits = tuple(sorted(list(map(int, line.split()))[:-1]))
                if lits in clauses:
                    clauses.remove(lits)
            else:
                lits = tuple(sorted(list(map(int, line.split()))[:-1]))
                if len(lits) < max_clause_len:
                    clauses.add(lits)
    print("drat file was processed")
    task = CNF(from_file=task_path)
    for clause in tqdm(clauses):
        task.append(clause)
    print("cnf was successful combine")
    task.to_file(result_task_path)
    print("ok!!")


if __name__ == "__main__":
    run()
