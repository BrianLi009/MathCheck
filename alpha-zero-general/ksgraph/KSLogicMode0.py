import copy
import itertools
import logging
import operator
import re
import subprocess
from abc import abstractmethod
from dataclasses import dataclass

import numpy as np
from pysat.solvers import Solver
from pysat.formula import CNF

import wandb

from .KSLogic import Board

from .EvalVarCalc import Node, MarchPysatPropagate

log = logging.getLogger(__name__)
cnf_obj = None
pysat_propagate_obj = None

class BoardMode0(Board):

    def __init__(self, args, cnf, max_metric_val, pysat_propagate):
        Board.__init__(self, args, cnf, pysat_propagate)
        self.max_literals = args.MAX_LITERALS
        self.valid_literals = None
        self.prob = None
        self.march_pos_lit_score_dict = None
        self.len_asgn_edge_vars = None
        self.ranked_keys = None
        self.top_five_kv_sorted = None
        self.rank_from_parent = 0
        self.ranks_till_now = []
        self.var_elim_till_now = []

        self.max_metric_val = max_metric_val # maximum possible value of the metric (unweighted)
        if args.verbose: print("Maximum metric value: ", self.max_metric_val)

        global pysat_propagate_obj
        pysat_propagate_obj = pysat_propagate

        global cnf_obj
        cnf_obj = cnf

    def __str__(self):
        return f"Board- rank_from_parent: {self.rank_from_parent}, res: {self.res}, step: {self.step}, vars_elim: {self.len_asgn_edge_vars}, total_rew: {self.total_rew:.3f}, prior_actions: {self.prior_actions}, ranked_keys: {self.ranked_keys}, top_five_kv_sorted: {self.top_five_kv_sorted}"

    def is_giveup(self): # give up if we have reached the upper bound on the number of steps or if there are only 0 or extra lits left
        return self.res is None and ((self.args.VARS_TO_ELIM is not None and self.len_asgn_edge_vars >= self.args.VARS_TO_ELIM) or (self.args.STEP_UPPER_BOUND is not None and self.step >= self.args.STEP_UPPER_BOUND) or len(self.get_legal_literals()) == 0)

    def calculate_march_metrics(self):
        if self.args.debugging: log.info(f"Calculating march metrics")
        edge_vars = self.max_literals
        assert pysat_propagate_obj is not None
        prior_actions_flat = list(itertools.chain.from_iterable(self.prior_actions))
        res, len_asgn_edge_vars, march_pos_lit_score_dict_all = pysat_propagate_obj.propagate(Node(prior_actions_flat))
        # print(res, march_pos_lit_score_dict)

        if res == 0: # refuted node
            self.res = 0 
            # len_asgn_edge_vars with be None

        self.len_asgn_edge_vars = len_asgn_edge_vars

        sorted_march_items = sorted(march_pos_lit_score_dict_all.items(), key=lambda x:x[1], reverse=True)
        self.top_five_kv_sorted = dict(sorted_march_items[:5])
        if self.args.LIMIT_TOP_3:
            march_pos_lit_score_dict = dict(sorted_march_items[:3])
        else: # required for CubeArena
            march_pos_lit_score_dict = dict(sorted_march_items)

        valid_pos_literals = list(march_pos_lit_score_dict.keys())
        valid_neg_literals = [-l for l in valid_pos_literals]

        prob = [0.0 for _ in range(edge_vars*2+1)]
        for l in valid_pos_literals:
            prob[l] = march_pos_lit_score_dict[l]
            prob[self.lit2var[-l]] = march_pos_lit_score_dict[l]
        
        if sum(prob) == 0:
            # uniform distribution
            prob = [1/(edge_vars*2) for _ in range(edge_vars*2+1)]
            prob[0] = 0.0 # 0 is not a valid literal
        else:
            prob = [p/sum(prob) for p in prob] # only for +ve literals

        # normalize the values of the march_pos_lit_score_dict
        for k in march_pos_lit_score_dict.keys():
            march_pos_lit_score_dict[k] /= self.max_metric_val

        # normalize the values of the march_pos_lit_score_dict_all
        for k in march_pos_lit_score_dict_all.keys():
            march_pos_lit_score_dict_all[k] /= self.max_metric_val
        
        max_val = max(march_pos_lit_score_dict.values()) if len(march_pos_lit_score_dict) > 0 else 0
        wandb.log({"depth": self.step, "max_val": max_val})
        # also log in a separate file
        # with open("max_val.txt", "a") as f:
        #     f.write(f"{self.step} {max_val}\n")

        self.valid_literals = valid_pos_literals + valid_neg_literals # both +ve and -ve literals
        self.prob = prob
        self.march_pos_lit_score_dict = march_pos_lit_score_dict
        self.march_pos_lit_score_dict_all = march_pos_lit_score_dict_all
        sorted_items = sorted(march_pos_lit_score_dict.items(), key=lambda x:x[1], reverse=True)
        self.ranked_keys = [k for k,v in sorted_items]
    
    def get_legal_literals(self):
        assert self.valid_literals is not None
        return set(self.valid_literals)
        
    def execute_move(self, action):
        assert self.is_done() == False
        # if action not in [self.lit2var[l] for l in self.get_legal_literals()]:
        #     print("Illegal move!")
        if self.args.debugging: log.info(f"Executing action {action}")
        new_state = copy.deepcopy(self)
        if self.args.debugging: log.info(f"Deepcopy done")
        new_state.valid_literals = None
        new_state.prob = None
        new_state.march_pos_lit_score_dict = None
        new_state.ranked_keys = None
        new_state.len_asgn_edge_vars = None
        new_state.top_five_kv_sorted = None
        new_state.rank_from_parent = 0

        new_state.step += 1
        chosen_literal = [new_state.var2lit[action]]
        new_state.prior_actions.append(chosen_literal)
        # new_state.cnf.append(chosen_literal) # append to the cnf object
        # collecting from the parent node's dict; TODO: not considering direction, so choosing the +ve one (abs)
        assert self.march_pos_lit_score_dict is not None
        try:
            current_metric_val = self.march_pos_lit_score_dict[abs(chosen_literal[0])]
            new_state.rank_from_parent = self.ranked_keys.index(abs(chosen_literal[0])) + 1
            new_state.ranks_till_now.append(new_state.rank_from_parent)
        except KeyError:
            current_metric_val = self.march_pos_lit_score_dict_all[abs(chosen_literal[0])]
        # reward is the propagation rate
        new_state.total_rew = current_metric_val # step is divided during the metric calculation
        # proportional to the number of literals that are assigned (eval_var), inversely proportional to the number of steps
        new_state.calculate_march_metrics()
        new_state.var_elim_till_now.append(new_state.len_asgn_edge_vars)
        if self.args.debugging: log.info(f"Calculated march metrics")
        return new_state

    def compute_reward(self, eval_cls=False):
        norm_rew = None
        if self.is_done():
            if self.is_win():
                print("Found SAT!")
                print(self.prior_actions)
                print("Exiting...")
                exit(0)
                # return self.total_rew + self.args.STEP_UPPER_BOUND
            elif self.is_fail(): 
                norm_rew = 0.1 # setting it to a non-zero positive val to avoid best values to be 0, as 0 is also for the illegal moves
            elif self.is_unknown(): # results in unknown using march_cu so heavily penalize and don't go down this path
                norm_rew = -1
            elif self.is_giveup(): 
                norm_rew = self.total_rew # if any changes are made here, make sure to change the reward in MCTS.py as well
            else:
                raise Exception("Unknown game state")
            
            if eval_cls:
                if norm_rew > 0:
                    return norm_rew * self.max_metric_val
                else:
                    return norm_rew
            else:
                wandb.log({"depth": self.step, "norm_rew": norm_rew})
                return norm_rew
        else:
            return None

    @DeprecationWarning
    def eval_var(self): # slow
        march_pos_lit_score_dict = {}
        
        for chosen_literal in list(set(self.get_flattened_clause()) - set([0]+self.extra_lits)):
            print(chosen_literal)
            chosen_literal = int(chosen_literal)
            if abs(chosen_literal) in march_pos_lit_score_dict:
                continue

            with Solver(bootstrap_with=self.cnf()) as solver:
                out = solver.propagate(assumptions=[chosen_literal])
                assert out is not None
                not_unsat, asgn = out

                if not not_unsat: # unsat
                    rew1 = 0
                else:
                    rew1 = len(asgn)

                out = solver.propagate(assumptions=[-chosen_literal])
                assert out is not None
                not_unsat, asgn = out

                if not not_unsat: # unsat
                    rew2 = 0
                else:
                    rew2 = len(asgn)

                if not (rew1 == 0 and rew2 == 0):
                    # one of them is not unsat
                    march_pos_lit_score_dict[abs(chosen_literal)] = rew1 + rew2