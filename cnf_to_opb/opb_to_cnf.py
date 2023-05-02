#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re

import pypblib
from pypblib import pblib


#
###############################################################################

PBLIB_OPS = {'<=': pblib.LEQ, '>=': pblib.GEQ, '=': pblib.BOTH}

HEADER_RE = re.compile(r'(.*)\s*#variable=\s*(\d+)\s*#constraint=\s*(\d+)\s*')
TERM_RE = re.compile(r'([+-]?\d)\s+x(\d+)')
IND_TERM_RE = re.compile(r'([>=|<=|=]+)\s+([+-]?\d+)')


#
###############################################################################

def transform_pb_to_cnf(pb_formula_path: str):
    config = pblib.PBConfig()
    config.set_PB_Encoder(pypblib.pblib.PB_ADDER)
    aux = pblib.AuxVarManager(1)
    pb2cnf = pblib.Pb2cnf(config)
    formula = pblib.VectorClauseDatabase(config)

    with open(pb_formula_path, 'r') as f:
        m = HEADER_RE.match(f.readline())
        aux.reset_aux_var_to(int(m.group(2)) + 1)

        reader = (l for l in map(str.strip, f) if l and l[0] != '*')
        for line in reader:
            wl = [pblib.WeightedLit(int(l), int(w))
                for w, l in TERM_RE.findall(line)]
            op, ind_term = IND_TERM_RE.search(line).groups()

            constraint = pblib.PBConstraint(wl, PBLIB_OPS[op], int(ind_term))
            pb2cnf.encode(constraint, formula, aux)
    return formula, aux


#
###############################################################################

if __name__ == '__main__':
    f, aux = transform_pb_to_cnf(sys.argv[1])
    f.print_formula("test.cnf", aux.get_biggest_returned_auxvar())