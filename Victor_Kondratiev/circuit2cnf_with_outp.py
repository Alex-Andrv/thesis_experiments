#!/usr/bin/env python3.8

import time
import sys
import os
import argparse
import random
import copy
import signal
import json
import pprint
import itertools
import functools
import subprocess
#import tempfile
#import shutil
from functools import reduce
from threading import Timer
from itertools import combinations, product
print = functools.partial(print, flush=True)




#Parser
def createParser ():
  parser = argparse.ArgumentParser()
  parser.add_argument ('-n', '--namecircuit', nargs = '?', default = 'test.bench', help = 'Circuit file (in bench or AIGER (ASCII) format)')
  parser.add_argument ('-o', '--outputfilename', nargs = '?', default = 'test.cnf', help = 'Name for output CNF')
  parser.add_argument ('-sv', '--shuffle_vars_flag', nargs = '?', type = int, default = 0)
  return parser

class Error(Exception):
  pass

# Функция вырезает хедер из строк bench-файла и парсит его
def get_bench_header(bench):
  bench_testname = ''
  nof_inputs = 0
  nof_outputs = 0
  nof_and_gates = 0
  nof_not_gates = 0
  i = 0
  while i < len(bench):
    line = bench[i]
    if len(line) == 0:
      del bench[i]
    elif line[0] == '#':
      if 'testname' in line:
        bench_testname = line.split()[-1]
      elif 'input' in line:
        nof_inputs = int(line.split()[-1])
      elif 'output' in line:
        nof_outputs = int(line.split()[-1])
      elif 'not' in line:
        nof_not_gates = int(line.split()[-1])
      elif 'and' in line:
        nof_and_gates = int(line.split()[-1])
      del bench[i]
    else:
      i += 1
  return bench, bench_testname, nof_inputs, nof_outputs, nof_and_gates, nof_not_gates


# Функция берёт строки из bench-файла и строит по ним карту из
# имён гейтов и соответсвующих им номерам переменной для первой схемы.
# Так же создаёт список входных и выходных переменных в правильном порядке.
def parse_bench_to_map(bench_lines,start_var_id,circuit_number):
  vars_dict = dict()
  outputs_names = []
  inputs_names = []
  current_var_id = start_var_id
  input_var_ids = 1
  for line in bench_lines:
    if len(line) > 0:
      if 'INPUT' in line:
        input_gate_name = int(line[7:-4])
        if input_gate_name not in vars_dict:
          if circuit_number == 1:
            vars_dict[input_gate_name] = current_var_id
            inputs_names.append([input_gate_name,current_var_id])
            current_var_id += 1
          elif circuit_number == 2:
            vars_dict[input_gate_name] = input_var_ids
            inputs_names.append([input_gate_name,input_var_ids])
            input_var_ids += 1
          else:
            raise 'WRONG SCHEME NUMBER IN parse_bench_to_map'
      elif 'OUTPUT' in line:
        output_gate_name = int(line[8:-4])
        outputs_names.append([output_gate_name, None])
      elif line[0] == 'G':
        internal_gate_name = int(line.split(' =')[0][1:-3])
        if internal_gate_name not in vars_dict:
          if internal_gate_name % 2 == 0:
            vars_dict[internal_gate_name] = current_var_id
            current_var_id += 1
          else:
            if internal_gate_name - 1 in vars_dict:
              vars_dict[internal_gate_name] = -vars_dict[internal_gate_name - 1]
            else:
              vars_dict[internal_gate_name - 1] = current_var_id
              vars_dict[internal_gate_name] = -vars_dict[internal_gate_name - 1]
              current_var_id += 1
  for output in outputs_names:
    if output[0] in vars_dict:
      output[1] = vars_dict[output[0]]
    elif output[0] - 1 in vars_dict:
      output[1] = vars_dict[output[0] - 1]
    else:
      raise Error('OUTPUT NOT IN VARS_DICT')
  return vars_dict, outputs_names, inputs_names, current_var_id


# Функция принимает на вход карту переменных, строки bench-файла
# флаг первой/второй схемы и имя сломанного гейта (для второй схемы)
# и строит по ним дизъюнкты
def encode_gates(bench_lines, vars_dict):
  clauses = []
  for line in bench_lines:
    # print(line)
    clauses_ = None
    if 'AND' in line:
      clauses_ = encode_AND_gate(line, vars_dict)
    if clauses_ != None:
      clauses.extend(clauses_)
  return clauses

