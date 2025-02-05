import argparse
import itertools
import logging
import coloredlogs

from tqdm import tqdm
import numpy as np
import wandb

import networkx as nx
import matplotlib.pyplot as plt
from ksgraph.KSGame import KSGame
import pydot
from networkx.drawing.nx_pydot import graphviz_layout

from Arena import calcAndLogMetrics
from utils import dotdict

log = logging.getLogger(__name__)
coloredlogs.install(level='INFO')

class GraphVisualization:
  def __init__(self, edge_labels):
    self.visual = []
    self.edge_labels = edge_labels

  def addEdge(self, a, b):
    temp = [a, b]
    self.visual.append(temp)

  def visualize(self):
    G = nx.Graph()
    G.add_edges_from(self.visual)
    # nx.draw_networkx(G)
    pos = graphviz_layout(G, prog="dot")
    plt.figure(figsize=(12,12)) 
    nx.draw(G, pos, with_labels=True, edge_color='black', width=1, linewidths=1, node_size=500, node_color='pink', alpha=0.9)
    nx.draw_networkx_edge_labels(
      G, pos,
      edge_labels=self.edge_labels,
      font_color='red'
    )
    plt.show()

class GraphVerifier:
    def __init__(self, V, root):
        self.V = V # No. of vertices
        self.E = 0 # No. of edges
        # Pointer to an array for adjacency lists
        self.adj = [[] for i in range(V)]
        self.fullBinary = True
        self.root = root

    # to add an edge to graph
    def addEdge(self, v, w):
        if w not in self.adj[v] and v not in self.adj[w]:
            self.E += 1 # increase the number of edges
            self.adj[v].append(w) # Add w to v’s list - directed edges
            # self.adj[w].append(v) # Add v to w’s list.

    # A recursive dfs function that uses visited[] and parent to
    # traverse the graph and mark visited[v] to true for visited nodes
    def dfsTraversal(self, v, visited, parent):
        # Mark the current node as visited
        visited[v] = True

        # Recur for all the vertices adjacent to this vertex
        for i in self.adj[v]:
            if len(self.adj[v]) not in [0, 2]: self.fullBinary = False
            # If an adjacent is not visited, then recur for that adjacent
            if not visited[i]:
                self.dfsTraversal(i, visited, v)

    # Returns true if the graph is connected, else false.
    def isConnected(self):
        # Mark all the vertices as not visited and not part of recursion stack

        visited = [False] * self.V

        # Performing DFS traversal of the graph and marking reachable vertices from root to true
        self.dfsTraversal(self.root, visited, -1)

        # If we find a vertex which is not reachable from root (not marked by dfsTraversal(), then we return false since graph is not connected
        for u in range(self.V):
            if not visited[u]:
                return False

        # since all nodes were reachable so we returned true and hence graph is connected
        return True

    def isFullBinaryTree(self):
        # as we proved earlier if a graph is connected and has V - 1 edges then it is a tree i.e. E = V - 1
        # print(self.isConnected(), self.E, self.V, self.fullBinary)
        return self.isConnected() and self.E == self.V - 1 and self.fullBinary

