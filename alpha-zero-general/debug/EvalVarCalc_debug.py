from pysat.solvers import Solver
from pysat.formula import CNF
import operator

class Node():

    def __init__(self, prior_actions=None) -> None:
        if prior_actions is None:
            prior_actions = []
        self.prior_actions = prior_actions # list of literals
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
        return Node(self.prior_actions+[var])

    def valid_cubing_lits(self, literals_all): 
        negated_prior_actions = [-l for l in self.prior_actions]
        return list(set(literals_all) - set(self.prior_actions) - set(negated_prior_actions))


class MarchPysatPropagate():

    def __init__(self, cnf, m) -> None:
        self.cnf = cnf
        self.nv = self.cnf.nv
        self.solver = Solver(name="minisat22", bootstrap_with=self.cnf)
        self.m = m # only top m variables to be considered for cubing

        if self.m is None: 
            self.m = self.cnf.nv
        print(f"{m} variables will be considered for cubing")

        literals_pos = list(range(1, self.m+1))
        literals_neg = [-l for l in literals_pos]
        self.literals_all = literals_pos + literals_neg

        self.node_count = 0

    def propagate(self, node):

        out1 = self.solver.propagate(assumptions=node.prior_actions)
        # log assumptions in a file
        with open("debug_log_assumptions.txt", "a") as f:
            f.write(f"{node.prior_actions}\n")
        assert out1 is not None
        not_unsat1, asgn1 = out1
        len_asgn_edge_vars = len(set(asgn1).intersection(set(self.literals_all))) # number of assigned edge variables

        # check for refutation
        if not not_unsat1:
            node.refuted = True
            node.reward = 1.0 # max reward
            return 0, len_asgn_edge_vars, {k: 0 for k in range(1, self.m+1)} # pass an empty dict
        else:
            node.refuted = False

        #TODO: what if the result is SAT?
        
        all_lit_rew = {}
        all_var_rew = {}
        valid_cubing_lits = node.valid_cubing_lits(self.literals_all)

        for literal in valid_cubing_lits:
            assert literal not in node.prior_actions, "Duplicate literals in the list"
            out = self.solver.propagate(assumptions=node.prior_actions+[literal])
            # log assumptions in a file
            with open("debug_log_assumptions.txt", "a") as f:
                f.write(f"{node.prior_actions+[literal]}\n")
            assert out is not None
            not_unsat2, asgn = out
            all_lit_rew[literal] = len(set(asgn).intersection(set(self.literals_all))) # number of assigned edge variables
            # if not not_unsat2:
            #     print("interim UNSAT for ", node.prior_actions+[literal])

        # combine the rewards of the positive and negative literals
        for literal in valid_cubing_lits:
            if literal > 0:
                all_var_rew[literal] = (all_lit_rew[literal] * all_lit_rew[-literal]) + all_lit_rew[literal] + all_lit_rew[-literal]

        # get the key (var) of the best value (eval_var)
        next_best_var = max(all_var_rew.items(), key=operator.itemgetter(1))[0]
        
        # top 3 all_var_rew
        top3_all_var_rew = sorted(all_var_rew.items(), key=operator.itemgetter(1), reverse=True)[:3]
        # keys of top3_all_var_rew
        top3_all_var_rew_keys = [k for k, v in top3_all_var_rew]

        # check if in debug_log.txt there is the same node.prior_actions and it has the same top3_all_var_rew_keys
        with open("debug_log.txt", "r") as f:
            for line in f:
                if line.startswith(str(node.prior_actions)):
                    if str(top3_all_var_rew_keys) not in line:
                        # write the current line to debug_log_error.txt
                        with open("debug_log_error.txt", "a") as f2:
                            f2.write(f"Not found in debug_log.txt: {node.prior_actions}, {top3_all_var_rew_keys}")
                            f2.write(f"Current line is: {line}")

        # log node.prior_actions, top 3 all_var_rew and len_asgn_edge_vars to a file
        with open("debug_log.txt", "a") as f:
            f.write(f"{node.prior_actions}, {top3_all_var_rew_keys}, {len_asgn_edge_vars}\n")

        return 1, len_asgn_edge_vars, all_var_rew