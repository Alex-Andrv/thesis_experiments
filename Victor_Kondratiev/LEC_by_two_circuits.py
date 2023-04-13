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
import ast
from toposort import toposort
#import tempfile
#import shutil
from functools import reduce
from threading import Timer
from itertools import combinations, product
print = functools.partial(print, flush=True)




#Parser
def createParser ():
  parser = argparse.ArgumentParser()
  parser.add_argument ('-nf', '--namefirst', nargs = '?', default = 'before.bench', help = 'First circuit file (in bench or AIGER (ASCII) format)')
  parser.add_argument ('-ns', '--namesecond', nargs = '?', default = 'after.bench', help = 'Second circuit file (in bench or AIGER (ASCII) format)')
  parser.add_argument ('-o', '--outputfilename', nargs = '?', default = 'before_vs_after.cnf', help = 'Name for output CNF')
  parser.add_argument ('-smf', '--split_miter_flag', nargs = '?', type = bool, default = False, help = 'Separate LEC making flag')
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
            inputs_names.append((input_gate_name,current_var_id))
            current_var_id += 1
          elif circuit_number == 2:
            vars_dict[input_gate_name] = input_var_ids
            inputs_names.append((input_gate_name,input_var_ids))
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
    elif output[0] -1 in vars_dict:
      output[1] = vars_dict[output[0] - 1]
    else:
      raise Error('OUTPUT NOT IN VARS_DICT')
  #pprint.pprint(vars_dict)
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

# Функция кодирования NOT гейта в КНФ
def encode_NOT_gate(line, var_map, circuit_flag = False):
  #G1gat = not(G2gat)
  clauses = []
  gate_outp = line.split()[0]
  gate_input = line.split('(')[1][:-1]
  if circuit_flag == False:
    var_outp = var_map[gate_outp]
    var_input = var_map[gate_input]
  else:
    var_outp = var_map[gate_outp]
    var_input = var_map[gate_input]
  clauses.extend([[-var_outp, -var_input],[var_outp, var_input]])
  return clauses


def encode_miter(outputs_names1, outputs_names2, current_var_id):
  miter_vars = []
  clauses = []
  miter_dict = dict()
  for output1, output2 in zip(outputs_names1, outputs_names2):
    clauses_, xor_var = encode_XOR_miter(output1, output2, current_var_id)
    miter_vars.append(xor_var)
    miter_dict[xor_var] = {abs(output1[1]), abs(output2[1])}
    clauses.extend(clauses_)
    current_var_id += 1
  clauses.append(miter_vars) 
  return clauses, miter_vars, miter_dict

def encode_XOR_miter(output1,output2,current_var_id):
  xor_outp = current_var_id
  xor_input1 = output1[1]
  xor_input2 = output2[1]
  xor_clauses = [[-xor_outp, -xor_input1, -xor_input2], 
                 [-xor_outp, xor_input1, xor_input2], 
                 [xor_outp, -xor_input1, xor_input2], 
                 [xor_outp, xor_input1, -xor_input2]]
  return xor_clauses, xor_outp


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

def make_header_and_comments(current_var_id, vars_miter, cnf_first_list, cnf_second_list, miter_list, inputs_names1, vars_dict1, outputs_names1, inputs_names2, vars_dict2, outputs_names2):
  header = 'p cnf ' + str(current_var_id + len(vars_miter) - 1) + ' ' + str(len(cnf_first_list)+len(cnf_second_list)+len(miter_list))
  comment_inputs = 'c inputs: ' + ' '.join([str(x[1]) for x in inputs_names1])
  first_circuit_vars = [x for x in vars_dict1.values() if x not in [x[1] for x in inputs_names1] and x > 0]
  comment_vars_first = 'c variables for gates in first scheme: ' + str(min(first_circuit_vars)) + ' ... ' +str(max(first_circuit_vars))
  comment_outputs_first = 'c outputs first scheme: ' + ' '.join([str(x[1]) for x in outputs_names1])
  second_circuit_vars = [x for x in vars_dict2.values() if x not in [x[1] for x in inputs_names2] and x > 0]
  comment_vars_second = 'c variables for gates in second scheme: ' + str(min(second_circuit_vars)) + ' ... ' +str(max(second_circuit_vars))
  comment_outputs_second = 'c outputs second scheme: ' + ' '.join([str(x[1]) for x in outputs_names2])
  comment_miter_vars = 'c miter variables: ' + ' '.join(list(map(str,vars_miter)))
  comment_layers = make_layers_comment(layers_vars)
  comments = [comment_inputs, comment_vars_first, comment_outputs_first, comment_vars_second, comment_outputs_second, comment_miter_vars, comment_layers]
  return header, comments

