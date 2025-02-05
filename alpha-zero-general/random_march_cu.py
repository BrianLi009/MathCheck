import logging
import os
import sys
from collections import deque
from pickle import Pickler, Unpickler
from random import shuffle
import random

import numpy as np
from tqdm import tqdm
import wandb

import itertools
from ksgraph.KSGame import KSGame

from utils import *


args = dotdict({
    'numIters': 1,           # TODO: Change this to 1000
    'numEps': 1,              # Number of complete self-play games to simulate during a new iteration.
    'tempThreshold': 10,        #
    'updateThreshold': None,     # During arena playoff, new neural net will be accepted if threshold or more of games are won.
    'maxlenOfQueue': 200000,    # Number of game examples to train the neural networks.
    'numMCTSSims': 50,          # Number of games moves for MCTS to simulate.
    'arenaCompare': 1,         # TODO: change this to 20 or 40 # Number of games to play during arena play to determine if new net will be accepted.
    'cpuct': 1,                 # controls the amount of exploration; keeping high for MCTSmode 0

    'checkpoint': './temp/',
    'load_model': False,
    'load_folder_file': ('/dev/models/8x100x50','best.pth.tar'),
    'numItersForTrainExamplesHistory': 20,

    'CCenv': True, # True for all servers and laptop
    'model_name': 'MCTS',
    'model_notes': 'MCTS without NN',
    'model_mode': 'mode-0',
    'phase': 'initial-testing',

    'debugging': False,

    'MCTSmode': 0, # mode 0 - executeEpisode, no learning, heuristic tree search, MCTS ignore direction;

    'order': 4, # 17,
    'MAX_LITERALS': 6, # 17*16//2,
    'STATE_SIZE': 10,
    'STEP_UPPER_BOUND': 4, # 10, # max depth of CnC
})

wandb.init(mode="disabled")

game = KSGame(args=args, filename="cnc.cnf") 

def DFSUtil(game, board, level, trainExamples, all_cubes):
    reward_now = game.getGameEnded(board)
    if reward_now: # reward is not None, i.e., game over
        flattened_list = itertools.chain.from_iterable(board.prior_actions)
        all_cubes.append(flattened_list)
        return reward_now # only leaves have rewards & leaves don't have neighbors
    else: # None
        reward_now = 0 # initialize reward for non-leaf nodes
    # Non-leaf nodes
    valid_vars = [board.lits2var[l] for l in board.get_legal_literals()]
    valids = game.getValidMoves(board)

    a = random.choice(valid_vars)
    game_copy_dir1 = game.get_copy()
    next_s_dir1 = game_copy_dir1.getNextState(board, a)

    comp_a = board.get_complement_action(a) # complement of the literal
    game_copy_dir2 = game.get_copy()
    next_s_dir2 = game_copy_dir2.getNextState(board, comp_a)

    assert valids[a] and valids[comp_a], "Invalid action chosen by MCTS"

    for game_n, neighbour in zip((game_copy_dir1, game_copy_dir2), (next_s_dir1, next_s_dir2)): 
        reward_now += DFSUtil(game_n, neighbour, level+1, trainExamples, all_cubes)
    
    trainExamples.append([board.get_state(), reward_now]) # after all children are visited, add a reward to the current node
    return reward_now # return the reward to the parent

trainExamples = []
all_cubes = []
game = game.get_copy()
board = game.getInitBoard()

DFSUtil(game, board, level=1, trainExamples=trainExamples, all_cubes=all_cubes)

random_cubes = [list(map(str, l)) for l in all_cubes]
if os.path.exists("random_cubes.txt"):
    print("random_cubes.txt already exists. Replacing old file!")
f = open("random_cubes.txt", "w")
f.writelines(["a " + " ".join(l) + " 0\n" for l in random_cubes])
f.close()

print("Saved cubes to file")
