#!/bin/bash -i
source activate thesis_experiments
python drat_processor/drat_processor.py /mnt/tank/scratch/aandreev/snake_in_the_box_sq_9_191_drat.txt /nfs/home/aandreev/kissat/snake_in_the_box_sq_9_191.cnf /mnt/tank/scratch/aandreev/snake_in_the_box_sq_9_191_with_learnts.cnf 10