# Функция кодирования AND гейта в КНФ
def encode_AND_gate(line, var_map, circuit_flag = False):
  #G1gat = and(G2gat, G3gat)
  clauses = []
  gate_outp = int(line.split()[0][1:-3])
  gate_input1 = int(line.split('(')[1].split(',')[0][1:-3])
  gate_input2 = int(line.split()[3][:-1][1:-3])
  if circuit_flag == False:
    var_outp = var_map[gate_outp]
    var_input1 = var_map[gate_input1]
    var_input2 = var_map[gate_input2]
  else:
    var_outp = var_map[gate_outp]
    var_input1 = var_map[gate_input1]
    var_input2 = var_map[gate_input2]
  clauses.extend([[var_outp, -var_input1, -var_input2], [-var_outp, var_input1], [-var_outp, var_input2]])
  return clauses

def solve_CNF(cnf, timelimit):
  solver = subprocess.run(["./kissat", "--time="+str(timelimit)], capture_output=True, text=True, input = cnf)
  result = solver.stdout.split('\n')
  errors = solver.stderr
  if len(errors) > 0:
    print(errors)
  return result

def list_to_clauses(clist):
  clauses = []
  for l in clist:
    clause = ' '.join(list(map(str,l))) + ' 0'
    clauses.append(clause)
  return clauses

def aig2bench(filename):
  aig_filename = filename
  test_name = (aig_filename.split('/')[-1]).split('.')[0]
  aig_file_lines = open(aig_filename).readlines()
  aig_header = aig_file_lines[0].split()
  max_var_index = int(aig_header[1])
  nof_inputs = int(aig_header[2])
  nof_latches = int(aig_header[3])
  nof_outputs = int(aig_header[4])
  nof_and_gates = int(aig_header[5])
  del aig_file_lines[0]
  not_gates = dict()

  #заполняем инпуты
  inputs_list = []
  for i in range(nof_inputs):
    inputs_list.append(int(aig_file_lines[0]))
    del aig_file_lines[0] 
  #print(inputs_list)

  #заполняем аутпуты (если аутпут нечетный, то добавляем сразу не-гейт с ним)
  outputs_list = []
  for i in range(nof_outputs):
    outputs_list.append(int(aig_file_lines[0]))
    if int(aig_file_lines[0])%2 > 0:
      not_tuple = (int(aig_file_lines[0]),int(aig_file_lines[0])-1)
      if not_tuple not in not_gates:
        not_gates[not_tuple] = 1
    del aig_file_lines[0] 

  const_false = False
  const_true = False
  and_gates = []
  for line in aig_file_lines:
    if line[0].isdigit():
      and_gate_name = int(line.split()[0])
      first_input = int(line.split()[1])
      second_input = int(line.split()[2])
      if first_input % 2 > 0 and first_input > 1:
        not_tuple = (first_input,first_input-1)
        if not_tuple not in not_gates:
          not_gates[not_tuple] = 1
      if second_input % 2 > 0 and second_input > 1:
        not_tuple = (second_input,second_input-1)
        if not_tuple not in not_gates:
          not_gates[not_tuple] = 1
      if first_input == 0 or second_input == 0:
        const_false = True
      if first_input == 1 or second_input == 1:
        const_true = True
      and_tuple = tuple([and_gate_name,first_input,second_input])
      and_gates.append(and_tuple)

  if const_false == True or const_true == True:
    if tuple([3, 2]) not in not_gates.keys():
      not_gates[tuple([3, 2])] = 1
    and_gates.append(tuple([0,2,3]))
    if const_true == True:
      not_gates[tuple([1,0])] = 1
  result = []
  result.append('# testname: ' + str(test_name))
  result.append('#         lines from primary input  gates .......     ' + str(len(inputs_list)))
  result.append('#         lines from primary output gates .......     ' + str(len(outputs_list)))
  result.append('#         lines from primary not gates .......     ' + str(len(not_gates)))
  result.append('#         lines from primary and gates .......     ' + str(len(and_gates)))
  for inp in sorted(inputs_list):
    input_line = 'INPUT(G' + str(inp) + 'gat)'
    result.append(input_line)
  for outp in outputs_list:
    output_line = 'OUTPUT(G' + str(outp) + 'gat)'
    result.append(output_line)
  result.append('')
  lines = []
  for not_gate in not_gates.keys():
    #G2gat = not(G1gat)
    not_gate_outp = not_gate[0]
    not_gate_inp = not_gate[1]
    not_line = 'G'+str(not_gate_outp)+'gat = NOT(G'+str(not_gate_inp)+'gat)'
    lines.append((not_line,not_gate))
    #print(not_line,file=outfile)
  for and_gate in and_gates:
    and_gate_outp = and_gate[0]
    and_gate_inp1 = and_gate[1]
    and_gate_inp2 = and_gate[2]
    #G3gat = and(G1gat, G2gat)
    and_line = 'G'+str(and_gate_outp)+'gat = AND(G'+str(and_gate_inp1)+'gat, G'+str(and_gate_inp2)+'gat)'
    lines.append((and_line,and_gate))
    #print(and_line,file=outfile)
  lines.sort(key = lambda x: int(max(x[1])))
  lines = [x[0] for x in lines]
  result += lines
  return result

