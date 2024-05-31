import itertools

def tri_relation(n, dual_edge_dict, original_edge_dict, tri_dict, cnf):
    #every vertex must have a neighbor
    clause_count = 0
    cnf_file = open(cnf, 'a+')
    for triangle in list(tri_dict.keys()):
        edge_lst = []
        for edge in list(original_edge_dict.keys()):
            if edge[0] == triangle:
                edge_lst.append(edge)
        cnf_file.write('{} {} 0\n'.format(str(original_edge_dict[edge_lst[0]]), str(-tri_dict[triangle])))
        cnf_file.write('{} {} 0\n'.format(str(original_edge_dict[edge_lst[1]]), str(-tri_dict[triangle])))
        cnf_file.write('{} {} 0\n'.format(str(original_edge_dict[edge_lst[2]]), str(-tri_dict[triangle])))
        cnf_file.write('{} {} {} {} 0\n'.format(str(-original_edge_dict[edge_lst[0]]), str(-original_edge_dict[edge_lst[1]]), str(-original_edge_dict[edge_lst[2]]), str(tri_dict[triangle])))
        clause_count += 4
    for dual_edge in list(dual_edge_dict.keys()):
        tri_1 = dual_edge[0]
        tri_2 = dual_edge[1]
        tri_1_var = tri_dict[tri_1]
        tri_2_var = tri_dict[tri_2]
        cnf_file.write('{} {} 0\n'.format(str(-dual_edge_dict[dual_edge]), str(tri_1_var)))
        cnf_file.write('{} {} 0\n'.format(str(-dual_edge_dict[dual_edge]), str(tri_2_var)))
        cnf_file.write('{} {} {} 0\n'.format(str(dual_edge_dict[dual_edge]), str(-tri_1_var), str(-tri_2_var)))
    return clause_count