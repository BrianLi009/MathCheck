import logging
import math

import numpy as np
import psutil
import wandb
import random

EPS = 1e-8
random.seed(42)
np.random.seed(42)

log = logging.getLogger(__name__)

class MCTS():
    """
    This class handles the MCTS tree.
    """

    def __init__(self, nnet, args, all_logging_data, nn_iteration):
        # self.game = game.get_copy()
        self.nn_iteration = nn_iteration
        self.nnet = nnet
        self.args = args
        self.Qsa = {}  # stores Q values for s,a (as defined in the paper)
        self.Bsa = {}  # stores best values for s,a
        self.Nsa = {}  # stores #times edge s,a was visited
        self.Ns = {}  # stores #times board s was visited
        self.Ps = {}  # stores initial policy (returned by neural net)

        self.Es = {}  # stores game.getGameEnded ended for board s
        # self.Vs = {}  # stores game.getValidMoves for board s - dynamic because of sat_unsat_actions

        self.data = []
        self.all_logging_data = all_logging_data
        self.cache_data = {}

    def getActionProb(self, game, board, temp=0, verbose=False):
        """
        This function performs numMCTSSims simulations of MCTS starting from
        canonicalBoard.

        Returns:
            probs: a policy vector where the probability of the ith action is
                   proportional to Nsa[(s,a)]**(1./temp)
        """
        canonicalBoard = game.getCanonicalForm(board)

        if verbose:
            # Getting % usage of virtual_memory ( 3rd field)
            print('RAM memory % used:', psutil.virtual_memory()[2])
            # Getting usage of virtual_memory in GB ( 4th field)
            print('RAM Used (GB):', psutil.virtual_memory()[3]/1000000000)

        for _ in range(self.args.numMCTSSims):
            if self.args.debugging: log.info("MCTS Simulation #{}".format(_))
            self.search(game, canonicalBoard, verbose=verbose)

        s = game.stringRepresentation(canonicalBoard)
        counts = [self.Nsa[(s, a)] if (s, a) in self.Nsa else 0 for a in range(game.getActionSize())]
        maxvals = [self.Bsa[(s, a)] if (s, a) in self.Bsa else 0 for a in range(game.getActionSize())]
        qvals = [self.Qsa[(s, a)] if (s, a) in self.Qsa else 0 for a in range(game.getActionSize())]
        non_zero_elems = [(ind_,elem_c,elem_v,elem_q) for ind_, (elem_c,elem_v,elem_q) in enumerate(zip(counts,maxvals,qvals)) if elem_c != 0]
        if verbose:
            print("Non zero elements in counts: ", non_zero_elems)
        if len(non_zero_elems) == 2:
            log.warning("NO EXPLORATION!!!!")
        
        # open a file to write the counts
        if self.args.debugging:
            with open(f"cubing_outputs/{self.args.o}_counts.txt", "a") as f:
                f.write(f"{s}: {non_zero_elems}\n")

        if temp == 0: # Note that this part is different from the original code - we are using maxvals instead of counts
            bestAs = np.array(np.argwhere(maxvals == np.max(maxvals))).flatten()
            bestA = np.random.choice(bestAs)
            probs = [0] * len(maxvals)
            probs[bestA] = 1
            return probs

        # Note: This part is still the same as the original code - we are using counts instead of maxvals
        counts = [x ** (1. / temp) for x in counts]
        counts_sum = float(sum(counts))
        probs = [x / counts_sum for x in counts]

        # all_data = self.all_logging_data + self.data
        # if self.args.debugging: log.info(f"WANDB LOGGING: Size of self.data = {len(self.data)} and all data = {len(all_data)}")
        # table = wandb.Table(data=all_data, columns = ["level", "Qsa", "best_u", "v"])
        # wandb.log({"MCTS Qsa vs tree depth" : wandb.plot.scatter(table,
        #                             "level", "Qsa")})
        # wandb.log({"MCTS best_u vs tree depth" : wandb.plot.scatter(table,
        #                             "level", "best_u")})
        # wandb.log({"MCTS value vs tree depth" : wandb.plot.scatter(table,
        #                             "level", "v")})
        return probs

    def search(self, game, canonicalBoard, verbose=False, level=0):
        """
        This function performs one iteration of MCTS. It is recursively called
        till a leaf node is found. The action chosen at each node is one that
        has the maximum upper confidence bound as in the paper.

        Once a leaf node is found, the neural network is called to return an
        initial policy P and a value v for the state. This value is propagated
        up the search path. In case the leaf node is a terminal state, the
        outcome is propagated up the search path. The values of Ns, Nsa, Qsa are
        updated.

        NOTE: the return values are the negative of the value of the current
        state. This is done since v is in [-1,1] and if v is the value of a
        state for the current player, then its value is -v for the other player.

        Returns:
            v: the negative of the value of the current canonicalBoard
        """

        if self.args.debugging: log.info(f"MCTS Search at level {level}")
        s = game.stringRepresentation(canonicalBoard)
        if self.args.debugging: log.info(f"String representation done: {s} with reward {canonicalBoard.total_rew:.4f}")
        if self.args.debugging: log.info(canonicalBoard)

        if verbose:
            log.info(f"At level {level}\n{s}")

        if s not in self.Es: # STEP 2: EXPANSION
            if verbose:
                log.info(f"Node not yet seen\n{s}")
            self.Es[s] = game.getGameEndedMCTS(canonicalBoard) # separate for MCTS to avoid calling it end of game if the depth limit is reached, MCTS should keep exploring further
        
        # self.Es[s] = canonicalBoard.total_rew # we cannot do this because this is MCTS-dependent termination, not an actual terminating state

        if self.Es[s] != None: # STEP 4 (I): BACKPROPAGATION
            # terminal node
            if verbose:
                log.info(f"Node is terminal node, reward is {self.Es[s]}\n{s}")
            
            if self.args.debugging:
                with open(f"cubing_outputs/{self.args.o}_all_Bsa_scores.txt", "a") as f:
                    f.write(f"{s}: {self.Es[s]} ({canonicalBoard.var_elim_till_now}, {self.Es[s]*canonicalBoard.step*canonicalBoard.max_metric_val})\n")

            return self.Es[s]
        
        if sum(game.getValidMoves(canonicalBoard)) == 0: 
            raise NotImplementedError # TODO: is it possible to reach here?
            # terminal node when you are out of valid moves
            # rew = game.getGameEnded(canonicalBoard) # need to recompute reward - run Solver
            # if verbose:
            #     log.info(f"Node is terminal node, reward is {rew}\n{s}")
            # return rew

        if s not in self.Ps: # STEP 3: ROLLOUT or SIMULATION (for MCTSmode != 0, use NN to predcit the value, i.e., the end reward to be backpropagated)
            # leaf node
            if verbose:
                log.info(f"Node is leaf node, using NN to predict value for\n{s}")
            if self.args.MCTSmode == 0 or (self.args.MCTSmode != 0 and self.nn_iteration < self.args.nn_iter_threshold):
                if self.args.debugging:
                    log.info("Using heuristic tree search without NN")
                # Steps in MCTS: selection, expansion, simulation, backpropagation
                v = canonicalBoard.total_rew
                self.Ps[s] = canonicalBoard.prob
            else:
                self.Ps[s], v = self.nnet.predict(canonicalBoard.get_state())
            valids = game.getValidMoves(canonicalBoard)
            self.Ps[s] = self.Ps[s] * valids  # masking invalid moves
            sum_Ps_s = np.sum(self.Ps[s])
            assert abs(sum_Ps_s - sum(canonicalBoard.prob)) < 0.1, f"sum_Ps_s = {sum_Ps_s}, sum(canonicalBoard.prob) = {sum(canonicalBoard.prob)}"
            if sum_Ps_s > 0:
                self.Ps[s] /= sum_Ps_s  # renormalize
            else:
                # if all valid moves were masked make all valid moves equally probable

                # NB! All valid moves may be masked if either your NNet architecture is insufficient or you've get overfitting or something else.
                # If you have got dozens or hundreds of these messages you should pay attention to your NNet and/or training process.   
                log.error("All valid moves were masked, doing a workaround.")
                self.Ps[s] = self.Ps[s] + valids
                self.Ps[s] /= np.sum(self.Ps[s])

            self.Ns[s] = 0

            if self.args.debugging:
                with open(f"cubing_outputs/{self.args.o}_all_Bsa_scores.txt", "a") as f:
                    f.write(f"{s}: {v} ({canonicalBoard.var_elim_till_now}, {v*canonicalBoard.max_metric_val})\n")

            return v # STEP 4 (II): BACKPROPAGATION

        valids = game.getValidMoves(canonicalBoard)
        cur_best = -float('inf')
        best_act = -1
        all_u = {}

        # pick the action with the highest upper confidence bound
        for a in range(game.getActionSize()): # STEP 1: SELECTION
            if valids[a]:
                if (s, a) in self.Qsa:
                    u = self.Qsa[(s, a)] + self.args.cpuct * self.Ps[s][a] * math.sqrt(self.Ns[s]) / (
                            1 + self.Nsa[(s, a)])
                    if self.args.debugging: # and level == 0: 
                        print(f"a: {a}, u: {u:.6f}, self.Qsa[(s, a)]: {self.Qsa[(s, a)]:.4f}, self.Ps[s][a]: {self.Ps[s][a]:.4f}, factor: {math.sqrt(self.Ns[s]) / (1 + self.Nsa[(s, a)]):.6f}")
                    
                else:
                    # assert self.Ns[s] == 0, f"self.Ns[s] = {self.Ns[s]} for s = {s}, a = {a}, canonicalBoard = {canonicalBoard}"
                    u = self.args.cpuct * self.Ps[s][a] * math.sqrt(self.Ns[s] + EPS)  # Q = 0 ?
                    if self.args.debugging: # and level == 0: 
                        print(f"a: {a}, u: {u}, self.Ps[s][a]: {self.Ps[s][a]:.4f}, factor: {math.sqrt(self.Ns[s] + EPS)}")
                    if self.Ps[s][a] == 0:
                        print(f"DEBUG - a: {a}, valids[a]: {valids[a]}, Board: {canonicalBoard}")

                if u > cur_best:
                    cur_best = u
                    best_act = a

                all_u[a] = u

        if self.args.debugging: # and level == 0: 
            print("Canonical board march metrics:")
            sorted_march_items = sorted(canonicalBoard.march_pos_lit_score_dict.items(), key=lambda x:x[1], reverse=True)
            for k, v in sorted_march_items[:5]:
                print(f"{k}: {v}")
            print("Canonical board best u vals:")
            sorted_u_items = sorted(all_u.items(), key=lambda x:x[1], reverse=True)
            for k, v in sorted_u_items[:5]:
                print(f"{k}: {v}")

        a = best_act

        if self.args.debugging: # and level == 0: 
            log.info(f"Best action is {a} with self.Ps[s][a] = {self.Ps[s][a]:.3f}")
            print(f"max self.Ps[s] value {max(self.Ps[s]):.3f}, same self.Ps[s][a] count = {sum(self.Ps[s] == self.Ps[s][a])}")
            print(f"best self.Ps[s] vals = {[sorted(enumerate(self.Ps[s]), reverse=True, key=lambda x:x[1])[:6]]}")

        
        #TODO: see why this is needed - is it because of the recursion? creating a copy because the game is modified in-place?
        
        if (s, a) not in self.cache_data:
            game_copy_dir1 = game.get_copy()
            next_s_dir1 = game_copy_dir1.getNextState(canonicalBoard, a)

            comp_a = canonicalBoard.get_complement_action(a) # complement of the literal
            game_copy_dir2 = game.get_copy()
            next_s_dir2 = game_copy_dir2.getNextState(canonicalBoard, comp_a)

            if self.args.debugging:
                log.info("Cache new data")
            self.cache_data[(s, a)] = (next_s_dir1, canonicalBoard)
            self.cache_data[(s, comp_a)] = (next_s_dir2, canonicalBoard)
        else:
            if self.args.debugging:
                log.info("Using cached data")
            comp_a = canonicalBoard.get_complement_action(a)
            (next_s_dir1, canonicalBoard) = self.cache_data[(s, a)]
            (next_s_dir2, canonicalBoard) = self.cache_data[(s, comp_a)]
            game_copy_dir1 = game.get_copy()
            game_copy_dir2 = game.get_copy()

        if verbose:
            log.info(f"Non-leaf node, considering action {a}, {comp_a} resulting in\n{next_s_dir1}, {next_s_dir2}")

        v1 = self.search(game_copy_dir1, next_s_dir1, level=level+1)
        v2 = self.search(game_copy_dir2, next_s_dir2, level=level+1)
        v = (v1 + v2)/2 - self.args.varpen*(abs(v1-v2)) # average reward of the two children - penalize if the rewards are very different
        # the 2 children already have the reward which is the sum along the path, so the parent should have the average
        # if one of them got unsat, the reward would be lower

        if (s, a) in self.Qsa: # using (s,a) from the positive-dir of a
            max_found = v >= self.Bsa[(s, a)]
            self.Bsa[(s, a)] = max(self.Bsa[(s, a)], v)
            if self.args.debugging:
                with open(f"cubing_outputs/{self.args.o}_all_Bsa_scores.txt", "a") as f:
                    f.write(f"{s},{canonicalBoard.var2lit[a]}: {self.Bsa[(s, a)]} {'(max)' if max_found else ''}\n")
            self.Qsa[(s, a)] = (self.Nsa[(s, a)] * self.Qsa[(s, a)] + v) / (self.Nsa[(s, a)] + 1)
            self.Nsa[(s, a)] += 1

        else:
            self.Bsa[(s, a)] = v
            if self.args.debugging:
                with open(f"cubing_outputs/{self.args.o}_all_Bsa_scores.txt", "a") as f:
                    f.write(f"{s},{canonicalBoard.var2lit[a]}: {self.Bsa[(s, a)]} (max)\n")
            self.Qsa[(s, a)] = v
            self.Nsa[(s, a)] = 1

        if (s, comp_a) in self.Qsa: # using (s,a) from the negative-dir of a
            max_found = v >= self.Bsa[(s, comp_a)]
            self.Bsa[(s, comp_a)] = max(self.Bsa[(s, comp_a)], v)
            if self.args.debugging:
                with open(f"cubing_outputs/{self.args.o}_all_Bsa_scores.txt", "a") as f:
                    f.write(f"{s},{canonicalBoard.var2lit[comp_a]}: {self.Bsa[(s, comp_a)]} {'(max)' if max_found else ''}\n")
            self.Qsa[(s, comp_a)] = (self.Nsa[(s, comp_a)] * self.Qsa[(s, comp_a)] + v) / (self.Nsa[(s, comp_a)] + 1)
            self.Nsa[(s, comp_a)] += 1

        else:
            self.Bsa[(s, comp_a)] = v
            if self.args.debugging:
                with open(f"cubing_outputs/{self.args.o}_all_Bsa_scores.txt", "a") as f:
                    f.write(f"{s},{canonicalBoard.var2lit[comp_a]}: {self.Bsa[(s, comp_a)]} (max)\n")
            self.Qsa[(s, comp_a)] = v
            self.Nsa[(s, comp_a)] = 1

        self.data.append([level, self.Qsa[s,a], cur_best, v])
        self.data.append([level, self.Qsa[s,comp_a], cur_best, v])

        self.Ns[s] += 1
        if self.args.debugging:
            with open(f"cubing_outputs/{self.args.o}_all_Bsa_scores.txt", "a") as f:
                f.write(f"{s}: {v}\n")
        return v