class CubeArena():

    def __init__(self, agent1, game, cubefile='cube.txt'):
        self.agent1 = agent1
        self.game = game
        self.cubefile = cubefile

    def parseCubeFile(self):
        file1 = open(self.cubefile, 'r')
        lines = file1.readlines()
        file1.close()

        lines = [l.split()[1:-1] for l in lines]
        l_set = set(itertools.chain(*lines)) # set of all literals
        l_dict = {k: v for v, k in enumerate(l_set)} # dict of literals to unique indices

        self.states = []
        for line in lines:
            state = ['f']
            for l in line:
                state.append(f'{state[-1]}_{l}') # state is being represented as f_{l1}_{l2}..._{ln} where f is the root and li is the ith literal in the path
            self.states.append(state) # self.states is a list of lists of self.states consisting of all paths from root to leaves
        
        s_list = list(itertools.chain(*self.states))
        self.s_set = set(s_list) # set of all self.states
        self.s_dict = {k: v for v, k in enumerate(self.s_set)} # dict of self.states to unique indices

        self.edge_labels = {}
        edge_labels_org = {}

        for state in self.states:
            for i in range(len(state)-1):
                self.edge_labels[(self.s_dict[state[i]], self.s_dict[state[i+1]])] = state[i+1].split('_')[-1]
                edge_labels_org[(state[i], state[i+1])] = state[i+1].split('_')[-1]
        
        return lines
    
    def visualizeCube(self):
        G = GraphVisualization(self.edge_labels)
        for state in self.states:
            for i in range(len(state)-1):
                G.addEdge(self.s_dict[state[i]], self.s_dict[state[i+1]])
        G.visualize()

    def verifyCube(self):
        root = [v for k, v in self.s_dict.items() if k=='f'][0]
        g = GraphVerifier(len(self.s_set), root)
        for state in self.states:
            for i in range(len(state)-1):
                g.addEdge(self.s_dict[state[i]], self.s_dict[state[i+1]])

        assert g.isFullBinaryTree() == True, "Graph is not a Full Binary Tree"

        log.info("Verified that the cube is a Full Binary Tree")

    def simulatePath(self, game, board, cube, solver_time):
        # TODO: Incorporate canonicalBoard & symmetry appropriately when required in the future
        # canonicalBoard = game.getCanonicalForm(board)
        # sym = game.getSymmetries(canonicalBoard, pi)
        # for b, p in sym:
        #     trainExamples.append([b.get_state(), p, None])
        
        # visited.add(v) # no need if we are using a tree

        for literal in cube:
            action = board.lit2var[int(literal)]
            
            # verify that the action is valid in the current board and the game is not over
            # valids = game.getValidMoves(board)
            # assert valids[action], f"Invalid action chosen by cube agent - {cube}, {board}, {board.get_legal_literals()}"
            reward_now = game.getGameEnded(board)
            assert reward_now is None, f"Invalid board state: Game is over - {board}"

            game_copy = game.get_copy()
            board = game_copy.getNextState(board, action)

        # now the game should be over
        reward_now = game.getGameEnded(board, eval_cls=True)
        assert reward_now is not None, f"Invalid board state: Game is not over - {board}"

        # if board.is_giveup():
        print(f"Cube: {cube}, reward: {reward_now}, board.total_rew: {board.total_rew}, avg_reward: {board.total_rew/board.step}")
        if reward_now > 0:
            solver_time.append(reward_now) 
        
        return reward_now     

    def playGame(self, list_of_cubes):

        game = self.game.get_copy()
        board = game.getInitBoard()

        solver_time = [] # solver time in seconds at leaf nodes (when game is in giveup state)
        rew = 0
        unsat_count = 0
        
        for cube in list_of_cubes:
            game = self.game.get_copy()
            board = game.getInitBoard()
            rew_current = self.simulatePath(game, board, cube, solver_time)
            if rew_current == -1: 
                unsat_count += 1
            else:
                assert rew_current > 0, f"Invalid reward: {rew_current}"
                rew += rew_current

        calcAndLogMetrics(0, np.array([[solver_time]]), "CubeAgent", newagent=False)

        assert len(solver_time)+unsat_count == len(list_of_cubes), f"Number of cubes ({len(list_of_cubes)}) and solver time ({len(solver_time)}) don't match"

        log.info(f"Cube Agent Total Reward: {rew} for {len(list_of_cubes)} cubes; Average Reward: {rew/len(list_of_cubes)}; Unsat/Err Count: {unsat_count}")

    def runSimulation(self): # main method
        list_of_cubes = self.parseCubeFile()
        # self.verifyCube()
        # self.visualizeCube()
        self.playGame(list_of_cubes)

if __name__ == '__main__':
    # python -u CubeArena.py "constraints_18_c_100000_2_2_0_final.simp" -order 18 -n 20 -m 153 -o "e4_18_mcts_nod_s300_c05.cubes"

    wandb.init(mode="disabled")

    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="filename of the CNF file", type=str)
    parser.add_argument("-order", help="KS order", type=int)
    parser.add_argument("-n", help="cutoff when n variables are eliminated", type=int)
    # parser.add_argument("-d", help="cutoff when d depth is reached", type=int)
    parser.add_argument("-m", help="only top m variables to be considered for cubing", type=int)
    parser.add_argument("-o", help="cube file")
    args_parsed = parser.parse_args()

    args = dotdict({**vars(args_parsed)})

    args['VARS_TO_ELIM'] = args_parsed.n
    args['STEP_UPPER_BOUND'] = args_parsed.n
    args['MAX_LITERALS'] = args_parsed.m
    args['STATE_SIZE'] = 10
    args['STEP_UPPER_BOUND_MCTS'] = 20
    args['MCTSmode'] = 0
    args['debugging'] = False
    args['wandb_logging'] = False
    args['LIMIT_TOP_3'] = False

    game = KSGame(args=args, filename=args.filename) 

    CubeArena(agent1=None, game=game, cubefile=args.o).runSimulation()
