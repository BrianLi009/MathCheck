import copy
import argparse
import itertools
import operator
import os
import pickle
from pysat.solvers import Solver
from pysat.formula import CNF
import time

class Node():

    def __init__(self, prior_actions=None, unsat_learnt_actions=None) -> None:
        if prior_actions is None: # https://docs.python.org/3/reference/compound_stmts.html#function-definitions
            prior_actions = []
        if unsat_learnt_actions is None:
            unsat_learnt_actions = []
        self.prior_actions = prior_actions # list of literals
        self.unsat_learnt_actions = unsat_learnt_actions # list of literals whose negation leads to UNSAT in the next step
        self.reward = None # only for terminal nodes
        # self.best_var_rew = 0 # found via propagation on the parent node, the best variable has been added to prior_actions

        # found after propagating on the current node
        self.cutoff = False
        self.refuted = False
        self.next_best_var = None 
        # self.next_best_var_rew = None
        # self.all_var_rew = None

    def is_terminal(self):
        assert self.cutoff is not None and self.refuted is not None
        return self.cutoff or self.refuted
    
    def is_refuted(self):
        assert self.refuted is not None
        return self.refuted

    def get_next_best_var(self):
        return self.next_best_var

    def get_next_node(self, var):
        return Node(self.prior_actions+[var], self.unsat_learnt_actions[:])

    def valid_cubing_lits(self, literals_all): 
        negated_prior_actions = [-l for l in self.prior_actions]
        negated_unsat_learnt_actions = [-l for l in self.unsat_learnt_actions]
        return list(set(literals_all) - set(self.prior_actions) - set(negated_prior_actions) - set(self.unsat_learnt_actions) - set(negated_unsat_learnt_actions))