def make_layers_comment(layers_vars):
  comment = 'c layers:'
  n = 0
  for layer in layers_vars:
    comment += ' [[' if n == 0 else ', ['
    comment += ', '.join([str(x) for x in layer])
    comment += ']'
    n += 1
  print('c Number of layers:', n)
  comment += ']'
  return comment

def write_out_LEC_CNF(LECfilename, header, comments, dimacs_cnf_first, dimacs_cnf_second, dimacs_miter):
  with open(LECfilename,'w') as outf:
    print(header, file = outf)
    print(*comments, sep = '\n', file = outf)
    print(*dimacs_cnf_first, sep = '\n', file = outf)
    print(*dimacs_cnf_second, sep = '\n', file = outf)
    print(*dimacs_miter, sep = '\n', file = outf)

def make_separate_miter_cnfs(cnf_first_list, cnf_second_list, miter_list, miter_vars, LECfilename, inputs_names1):
  miter_list = miter_list[:-1]
  for i in range(1, len(miter_vars) + 1):
    make_separate_miter_cnf(miter_vars[i-1], cnf_first_list, cnf_second_list, miter_list, LECfilename, inputs_names1, i)
    

def make_separate_miter_cnf(miter_var, cnf_first_list, cnf_second_list, miter_list, LECfilename, inputs_names1, counter):
  clauses = []
  first_circuit_output = None
  second_circuit_output = None
  used_vars = set()
  used_vars.add(miter_var)
  clauses.append([miter_var])
  for clause in reversed(miter_list):
    if miter_var == abs(clause[0]):
      first_circuit_output = abs(clause[1])
      second_circuit_output = abs(clause[2])
    if abs(clause[0]) in used_vars:
      clauses.append([x for x in clause])
      used_vars.update([abs(lit_) for lit_ in clause])
  for clause in reversed(cnf_second_list):
    if abs(clause[0]) in used_vars:
      clauses.append([x for x in clause])
      used_vars.update([abs(lit_) for lit_ in clause])
  for clause in reversed(cnf_first_list):
    if abs(clause[0]) in used_vars:
      clauses.append([x for x in clause])
      used_vars.update([abs(lit_) for lit_ in clause])
  clauses.reverse()
  used_vars = {x[1] : x[0] + 1 for x in enumerate(sorted(list(used_vars)))}
  #used_vars = {x[1] : x[1] for x in enumerate(sorted(list(used_vars)))}
  #for clause in clauses:
    #for i in range(len(clause)):
      #clause[i] = used_vars[abs(clause[i])] if clause[i] > 0 else -used_vars[abs(clause[i])]
  header = 'p cnf ' + str(used_vars[miter_var]) + ' ' + str(len(clauses))
  comments = []
  current_inputs = []
  for x in inputs_names1:
    if x[1] in used_vars.keys():
      # current_inputs.append(used_vars[x[1]])
      current_inputs.append(x[1])
  #pprint.pprint(used_vars)
  #current_first_circuit_output = used_vars[first_circuit_output]
  #current_second_circuit_output = used_vars[second_circuit_output]
  current_first_circuit_output = first_circuit_output
  current_second_circuit_output = second_circuit_output
  comments.append('c inputs: ' + ' '.join([str(x) for x in current_inputs]))
  first_var_first_circuit = max([x for x in current_inputs]) + 1
  comments.append('c variables for gates in first scheme: ' + str(first_var_first_circuit) + ' ... ' + str(current_first_circuit_output))
  comments.append('c outputs first scheme: ' + str(current_first_circuit_output))
  comments.append('c variables for gates in first scheme: ' + str(current_first_circuit_output + 1) + ' ... ' + str(current_second_circuit_output))
  comments.append('c outputs second scheme: ' + str(current_second_circuit_output))
  comments.append('c original miter variable: ' + str(miter_var))
  #comments.append('c miter variables: ' + str(used_vars[miter_var]))
  comments.append('c miter variables: ' + str(miter_var))

  dimacs_cnf = list_to_clauses(clauses)
  current_LECfilename = str(miter_var)
  with open('slec_' + str(counter) + '_' + LECfilename,'w') as outf:
    print(header, file = outf)
    print(*comments, sep = '\n', file = outf)
    print(*dimacs_cnf, sep = '\n', file = outf)
  print('Separated LEC with outputs pair:', [first_circuit_output, second_circuit_output], 'was written to', 'slec_' + str(counter) + '_' + LECfilename)
    
