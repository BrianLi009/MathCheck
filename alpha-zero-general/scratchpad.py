# # import hashlib

# # def calculate_hash(string):
# #     sha256_hash = hashlib.sha256()
# #     sha256_hash.update(string.encode('utf-8'))
# #     return sha256_hash.hexdigest()

# # string = "Hello, world!"
# # hash_value = calculate_hash(string)
# # print(hash_value)

# import re
# output = """
# c maximum variable to appear in cubes is 6
# c cubes are emitted to x.cubes
# c the DIMACS p-line indicates a CNF of 6 variables and 5 clauses.
# c init_lookahead: longest clause has size 2
# c number of free entry variables = 2
# c number of free variables = 2
# c highest active variable  = 4
# c |----------------------------------------------------------------|
# alphasat: variable: 4, w-left: 0.000000, w-right: 0.000000
# variable: 4, left: 0.000000, right: 0.000000
# variable 4 with score 0.000000
# alphasat: variable: 3, w-left: 0.000000, w-right: 0.000000
# variable: 3, left: 0.000000, right: 0.000000
# variable 3 with score 0.000000
# selected 4 at 1 with diff 0.000000
# c |****************************************************************
# c
# """

# re_out = re.findall(r"alphasat: variable: (\d+), w-left: (\d+.\d+), w-right: (\d+.\d+)", output)
# re_dict = {int(k):(float(v)+float(w)) for k,v,w in re_out}
# print(re_dict)

# import operator
# print(max(re_dict.items(), key=operator.itemgetter(1))[1])

# print(re.findall(r"selected (-?\d+) at \d+ with diff (\d+)", output))

# # o1 = """
# # c
# # c main():: nodeCount: 0
# # c main():: dead ends in main: 0
# # c main():: lookAheadCount: 98
# # c main():: unitResolveCount: 0
# # c time = 1.14 seconds
# # c main():: necessary_assignments: 68
# # c number of cubes 1, including 1 refuted leaf
# # """

# # print("c number of cubes 1, including 1 refuted leaf" in o1)

# import pysat
# import random
# import time

# from pysat.formula import CNF
# from pysat.solvers import Solver

# formula = CNF()
# formula.append([1, 2, 3])
# formula.append([-1, 2, 3])
# formula.append([-4, 2, 3])
# formula.append([-5, 2, 3])
# formula.append([-6, 2, -3])

# solver = Solver(bootstrap_with=formula)
# print(solver.propagate(assumptions=[-5]))

# import time
# import numpy as np
# import matplotlib.pyplot as plt
# import numpy as np
# import wandb

# wandb.init(reinit=True, 
#         name="try",
#         project="AlphaSAT", 
#         settings=wandb.Settings(start_method='thread'), 
#         save_code=True)


# for i in range(10):
#     random_values = np.random.randn(100)
#     random_ints = np.random.randint(10, size=100)

#     data = [[x, y, z, w] for (x, y, z, w) in zip(random_ints, random_values, random_values, random_values)]

#     table = wandb.Table(data=data, columns = ["level", "Qsa", "best_u", "v"])
#     wandb.log({"MCTS Qsa vs tree depth" : wandb.plot.scatter(table,
#                             "level", "Qsa")})
#     wandb.log({"MCTS best_u vs tree depth" : wandb.plot.scatter(table,
#                             "level", "best_u")})
#     wandb.log({"MCTS value vs tree depth" : wandb.plot.scatter(table,
#                             "level", "v")})
    
#     time.sleep(15)


# for i in random_ints:
#     wandb.log({"random_int": i})

# plt.plot([1, 2, 3, 4])
# plt.ylabel("some interesting numbers")
# wandb.log({"chart": plt})

# # Creating dataset
# np.random.seed(10)
# data = np.random.normal(100, 20, 200)
 
# fig = plt.figure(figsize =(10, 7))
# plt.boxplot(data)
# plt.savefig("boxplot.png")
# wandb.log({"example": wandb.Image("boxplot.png")})

