import itertools

def neighbor(n, edge_dict, cnf):
    #every vertex must have a neighbor
    clause_count = 0
    cnf_file = open(cnf, 'a+')
    vertices_lst = list(range(1, n+1))
    for v in vertices_lst:
        edges = []
        for edge in edge_dict.keys():
            if edge[0] == v:
                edges.append(edge)
        cnf_file.write('{} {} {} 0\n'.format(str(edge_dict[edges[0]]), str(edge_dict[edges[1]]), str(edge_dict[edges[2]])))
        clause_count += 1
    return clause_count