class AmsNoMCTS():

    def __init__(self, filename="constraints_20_c_100000_2_2_0_final.simp", solver_name="minisat22", recomp=-1, all_cubes=0, n=None, d=None, m=None, o=None) -> None:
        self.filename = filename
        self.cnf = CNF(from_file=self.filename)
        self.nv = self.cnf.nv
        self.solver = Solver(name=solver_name, bootstrap_with=self.cnf)
        self.all_cubes = all_cubes
        self.recomputation_limit = recomp # recomputation limit
        if self.recomputation_limit == -1: 
            self.recomputation_limit = self.nv # upper bound on the number of recomputations
        self.n = n # cutoff when n variables are eliminated
        self.d = d # cutoff when d depth is reached
        self.m = m # only top m variables to be considered for cubing
        self.o = o # output file for cubes

        if self.o is None: 
            print("Will be saving to default file: out.cubes")
            self.o = "out.cubes"
        
        assert self.n is not None or self.d is not None, "Please specify at least one of -n or -d"

        if self.m is None: 
            self.m = self.cnf.nv
        print(f"{m} variables will be considered for cubing")

        literals_pos = list(range(1, self.m+1))
        literals_neg = [-l for l in literals_pos]
        self.literals_all = literals_pos + literals_neg

        self.node_count = 0

    def DFSUtil(self, node: Node, level: int, all_cubes):

        self.node_count += 1

        if node.is_terminal(): 
            # print("Leaf: ", node.prior_actions, "len: ", len(node.prior_actions), "not node.is_refuted(): ", not node.is_refuted())
            if self.all_cubes:
                all_cubes.append(node.prior_actions)
            else:
                if not node.is_refuted(): # if UNSAT, skip cube
                    all_cubes.append(node.prior_actions)
            return node.reward
        
        reward_now = 0
            
        # Non-terminal nodes
        var = node.get_next_best_var()
        node_left = node.get_next_node(var)
        node_right = node.get_next_node(-var)

        self.propagate(node_left)
        self.propagate(node_right)

        for neighbour_node in (node_left, node_right): 
            reward_now += self.DFSUtil(neighbour_node, level+1, all_cubes)
        reward_now = reward_now/2 # average reward of the two children
        
        return reward_now # return the reward to the parent

    def propagate(self, node):

        out1 = self.solver.propagate(assumptions=node.prior_actions+node.unsat_learnt_actions)
        assert out1 is not None
        not_unsat1, asgn1 = out1
        len_asgn_edge_vars = len(set(asgn1).intersection(set(self.literals_all))) # number of assigned edge variables

        # print(f"Node: {node.prior_actions} with {len_asgn_edge_vars} assigned edge variables and {len(set(asgn1+node.prior_actions+node.unsat_learnt_actions).intersection(set(self.literals_all)))} all assigned vars") #; node.prior_actions+node.unsat_learnt_actions = {node.prior_actions+node.unsat_learnt_actions}; out1 = {out1}")
        # check for cutoff
        if (self.n is not None and len_asgn_edge_vars >= self.n) or (self.d is not None and len(node.prior_actions) >= self.d):
            node.cutoff = True
            node.reward = len(asgn1)/self.nv # reward is the fraction of assigned variables
            return
        else:
            node.cutoff = False

        # check for refutation
        if not not_unsat1:
            node.refuted = True
            node.reward = 1.0 # max reward
            return
        else:
            node.refuted = False

        recomputation_counter = 0
        
        while True:
            unsat_flag = False
            all_lit_rew = {}
            all_var_rew = {}
            valid_cubing_lits = node.valid_cubing_lits(self.literals_all)

            for literal in valid_cubing_lits:
                assert literal not in node.prior_actions+node.unsat_learnt_actions, "Duplicate literals in the list"
                out = self.solver.propagate(assumptions=node.prior_actions+node.unsat_learnt_actions+[literal])
                assert out is not None
                not_unsat2, asgn = out
                if not not_unsat2 and recomputation_counter < self.recomputation_limit: # recompute if unsat and recomputation limit not reached
                    unsat_literal = literal
                    node.unsat_learnt_actions.append(-unsat_literal) # add the negation of the unsat literal to the learnt actions
                    unsat_flag = True
                    recomputation_counter += 1
                    break

                all_lit_rew[literal] = len(set(asgn).intersection(set(self.literals_all)))

            if not unsat_flag: # no refutation found
                break
        
        if len(all_lit_rew) == 0:
            node.cutoff = True
            node.reward = 1.0 # no valid cubing literals found, so reward is max
            # print(f"Node: {node.prior_actions} - no valid cubing literals found, so reward is max")
            return

        # combine the rewards of the positive and negative literals
        for literal in valid_cubing_lits:
            if literal > 0:
                all_var_rew[literal] = (all_lit_rew[literal] * all_lit_rew[-literal]) + all_lit_rew[literal] + all_lit_rew[-literal]

        # get the key (var) of the best value (eval_var)
        node.next_best_var = max(all_var_rew.items(), key=operator.itemgetter(1))[0]
        return

        # node.next_best_var_rew = all_var_rew[node.next_best_var]
        # node.all_var_rew = all_var_rew

    def run_cnc(self):
        start_time = time.time()
        all_cubes = []
        node = Node()
        self.propagate(node)

        self.leaf_counter = 0
        r = self.DFSUtil(node=node, level=1, all_cubes=all_cubes)
        print("Reward: ", r)

        arena_cubes = [list(map(str, l)) for l in all_cubes]
        if os.path.exists(self.o):
            print(f"{self.o} already exists. Replacing old file!")
        f = open(self.o, "w")
        f.writelines(["a " + " ".join(l) + " 0\n" for l in arena_cubes])
        f.close()

        print("Saved cubes to file ", self.o)
        print("Time taken for cubing: ", round(time.time() - start_time, 3))
        print("Number of nodes: ", self.node_count)

# python ams_no_mcts.py "constraints_19_c_100000_2_2_0_final.simp" -d 1 -m 171 -o "e4_19_debug.cubes"
if __name__ == "__main__":
    st = time.time()

    # ams_no_mcts = AmsNoMCTS(filename="constraints_18_c_100000_2_2_0_final.simp", n=80, m=153)
    # ams_no_mcts.run_cnc()

    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="filename of the CNF file", type=str)
    parser.add_argument("-solver_name", help="solver name", default="minisat22")
    parser.add_argument("-recomp", help="recomputation_limit", type=int, default=-1)
    parser.add_argument("-all_cubes", help="get all cubes?", type=int, default=1)
    parser.add_argument("-n", help="cutoff when n variables are eliminated", type=int)
    parser.add_argument("-d", help="cutoff when d depth is reached", type=int)
    parser.add_argument("-m", help="only top m variables to be considered for cubing", type=int)
    parser.add_argument("-o", help="output file for cubes", default="out.cubes")
    args = parser.parse_args()

    print(args)

    ams_no_mcts = AmsNoMCTS(filename=args.filename, solver_name=args.solver_name, recomp=args.recomp, all_cubes=args.all_cubes, n=args.n, d=args.d, m=args.m, o=args.o)
    ams_no_mcts.run_cnc()

    print("Tool runtime: ", round(time.time() - st, 3))

# Notes:
# Keeping all_cubes at 1, so all unsat nodes are intact
# Keeping recomputation_limit at -1
# Pysat includes prior actions while metric calc
# Metric is 0 for those literals which lead to unsat
# UNSAT rew = 1 (during rew calc, not mcts search process)

