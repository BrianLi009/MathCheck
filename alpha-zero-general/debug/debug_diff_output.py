import copy
import argparse
import itertools
import operator
import os
import pickle
from pysat.solvers import Solver
from pysat.formula import CNF
import time
from tqdm import tqdm
import random

random.seed(42)

filename="constraints_20_c_100000_2_2_0_final.simp"
m=190
solver_name="minisat22"
filename = filename
cnf = CNF(from_file=filename)
solver = Solver(name=solver_name, bootstrap_with=cnf)
prior_actions=[-79, 92, -31, 111, -57, 15]
all_eval_vars_40 = []

# get list of cnfs from solver
# print("No. of clauses before propagation: ", solver.nof_clauses())

# deep copy cnf.clauses
old_clauses = copy.deepcopy(cnf.clauses)

# read list of assumptions from file and convert to list of integers
# with open("debug_log_assumptions.txt", "r") as f:
#     list_of_assumptions = f.readlines()

literals_pos = list(range(1, m+1))
literals_neg = [-l for l in literals_pos]
literals_all = literals_pos + literals_neg
negated_prior_actions = [-l for l in prior_actions]
valid_cubing_lits = list(set(literals_all) - set(prior_actions) - set(negated_prior_actions))

# print("BEFORE:")
for _ in tqdm(range(1000)):
    all_lit_rew = {}
    all_var_rew = {}

    # print(solver.propagate(assumptions=prior_actions+[40]))
    # print(solver.propagate(assumptions=prior_actions+[-40]))

    for literal in valid_cubing_lits:
        assert literal not in prior_actions, "Duplicate literals in the list"
        out = solver.propagate(assumptions=prior_actions+[literal])
        assert out is not None
        _, asgn = out
        all_lit_rew[literal] = len(set(asgn).intersection(set(literals_all)))
        # print(prior_actions+[literal], ": ", asgn)
        # print([True for l in prior_actions+[literal] if l in asgn])

    # combine the rewards of the positive and negative literals
    for literal in valid_cubing_lits:
        if literal > 0:
            all_var_rew[literal] = (all_lit_rew[literal] * all_lit_rew[-literal]) + all_lit_rew[literal] + all_lit_rew[-literal]

    sorted_march_items = sorted(all_var_rew.items(), key=lambda x:x[1], reverse=True)
    all_eval_vars_40.append(dict(sorted_march_items)[40])

print(len(all_eval_vars_40), sum(all_eval_vars_40)/len(all_eval_vars_40))

# for assumptions in tqdm(list_of_assumptions):
#     assumptions = eval(assumptions)
#     solver.propagate(assumptions=assumptions)

# print("AFTER:")
# all_lit_rew = {}
# all_var_rew = {}

# # print(solver.propagate(assumptions=prior_actions+[40]))
# # print(solver.propagate(assumptions=prior_actions+[-40]))

# for literal in valid_cubing_lits:
#     assert literal not in prior_actions, "Duplicate literals in the list"
#     out = solver.propagate(assumptions=prior_actions+[literal])
#     assert out is not None
#     _, asgn = out
#     all_lit_rew[literal] = len(set(asgn).intersection(set(literals_all)))
#     # print(prior_actions+[literal], ": ", asgn)
#     # print([True for l in prior_actions+[literal] if l in asgn])

# # combine the rewards of the positive and negative literals
# for literal in valid_cubing_lits:
#     if literal > 0:
#         all_var_rew[literal] = (all_lit_rew[literal] * all_lit_rew[-literal]) + all_lit_rew[literal] + all_lit_rew[-literal]

# sorted_march_items = sorted(all_var_rew.items(), key=lambda x:x[1], reverse=True)
# print(dict(sorted_march_items[:5]))

# print("No. of clauses before propagation: ", len(old_clauses))
# print("No. of clauses after propagation: ", len(cnf.clauses))
# print("No. of clauses after propagation: ", solver.nof_clauses())
# print("CNF clauses are same after propagation: ", cnf.clauses == old_clauses)
# assert cnf.clauses == old_clauses