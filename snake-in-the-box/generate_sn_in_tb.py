from pysat.formula import CNF
from pysat.card import *

def vareqxor(lp,rp1,rp2, clauses):
    clauses.append([-lp, -rp1, -rp2])
    clauses.append([-lp, rp1, rp2])
    clauses.append([lp, -rp1, rp2])
    clauses.append([lp, rp1, -rp2])

def only_one_simple(vars,clauses):
    lcl = list()    
    for u in range(len(vars)):
        for h in range(u+1, len(vars)):
            clauses.append([-vars[u],-vars[h]])
    for u in vars:
        lcl.append(u)
    clauses.append(lcl)
    
def at_least_two_plain(vars,clauses):
    clauses.append(vars)
    for u in range(len(vars)):
        cl = list()
        for h in range(len(vars)):
            if u == h:
                cl.append(-vars[h])
            else:
                cl.append(vars[h])
        clauses.append(cl)
    
def generate_snake_in_the_box_plain(cube_dimension, snake_size):
    #allocate variables    
    encoding = list()
    nvars = 1
    step_vars = list()
    for _ in range(snake_size + 1):
        vl = list()
        for _ in range(cube_dimension):
            vl.append(nvars)
            nvars += 1
        step_vars.append(vl)

    #generate encoding
    #specify that between each two consecutive steps only a single coordinate changes
    for i in range(1, len(step_vars)):
        newvars = range(nvars,nvars+cube_dimension)
        nvars += cube_dimension 
        for u in range(len(newvars)):
            vareqxor(newvars[u],step_vars[i][u], step_vars[i-1][u],encoding)
        only_one_simple(newvars,encoding)
    
    #specify that between each two non-consecutive steps at least two coordinates change

    for i in range(2, len(step_vars)):
        for j in range(i-2,-1,-1):
            newvars = range(nvars,nvars+cube_dimension)
            nvars += cube_dimension 
            for u in range(len(newvars)):
                vareqxor(newvars[u],step_vars[i][u], step_vars[j][u],encoding)
            at_least_two_plain(newvars,encoding)
    return encoding
    


def generate_snake_in_the_box_plain_CNF(cube_dimension, snake_size, filename_out):
    #allocate variables    
    encoding = CNF()
    nvars = 1
    step_vars = list()
    for _ in range(snake_size + 1):
        vl = list()
        for _ in range(cube_dimension):
            vl.append(nvars)
            nvars += 1
        step_vars.append(vl)

    #generate encoding
    #specify that between each two consecutive steps only a single coordinate changes
    for i in range(1, len(step_vars)):
        newvars = range(nvars,nvars+cube_dimension)
        nvars += cube_dimension 
        for u in range(len(newvars)):
            vareqxor(newvars[u],step_vars[i][u], step_vars[i-1][u],encoding)
        only_one_simple(newvars,encoding)
    
    #specify that between each two non-consecutive steps at least two coordinates change

    for i in range(2, len(step_vars)):
        for j in range(i-2,-1,-1):
            newvars = range(nvars,nvars+cube_dimension)
            nvars += cube_dimension 
            for u in range(len(newvars)):
                vareqxor(newvars[u],step_vars[i][u], step_vars[j][u],encoding)
            at_least_two_plain(newvars,encoding)    
    with open(filename_out,'w') as fp:
        encoding.to_fp(fp)

def generate_snake_in_the_box_card_CNF(cube_dimension, snake_size, cardenc, filename_out):
    #allocate variables
    encoding = CNF()
    nvars = 1
    step_vars = list()
    for _ in range(snake_size + 1):
        vl = list()
        for _ in range(cube_dimension):
            vl.append(nvars)
            nvars += 1
        step_vars.append(vl)

    #generate encoding
    #specify that between each two consecutive steps only a single coordinate changes
    for i in range(1, len(step_vars)):
        newvars = range(nvars,nvars+cube_dimension)
        nvars += cube_dimension 
        for u in range(len(newvars)):
            vareqxor(newvars[u],step_vars[i][u], step_vars[i-1][u],encoding)
        only_one_simple(newvars,encoding)
    
    #specify that between each two non-consecutive steps at least two coordinates change

    for i in range(2, len(step_vars)):
        for j in range(i-2,-1,-1):
            newvars = range(nvars,nvars+cube_dimension)
            nvars += cube_dimension 
            for u in range(len(newvars)):
                vareqxor(newvars[u],step_vars[i][u], step_vars[j][u],encoding)
            #at_least_two_plain(newvars,encoding)    
#            print(nvars)
            f = CardEnc.atleast(lits = newvars, bound=2, top_id=nvars, vpool=None, encoding=cardenc)
            encoding.extend(f)
            for h in f:
                for g in h:
                    if g >= nvars:
                        nvars = g + 1
#            print(nvars)
    with open(filename_out,'w') as fp:
        encoding.to_fp(fp)


def print_encoding(encoding, filename):
    nvars = 0
    for u in encoding:
        for v in u:
            if nvars < v:
                nvars = v
    with open(filename,'w') as outfile:
        outfile.write("p cnf {} {}\n".format(str(nvars),str(len(encoding))))
        for u in encoding:
            p = [str(h) for h in u]            
            outfile.write(" ".join(p)+" 0\n")
            

# viable cardenc values:
#seqcounter  = 1
#sortnetwrk  = 2
#cardnetwrk  = 3
#totalizer   = 6
#mtotalizer  = 7
#kmtotalizer = 8
viable_sizes = [[9,191]]
for dimension,size in viable_sizes:
    generate_snake_in_the_box_plain_CNF(dimension,size,"snake_in_the_box_plain_{}_{}.cnf".format(str(dimension),str(size)))
    generate_snake_in_the_box_card_CNF(dimension, size,1,"snake_in_the_box_sq_{}_{}.cnf".format(str(dimension),str(size)))
    generate_snake_in_the_box_card_CNF(dimension, size,2,"snake_in_the_box_sn_{}_{}.cnf".format(str(dimension),str(size)))
    generate_snake_in_the_box_card_CNF(dimension, size,3,"snake_in_the_box_cn_{}_{}.cnf".format(str(dimension),str(size)))
    generate_snake_in_the_box_card_CNF(dimension, size,6,"snake_in_the_box_to_{}_{}.cnf".format(str(dimension),str(size)))
    generate_snake_in_the_box_card_CNF(dimension, size,7,"snake_in_the_box_mt_{}_{}.cnf".format(str(dimension),str(size)))
    generate_snake_in_the_box_card_CNF(dimension, size,8,"snake_in_the_box_kmt_{}_{}.cnf".format(str(dimension),str(size)))
