def encode_output_equiv(max_var, outputs_names):
  new_clauses = []
  current_var = max_var
  for output_name in outputs_names:
    output_var = output_name[1]
    new_clauses_, current_var = encode_EQUIV_clauses(output_var, current_var)
    output_name[1] = current_var
    new_clauses.extend(new_clauses_)
  return new_clauses, current_var

def encode_EQUIV_clauses(output_var, current_var):
  current_var += 1
  clauses = [[-current_var, output_var],
             [current_var, -output_var]]
  return clauses, current_var

def shuffle_var_names(clauses_list, max_var, inputs_names, outputs_names):
  old_var_names = [x for x in range(1, max_var + 1)]
  new_var_names = [x for x in range(1, max_var + 1)]
  random.shuffle(new_var_names)
  shuffle_dict = dict()
  #print(new_var_names)
  for old, new in zip(old_var_names, new_var_names):
    shuffle_dict[old] = new
  #pprint.pprint(shuffle_dict)
  for clause in clauses_list:
    for i in range(len(clause)):
      clause[i] = -shuffle_dict[abs(clause[i])] if clause[i] < 0 else shuffle_dict[abs(clause[i])]
  for pair in inputs_names:
    #print(pair)
    pair[1] = shuffle_dict[abs(pair[1])]
  for pair in outputs_names:
    #print(pair)
    pair[1] = shuffle_dict[abs(pair[1])]

def make_header_and_comments(len_clauses_list, max_var, inputs_names, vars_dict, outputs_names):
  header = 'p cnf ' + str(max_var) + ' ' + str(len_clauses_list)
  comment_inputs = 'c inputs: ' + ' '.join([str(x[1]) for x in inputs_names])
  circuit_vars = [x for x in vars_dict.values() if x not in [x[1] for x in inputs_names] and x > 0]
  comment_vars = 'c variables for gates: ' + str(min(circuit_vars)) + ' ... ' +str(max(circuit_vars))
  comment_outputs = 'c outputs: ' + ' '.join([str(x[1]) for x in outputs_names])
  comments = [comment_inputs, comment_vars, comment_outputs]
  return header, comments

def write_out_CNF(LECfilename, header, comments, dimacs_cnf,):
  with open(LECfilename,'w') as outf:
    print(header, file = outf)
    print(*comments, sep = '\n', file = outf)
    print(*dimacs_cnf, sep = '\n', file = outf)

def rand_sign(x):
  return (-1 if random.randint(0,1) == 0 else 1) * x

def create_and_solve_CNF(task_index, clauses, new_clauses, max_var, solver):
  cnf_str = create_str_CNF(clauses, new_clauses, max_var)
  #if task_index == 864:
    #with open('lec_CvK_16_dec2_task' + str(task_index) + '.cnf', 'w') as f:
      #print(cnf_str, file = f)
  result = solve_CNF(cnf_str, solver)
  model = get_model_from_solver_log(result)
  answer = 'INDET'
  time = None
  conflicts = None
  for line in result:
    if len(line) > 0 and line[0] == 's':
      if 'UNSAT' in line:
        answer = 'UNSATISFIABLE'
      elif 'SAT' in line:
        answer = 'SATISFIABLE'
    elif ('c process-time' in line and 'kissat' in solver) or ('c total process time' in line and 'cadical' in solver) or ('c CPU time' in line):
      time = float(line.split()[-2])
    elif ('c conflicts:' in line and 'kissat' in solver) or ('c conflicts:' in line and 'cadical' in solver):
      conflicts = int(line.split()[-4])
    elif ('c conflicts ' in line):
      conflicts = int(line.split()[3])
  return answer, time, conflicts, model