def shuffle_var_names(cnf_first_list, cnf_second_list, miter_clauses, nof_vars_second_cnf, nof_inputs, miter_vars):
  old_var_names = [x for x in range(nof_inputs + 1, nof_vars_second_cnf + 1)]
  #print(old_var_names)
  #print()
  new_var_names = [x for x in range(nof_inputs + 1, nof_vars_second_cnf + 1)]
  random.shuffle(new_var_names)
  shuffle_dict = dict()
  #print(new_var_names)
  for old, new in zip(old_var_names, new_var_names):
    shuffle_dict[old] = new
  for clause in cnf_first_list:
    for i in range(len(clause)):
      if abs(clause[i]) > nof_inputs:
        clause[i] = -shuffle_dict[abs(clause[i])] if clause[i] < 0 else shuffle_dict[abs(clause[i])]
  for clause in cnf_second_list:
    for i in range(len(clause)):
      if abs(clause[i]) > nof_inputs:
        clause[i] = -shuffle_dict[abs(clause[i])] if clause[i] < 0 else shuffle_dict[abs(clause[i])]
  for clause in miter_clauses:
    for i in range(len(clause)):
      if abs(clause[i]) > nof_inputs and abs(clause[i]) not in miter_vars:
        clause[i] = -shuffle_dict[abs(clause[i])] if clause[i] < 0 else shuffle_dict[abs(clause[i])]


def get_toposort_layers(bench1, var_map1, bench2, var_map2, miter_dict):
  vars_layers = dict(miter_dict)
  for line in bench1:
    if 'AND' in line:
      gate_outp = int(line.split()[0][1:-3])
      gate_input1 = int(line.split('(')[1].split(',')[0][1:-3])
      gate_input2 = int(line.split()[3][:-1][1:-3])
      var_outp = var_map1[gate_outp]
      var_input1 = var_map1[gate_input1]
      var_input2 = var_map1[gate_input2]
      vars_layers[abs(var_outp)] = {abs(var_input1), abs(var_input2)}
  for line in bench2:
    if 'AND' in line:
      gate_outp = int(line.split()[0][1:-3])
      gate_input1 = int(line.split('(')[1].split(',')[0][1:-3])
      gate_input2 = int(line.split()[3][:-1][1:-3])
      var_outp = var_map2[gate_outp]
      var_input1 = var_map2[gate_input1]
      var_input2 = var_map2[gate_input2]
      vars_layers[abs(var_outp)] = {abs(var_input1), abs(var_input2)}
  #pprint.pprint(vars_layers)
  vars_layers_list = list(toposort(vars_layers))
  return vars_layers_list
