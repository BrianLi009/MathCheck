import itertools

def neighbor(n, edge_dict, cnf):
    #every vertex must have a neighbor
    clause_count = 0
    cnf_file = open(cnf, 'a+')
    vertices_lst = list(range(1, n+1))
    for v in vertices_lst:
        clause = []
        for v2 in vertices_lst:
            if v != v2:
                edge = tuple(sorted((v, v2)))
                clause.append(str(edge_dict[edge]))
        constraint_1 = ' '.join(clause)
        cnf_file.write(constraint_1 + " 0\n")
        clause_count += 1
    return clause_count