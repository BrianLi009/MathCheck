import itertools

def triangle(n, edge_dict, tri_dict, cnf):
    """
    Encode the property that each edge in a graph is part of at least one triangle.

    Args:
    n (int): The number of vertices in the graph.
    edge_dict (dict): A dictionary mapping each edge to a unique variable.
    tri_dict (dict): A dictionary mapping each triangle to a unique variable.
    cnf (str): The filename where the CNF clauses will be written.

    Returns:
    int: The total number of clauses written.
    """
    cnf_file = open(cnf, 'a+')
    clause_count = 0

    # List of all vertices in the graph
    vertices_lst = list(range(1, n+1))

    # Map each edge to the triangles it is part of
    edge_to_triangles = {}
    for triangle in itertools.combinations(vertices_lst, 3):
        # Convert sorted_triangle to a tuple so it can be used as a dictionary key
        sorted_triangle = tuple(sorted(triangle))
        for edge in itertools.combinations(sorted_triangle, 2):
            edge_to_triangles.setdefault(edge, []).append(sorted_triangle)

        # If a triangle exists, all its edges must exist
        edges = [edge_dict[edge] for edge in itertools.combinations(sorted_triangle, 2)]
        triangle_var = tri_dict[sorted_triangle]  
        for edge_var in edges:
            # Clause: Triangle implies edge
            cnf_file.write('{} {} 0\n'.format(-triangle_var, edge_var))
            clause_count += 1
        negated_edges = [-e for e in edges]
        cnf_file.write(' '.join(map(str, negated_edges)) + " {} 0\n".format(triangle_var))
        clause_count += 1

     # Create a CNF clause for each edge
    for edge, triangles in edge_to_triangles.items():
        clause = [str(tri_dict[tri]) for tri in triangles]
        cnf_file.write('-' + str(edge_dict[edge]) + ' ' + ' '.join(clause) + " 0\n")
        clause_count += 1

    cnf_file.close()
    return clause_count