######################################################################################################
##-----------------------------------------------MAIN-----------------------------------------------##
######################################################################################################


if __name__ == '__main__':
  #start_time = time.time()
  parser = createParser()
  namespace = parser.parse_args (sys.argv[1:])

  circuit1_filename = namespace.namefirst
  circuit2_filename = namespace.namesecond
  LECfilename = namespace.outputfilename

  if (circuit1_filename.endswith('.aig') == True) or (circuit1_filename.endswith('.aag') == True):
    bench1 = aig2bench(circuit1_filename)
  elif circuit1_filename.endswith('.bench') == True:
    bench1 = open(circuit1_filename,'r').readlines()
    for i in range(len(bench1)):
      if bench1[i][-1] == '\n':
        bench1[i] = bench1[i][:-1]
  else:
    raise Error('Unrecognized first circuit format')

  bench1, bench1_testname, nof_inputs1, nof_outputs1, nof_and_gates1, nof_not_gates1 = get_bench_header(bench1)

  #создаем карту гейты-переменные и списки входов и выходов
  current_var_id = 1
  vars_dict1, outputs_names1, inputs_names1, current_var_id = parse_bench_to_map(bench1, current_var_id, 1)
  nof_vars_first_cnf = current_var_id - 1

  if (circuit2_filename.endswith('.aig') == True) or (circuit2_filename.endswith('.aag') == True):
    bench2 = aig2bench(circuit2_filename)
  elif circuit2_filename.endswith('.bench'):
    bench2 = open(circuit2_filename,'r').readlines()
    for i in range(len(bench2)):
      if bench2[i][-1] == '\n':
        bench2[i] = bench2[i][:-1]
  else:
    raise Error('Unrecognized second circuit format')

  bench2, bench2_testname, nof_inputs2, nof_outputs2, nof_and_gates2, nof_not_gates2 = get_bench_header(bench2)

  #создаем карту гейты-переменные и списки входов и выходов
  vars_dict2, outputs_names2, inputs_names2, current_var_id = parse_bench_to_map(bench2, current_var_id, 2)
  nof_vars_second_cnf = current_var_id - 1

  # Кодируем первую схему в кнф
  cnf_first_list = encode_gates(bench1, vars_dict1)
  # pprint.pprint(cnf_first_list)

  # Кодируем вторую схему в кнф
  cnf_second_list = encode_gates(bench2, vars_dict2)
  # pprint.pprint(cnf_second_list)


  # создаем майтер
  miter_list, vars_miter, miter_dict = encode_miter(outputs_names1, outputs_names2, current_var_id)

  # перемешаиваем номера переменных если нужно
  #shuffle_var_names(cnf_first_list, cnf_second_list, miter_list, nof_vars_second_cnf, nof_inputs1, vars_miter)

  # создаем список слоёв с переменными (топосорт схемы)
  layers_vars = get_toposort_layers(bench1, vars_dict1, bench2, vars_dict2, miter_dict)

  # делаем заготовки для комментариев и хедера в DIMACS
  header, comments = make_header_and_comments(current_var_id, vars_miter, cnf_first_list, cnf_second_list, miter_list, inputs_names1, vars_dict1, outputs_names1, inputs_names2, vars_dict2, outputs_names2)

  # Переводим дизъюнкты из списков в DIMACS
  dimacs_cnf_first = list_to_clauses(cnf_first_list)
  dimacs_cnf_second = list_to_clauses(cnf_second_list)
  dimacs_miter = list_to_clauses(miter_list)

  # Записываем выходную КНФ
  write_out_LEC_CNF(LECfilename, header, comments, dimacs_cnf_first, dimacs_cnf_second, dimacs_miter)
  print('Complete LEC was written to', LECfilename)

  if namespace.split_miter_flag == True:
    print('CNFs with separate miter:')
    make_separate_miter_cnfs(cnf_first_list, cnf_second_list, miter_list, vars_miter, LECfilename, inputs_names1)





