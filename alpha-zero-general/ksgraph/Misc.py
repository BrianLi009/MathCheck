# convert the 2-D adjacency matrix to a 1-D vector of the upper triangular elements
def adj2triu(self, adj_matrix): 
    assert len(adj_matrix) == self.n
    i = np.triu_indices(self.n, k=1) # k=1 to exclude the diagonal
    col_wise_sort = i[1].argsort()
    i_new = (i[0][col_wise_sort], i[1][col_wise_sort])
    board_triu = adj_matrix[i_new]
    return board_triu

# convert the a 1-D vector of the upper triangular elements to a 2-D adjacency matrix
def triu2adj(self, board_triu): 
    assert len(board_triu) == self.n*(self.n-1)//2
    adj_matrix = np.zeros((self.n, self.n), dtype=int)
    i = np.triu_indices(self.n, k=1) # k=1 to exclude the diagonal
    col_wise_sort = i[1].argsort()
    i_new = (i[0][col_wise_sort], i[1][col_wise_sort])
    adj_matrix[i_new] = board_triu
    return adj_matrix

# create a isomorphic graph from the adjacency matrix
def create_graph(self, adj_matrix, permutation_matrix):
    G = nx.from_numpy_array(adj_matrix)
    H = nx.relabel_nodes(G, dict(zip(G.nodes(), permutation_matrix)))
    return H

# print networkx graph from adjacency matrix
def print_graph(self, adj_matrix):
    G = nx.from_numpy_array(adj_matrix)
    nx.draw(G, with_labels=True)