def get_model_from_solver_log(result):
  model = []
  for line in result:
    if len(line) > 0 and line[0] == 'v':
      model.append(list(map(int,line.split()[1:])))
  model = flatten(model)
  if model[-1] == 0:
    model = model[:-1]
  return model

def create_str_CNF(clauses, new_clauses, max_var):
  lines = []
  header_ = 'p cnf ' + str(max_var) + ' ' + str(len(clauses)+len(new_clauses))
  lines.append(header_)
  lines.extend([' '.join(list(map(str,clause))) + ' 0' for clause in clauses])
  lines.extend([' '.join(list(map(str,clause))) + ' 0' for clause in new_clauses])
  cnf = '\n'.join(lines)
  #pprint.pprint(cnf)
  return cnf


def solve_CNF(cnf, solver):
  solver = subprocess.run(["/home/vkondratev/data/Solvers/Binaries/" + solver], capture_output=True, text=True, input = cnf)
  result = solver.stdout.split('\n')
  errors = solver.stderr
  #print(result)
  if len(errors) > 0:
    print(errors)
  return result

def flatten(l):
    return [item for sublist in l for item in sublist]

def get_output_from_model(model, outp_vars):
  return [[x] for x in model if abs(x) in outp_vars]
######################################################################################################
##-----------------------------------------------MAIN-----------------------------------------------##
######################################################################################################


if __name__ == '__main__':
  #start_time = time.time()
  parser = createParser()
  namespace = parser.parse_args (sys.argv[1:])

  circuit_filename = namespace.namecircuit
  LECfilename = namespace.outputfilename
  shuffle_vars_flag = namespace.shuffle_vars_flag

  if (circuit_filename.endswith('.aig') == True) or (circuit_filename.endswith('.aag') == True):
    bench = aig2bench(circuit_filename)
  elif circuit_filename.endswith('.bench') == True:
    bench = open(circuit_filename,'r').readlines()
    for i in range(len(bench)):
      if bench[i][-1] == '\n':
        bench[i] = bench[i][:-1]
  else:
    raise Error('Unrecognized circuit format')

  bench, bench_testname, nof_inputs, nof_outputs, nof_and_gates, nof_not_gates = get_bench_header(bench)

  #создаем карту гейты-переменные и списки входов и выходов
  current_var_id = 1
  vars_dict, outputs_names, inputs_names, current_var_id = parse_bench_to_map(bench,current_var_id,1)
  max_var = current_var_id - 1


  # Кодируем первую схему в кнф
  clauses_list = encode_gates(bench, vars_dict)
  print(outputs_names)

  if [x[1] for x in outputs_names] != list(range(max_var - len(outputs_names) + 1, max_var + 1)):
    output_equiv_clauses, max_var = encode_output_equiv(max_var, outputs_names)
    clauses_list.extend(output_equiv_clauses)

  # перемешаиваем номера переменных если нужно
  if shuffle_vars_flag == 1:
    shuffle_var_names(clauses_list, max_var, inputs_names, outputs_names)

  #print(outputs_names)


  create_random_inp = [[rand_sign(x[1])] for x in inputs_names]

  answer, time, conflicts, model = create_and_solve_CNF(0, clauses_list, create_random_inp, max_var, 'kissat2022')

  current_outp = get_output_from_model(model, [x[1] for x in outputs_names])
  print('Random input:', create_random_inp)
  print('Corresonding output:', current_outp)
  clauses_list.extend(current_outp)


  # Переводим дизъюнкты из списков в DIMACS
  dimacs_cnf = list_to_clauses(clauses_list)

  # делаем заготовки для комментариев и хедера в DIMACS
  header, comments = make_header_and_comments(len(clauses_list), max_var, inputs_names, vars_dict, outputs_names)

  # Записываем выходную КНФ
  write_out_CNF(LECfilename, header, comments, dimacs_cnf)
  sat_assignment_filename = LECfilename.split('.')[0] + '.sat_assignment'
  with open(sat_assignment_filename, 'w') as f:
    print('s', answer, file = f)
    print('v', *model, '0', sep = ' ', file = f)
  print('CNF was written to', LECfilename)






