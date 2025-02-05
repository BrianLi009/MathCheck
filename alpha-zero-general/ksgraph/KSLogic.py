import copy
import itertools
from abc import abstractmethod
from dataclasses import dataclass

import numpy as np
from pysat.solvers import Solver

import wandb

# global variable to avoid copying while creating copies of the board
cnf_obj = None
pysat_propagate_obj = None 

class Board:

    def __init__(self, args, cnf, pysat_propagate):
        self.args = args
        # self.cnf_clauses_org = copy.deepcopy(cnf.clauses)
        # self.cnf = copy.deepcopy(cnf)
        self.nlits = cnf.nv # number of variables in the CNF formula
        self.extra_lits = list(range(self.args.MAX_LITERALS+1, self.nlits+1, 1))+list(range(-self.args.MAX_LITERALS-1, -self.nlits-1, -1)) # extra lits not part of the action space

        self.arena_mode = 0 # 0: normal mode, 1: arena mode
        self.step = 0
        self.total_rew = 0
        self.sat_or_unsat_leaf = 0
        self.prior_actions = []
        self.sat_unsat_actions = set() # actions that lead to a sat or unsat leaf - to be removed from the legal action space
        self.res = None

        self.counter_sat = 0
        self.counter_unsat = 0
        self.counter_giveup = 0

        literals_pos = list(range(1,self.args.MAX_LITERALS+1))
        literals_neg = [-l for l in literals_pos]
        literals_all = literals_pos + literals_neg
        vars_all = [self.args.MAX_LITERALS + (-c) if c<0 else c for c in literals_all]
        self.lit2var = dict(zip(literals_all, vars_all))
        self.var2lit = dict(zip(vars_all, literals_all))

        global pysat_propagate_obj
        pysat_propagate_obj = pysat_propagate

        global cnf_obj
        cnf_obj = cnf

    def __str__(self):
        return f"Board: {self.get_flattened_clause()}, nlits: {self.nlits}, res: {self.res}, step: {self.step}, total_rew: {self.total_rew}, sat_or_unsat_leaf: {self.sat_or_unsat_leaf}, prior_actions: {self.prior_actions}, sat_unsat_actions: {self.sat_unsat_actions}"

    def is_giveup(self): # give up if we have reached the upper bound on the number of steps or if there are only 0 or extra lits left
        return self.res is None and (self.step >= self.args.STEP_UPPER_BOUND or len(self.get_legal_literals()) == 0)
    
    def is_unknown(self):
        return self.res == 2
    
    def is_win(self):
        return self.res == 1
    
    def is_fail(self):
        return self.res == 0

    def is_done(self):
        return self.is_giveup() or self.is_win() or self.is_fail() or self.is_unknown()
    
    def cnf(self):
        assert cnf_obj is not None
        if len(self.prior_actions) > 0:
            return cnf_obj.clauses + self.prior_actions
        else:
            return cnf_obj.clauses
    
    def get_and_reset_counters(self):
        counters = [self.counter_sat, self.counter_unsat, self.counter_giveup]
        self.counter_sat = 0
        self.counter_unsat = 0
        self.counter_giveup = 0
        return counters
    
    def get_complement_action(self, action): # action is a var
        action_lits = self.var2lit[action]
        action_lits_comp = -action_lits
        action_comp = self.lit2var[action_lits_comp]
        assert action_comp != action and action_comp > 0
        return action_comp # returned action is a var
        
    def get_state(self):
        prior_actions = list(itertools.chain.from_iterable(self.prior_actions)) # flatten the list
        prior_actions = [self.lit2var[i] for i in prior_actions] # treat the negative literals as a new literal (for convenient MCTS action space)
        # pre-padding to keep the last self.args.STATE_SIZE actions with the most recent one always at the end
        prior_actions_padded = [0]*(self.args.STATE_SIZE-len(prior_actions)) + prior_actions[-self.args.STATE_SIZE:] # pad the list with 0s
        return np.array(prior_actions_padded) # literals are mapped to vars
    
    def get_state_clause(self):
        clauses = copy.deepcopy(self.cnf())
        for i, c in enumerate(clauses):
            clauses[i].append(0) # add the clause separator
        
        clauses = list(itertools.chain.from_iterable(clauses)) # flatten the list
        clauses = [self.nlits + (-c) if c<0 else c for c in clauses] # treat the negative literals as a new literal (for convenient MCTS action space)
        clauses_padded = clauses[:self.args.STATE_SIZE] + [0]*(self.args.STATE_SIZE-len(clauses)) # pad the list with 0s
        return np.array(clauses_padded) # literals are mapped to vars

    def get_state_complete(self): # no truncation or padding
        clauses = copy.deepcopy(self.cnf())
        for i, c in enumerate(clauses):
            clauses[i].append(0) # add the clause separator
        
        clauses = list(itertools.chain.from_iterable(clauses)) # flatten the list
        clauses = [self.nlits + (-c) if c<0 else c for c in clauses] # treat the negative literals as a new literal (for convenient MCTS action space)
        return np.array(clauses) # literals are mapped to vars
    
    def get_flattened_clause(self): # no mapping or truncation or padding
        clauses = copy.deepcopy(self.cnf())
        for i, c in enumerate(clauses):
            clauses[i].append(0) # add the clause separator
        
        clauses = list(itertools.chain.from_iterable(clauses)) # flatten the list
        return np.array(clauses) # literals are not mapped to vars
    
    def get_legal_literals(self):
        return set(self.get_flattened_clause()) - set([0]+self.extra_lits) # remove the clause separator from the list of legal moves
        
    def execute_move(self, action):
        assert self.is_done() == False
        # if action not in [self.lit2var[l] for l in self.get_legal_literals()]:
        #     print("Illegal move!")
        new_state = copy.deepcopy(self)

        new_state.step += 1
        chosen_literal = [new_state.var2lit[action]]
        new_state.prior_actions.append(new_state.var2lit[action])
        
        with Solver(bootstrap_with=new_state.cnf()) as solver:
            out = solver.propagate(assumptions=chosen_literal)
            assert out is not None
            not_unsat, asgn = out
        
        new_state.total_rew += len(asgn) # reward is the number of literals that are assigned (eval_var)
        # wandb.log({"eval_var": len(asgn), "arena_mode": self.arena_mode})

        if not not_unsat: # unsat
            new_state.res = 0
            raise Exception("cnf member does not exist anymore!")
            new_state.cnf.clauses = [[]]
            new_state.sat_or_unsat_leaf += 1
            self.counter_unsat += 1
            self.sat_or_unsat_leaf += 1 # update the parent too, so that you can propagate to the cutoff leaf
            self.sat_unsat_actions.add(action) # add the action to the list of actions (of the parent) that lead to a sat or unsat leaf

        else:
            raise Exception("cnf member does not exist anymore!")
            clauses_interm = [c for c in new_state.cnf.clauses if all(r not in c for r in chosen_literal)] # remove the clauses that contain the chosen literal
            new_state.cnf.clauses = [[l for l in c if all(l!=-r for r in chosen_literal)] for c in clauses_interm] # remove the negation of chosen literal from the remaining clauses
            if new_state.cnf.clauses == []: # sat
                new_state.res = 1
                new_state.sat_or_unsat_leaf += 1
                self.counter_sat += 1
                self.sat_or_unsat_leaf += 1 # update the parent too, so that you can propagate to the cutoff leaf
                self.sat_unsat_actions.add(action) # add the action to the list of actions (of the parent) that lead to a sat or unsat leaf

        return new_state

    def compute_reward(self):
        if self.is_done():
            if self.is_win():
                return 1, self.prior_actions # positive reward, and the model is the list of actions that led to the win
            elif self.is_fail():
                return 1, None
            elif self.is_giveup(): # call the solver to get the result + also used by Arena
                self.counter_giveup += 1
                with Solver(bootstrap_with=self.cnf(), use_timer=True) as solver:
                    res = solver.solve(assumptions=self.prior_actions)
                    if res: 
                        solver_model = solver.get_model() # assumptions are included
                    else:
                        solver_model = None
                    time_s = solver.time()
                    wandb.log({"solver_time": time_s, "arena_mode": self.arena_mode, "eval_var": self.total_rew})
                    assert time_s is not None
                    return -time_s/10, solver_model # penalty is the time it takes to solve the problem (seconds / 10)
            else:
                raise Exception("Unknown game state")
        else:
            return None, None
