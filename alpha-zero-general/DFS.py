# Python3 program to print DFS traversal
# from a given graph
from collections import defaultdict

# This class represents a directed graph using
# adjacency list representation


class Graph:
  def __init__(self):
    self.graph = defaultdict(list)
    self.d_state_rew = {3: 30, 4: 40, 6: 60, 7: 70, 10: 100, 12: 120, 13: 130, 14: 140} # all leafs

  def addEdge(self, u, v):
    self.graph[u].append(v)

  def DFSUtil(self, v, visited, level, rew):
    visited.add(v)
    # change: pi = getPi(v)
    reward_now = self.d_state_rew[v] if v in self.d_state_rew else 0 # change: getReward(v)
    if reward_now > 0: # change: isDone()
      rew[v] = reward_now
      return reward_now # only leaves have rewards, leaves don't have neighbors

    # Non-leaf nodes
    # change: a = sample(pi)
    # change: assert a and -a are valid actions
    # change: neighbors = [v1=go(v,a), v2=go(v,-a)] # take care of var/lit conversion
    for neighbour in self.graph[v]: # change: dynamic neighbors calc above
      if neighbour not in visited: # Change: not req for a tree as there always exists a unique path from root to any node
        reward_now += self.DFSUtil(neighbour, visited, level+1, rew)
    
    rew[v] = reward_now # after all children are visited, add a reward to the current node
    return reward_now # return the reward to the parent

  def DFS(self, v):
    visited = set()
    rew = {}
    self.DFSUtil(v, visited, level=0, rew=rew)
    print(rew)

if __name__ == "__main__":
  g = Graph()
  g.addEdge(0, 1)
  g.addEdge(1, 2)
  g.addEdge(2, 3)
  g.addEdge(2, 4)
  g.addEdge(1, 5)
  g.addEdge(0, 8)
  g.addEdge(8, 14)
  g.addEdge(8, 9)
  g.addEdge(9, 10)
  g.addEdge(9, 11)
  g.addEdge(11, 12)
  g.addEdge(11, 13)
  g.addEdge(5, 6)
  g.addEdge(5, 7)

  print("Following is DFS from (starting from vertex 2)")
  # Function call
  g.DFS(0)

# This code is contributed by Neelam Yadav
