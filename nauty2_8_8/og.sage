from sage.all import *
set_random_seed(72)

def compute_can(base_graph_o):
    G = base_graph_o.copy()
    n = G.order()
    sofar = list(range(n))
    E_prime = set()

    for i in range(n - 1, -1, -1):
        # Perform canonical relabeling
        g_canonical, lab = G.canonical_label(algorithm='sage', certificate=True)

        # Update sofar based on the new labeling
        can = [sofar[lab[v]] for v in range(n)]
        sofar = can

        # Construct new edge set E_prime
        for j in range(i):
            k = lab[j]
            for h in G.neighbors(k):
                if j < lab[i] and lab[h] != j:  # Avoid self-loops
                    E_prime.add((lab[h], j))

        # Update the graph for the next iteration
        if i > 0:
            G.delete_vertex(i)
            G = Graph([list(range(i)), list(E_prime)])
        E_prime.clear()  # Clear E_prime for the next iteration

    # Construct and return the final canonical graph
    return Graph([list(range(n)), list(E_prime)])

# Test with a cycle graph
base_graph_1 = graphs.PetersenGraph()
base_graph_2 = graphs.PetersenGraph()
gamma = SymmetricGroup(10).random_element()
base_graph_2.relabel(gamma)

print("Are the original graphs isomorphic?", base_graph_1.is_isomorphic(base_graph_2))

# Apply the canonical labeling algorithm
canonical_base_graph_1 = compute_can(base_graph_1)
print("First canonical adjacency matrix:")
print(canonical_base_graph_1.adjacency_matrix())
print("=========")

canonical_base_graph_2 = compute_can(base_graph_2)
print("Second canonical adjacency matrix:")
print(canonical_base_graph_2.adjacency_matrix())

# Verify that the adjacency matrices are the same
assert canonical_base_graph_1.adjacency_matrix() == canonical_base_graph_2.adjacency_matrix(), "Adjacency matrices do not match!"