# data = [[x, y] for (x, y) in zip(random_ints, random_values)]
# table = wandb.Table(data=data, columns = ["solver_reward (NA)", "eval_var (NA)"])
# wandb.log({'Solver rewards (Arena)': wandb.plot.histogram(table, "solver_reward (NA)",
#                         title="Histogram")})


# from march_pysat import MarchPysat, Node

# march_pysat = MarchPysat(filename="constraints_17_c_100000_2_2_0_final.simp", m=136)
# march_pysat.run_cnc()

import copy
import argparse
import itertools
import operator
import os
import pickle
from pysat.solvers import Solver
from pysat.formula import CNF
import time

prior_actions=[-67, 106, -111, 68, -79, 125, 31, -60]

filename="constraints_20_c_100000_2_2_0_final.simp"
m=190
solver_name="minisat22"
filename = filename
cnf = CNF(from_file=filename)
solver = Solver(name=solver_name, bootstrap_with=cnf)

literals_pos = list(range(1, m+1))
literals_neg = [-l for l in literals_pos]
literals_all = literals_pos + literals_neg
negated_prior_actions = [-l for l in prior_actions]
valid_cubing_lits = list(set(literals_all) - set(prior_actions) - set(negated_prior_actions))

all_lit_rew = {}
all_var_rew = {}

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

print(all_var_rew)
sorted_march_items = sorted(all_var_rew.items(), key=lambda x:x[1], reverse=True)
print(dict(sorted_march_items[:5]))

# create a 3D scatter plot of this formula x * y + x + y

# def f(x, y):
#     return x * y + x + y

# import matplotlib.pyplot as plt
# import numpy as np

# x = np.linspace(-10, 10, 100)
# y = np.linspace(-10, 10, 100)

# X, Y = np.meshgrid(x, y)
# Z = f(X, Y)

# fig = plt.figure()
# ax = plt.axes(projection='3d')
# ax.contour3D(X, Y, Z, 50, cmap='binary')
# ax.set_xlabel('x')
# ax.set_ylabel('y')
# ax.set_zlabel('z')
# plt.show()

# import numpy as np

# # Create a range of variances for x and y
# variances_x = np.linspace(1, 5, 100)
# variances_y = np.linspace(1, 5, 100)

# # Initialize arrays to store the results
# z_values = []

# # Generate datasets with varying variances and calculate z
# for var_x, var_y in zip(variances_x, variances_y):
#     x = var_x
#     y = var_y
#     z = x * y + x + y
#     z_values.append(z)

# # Plot the relationship between variances and z values
# import matplotlib.pyplot as plt

# plt.plot(variances_x, z_values, label="Variance of x vs. Mean of z")
# plt.xlabel("Variance of x")
# plt.ylabel("Mean of z")
# plt.legend()
# plt.show()

# import numpy as np
# import matplotlib.pyplot as plt

# # Create lists of x and y values
# x = list(range(1, 101))
# y = list(range(1, 101))

# # Initialize lists to store variances and z values
# variances = []
# z_values = []

# # Calculate variances and z values for all combinations of x and y
# for x_val in x:
#     for y_val in y:
#         var_x = np.var([x_val, y_val])
#         z_val = x_val * y_val + x_val + y_val
#         variances.append(var_x)
#         z_values.append(z_val)

# # Create a scatter plot of variances vs. z values
# plt.scatter(variances, z_values, c=z_values, cmap='viridis')
# plt.xlabel('Variance of x and y')
# plt.ylabel('z Value')
# plt.title('Variance of x and y vs. z Value')
# plt.colorbar(label='z Value')
# plt.show()

# def func_mod(a, b, c):
#     a.append(1)
#     b.append(2)
#     c.append(3)
#     print(a, b, c)

# a = [1,2,3]
# b = [4,5,6]
# c = [7,8,9]

# func_mod(a, b+[0], c[:])
# print(a, b, c)