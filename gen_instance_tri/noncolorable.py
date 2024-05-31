import itertools
import math

def noncolorable(n, edge_dict, tri_dict, cnf, blocked=0.5, minimum=0):
    n = n*3
    cnf_file = open(cnf, 'a+')
    clause_count = 0
    vertices_lst = list(range(1, n+1))

    #given a particular configuration, if two vertices are in the same triangle and colored 1, they are connected. if three vertices 
    for i in range(math.ceil(n*float(minimum)+1), math.ceil(n*float(blocked)+1)):
        #block all labelings with i label-1s
        possible_comb = list(itertools.combinations(vertices_lst, i))
        #possible_comb contains all possible ways to label the graph with i label-1's
        print (possible_comb)
        
            
    return clause_count
