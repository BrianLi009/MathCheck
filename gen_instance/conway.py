import itertools
from itertools import combinations
from itertools import product

def generate_implication_clause(a,b):
    clause=[]
    if 'F' in a or 'T' in b: #whole clause is T if any variable in is T
        pass
    else:
        for i in a:
            if  i == 'T': #False variables in a DNF dont contribute.... does this give upper though??
                continue
            else:
                clause.append(str(-(i)))#pattern in the 4 clauses, a is always -ive
        for j in b:
            if j == 'F':
                continue
            else:
                clause.append(str(j))#pattern in the 4 clauses, b is always +ive
        #clause.append("0"+"\n")
        return(clause)

# Generate clauses encoding that exactly s variables in X are assigned true (using sequential counters)
def generate_adder_clauses(X, s, total_vars, force = False):
    clauses = []
    n = len(X)
    k = s+1
    S = [[0 for j in range(k+1)] for i in range(n+1)]

    for i in range(n+1):
        S[i][0] = 'T'

    for j in range(1, k+1):
        S[0][j] = 'F'

    if force:
        S[n][s] = 'T'
        S[n][k] = 'F'

    # Define new auxiliary variables (and updates the global variable total_vars)
    for i in range(n+1):
        for j in range(k+1):
            if S[i][j] == 0:
                total_vars += 1
                S[i][j] = total_vars
    
    # Generate clauses encoding cardinality constraint
    for i in range(1, n+1):
        for j in range(1, k+1):
            clauses.append(generate_implication_clause({S[i-1][j]}, {S[i][j]}))
            clauses.append(generate_implication_clause({X[i-1], S[i-1][j-1]}, {S[i][j]}))
            clauses.append(generate_implication_clause({S[i][j]}, {S[i-1][j], X[i-1]}))
            clauses.append(generate_implication_clause({S[i][j]}, {S[i-1][j], S[i-1][j-1]}))
    return clauses, S, total_vars
                        
def conway(n, edge_dict, tri_dict, tri_count_lst, cnf, var_count):
    #at least vs vertices are connected to at least t triangles
    clause_count = 0
    cnf_file = open(cnf, 'a+')
    vertices_lst = list(range(1, n+1))
    all_tri = list(itertools.combinations(vertices_lst, 3))
    t = 4 #we don't need to generate the entire counting matrix
    extra_var_dict_master = {}

    #Encoding triangles, need to be uncommented when noncolorable.py is not called

    """for triangle in list(itertools.combinations(vertices_lst, 3)):
        # the following encoding are applied in every possible triangle in the graph
        # given a triangle, if encode the equivalence relation
        v_1 = triangle[0]
        v_2 = triangle[1]
        v_3 = triangle[2]
        vertices = [v_1, v_2, v_3]
        vertices.sort()
        edge_1 = (vertices[0], vertices[1])
        edge_2 = (vertices[1], vertices[2])
        edge_3 = (vertices[0], vertices[2])
        cnf_file.write('{} {} 0\n'.format(str(edge_dict[edge_1]), str(-tri_dict[triangle])))
        cnf_file.write('{} {} 0\n'.format(str(edge_dict[edge_2]), str(-tri_dict[triangle])))
        cnf_file.write('{} {} 0\n'.format(str(edge_dict[edge_3]), str(-tri_dict[triangle])))
        cnf_file.write('{} {} {} {} 0\n'.format(str(-edge_dict[edge_1]), str(-edge_dict[edge_2]), str(-edge_dict[edge_3]), str(tri_dict[triangle])))
        clause_count += 4"""

    #Encoding bowtie, such that triangle 1 and triangle 2 iff bowtie 12
    bowtie_dict = {}
    for tri_pair in itertools.combinations(all_tri, 2):
        tri_1 = tri_pair[0]
        tri_2 = tri_pair[1]
        unique_elements = sorted(set(tri_1 + tri_2))
        if len(unique_elements) == 5:
            #tri_1 and tri_2 iff bowtie_12
            bowtie = var_count + 1
            bowtie_dict[frozenset(unique_elements)] = bowtie
            tri_1_var = tri_dict[tri_1]
            tri_2_var = tri_dict[tri_2]
            var_count += 1
            clause_1 = str(bowtie) + " -" + str(tri_1_var) + " -" + str(tri_2_var)
            clause_2 = "-" + str(bowtie) + " " + str(tri_1_var)
            clause_3 = "-" + str(bowtie) + " " + str(tri_2_var)
            cnf_file.write(clause_1 + " 0\n")
            cnf_file.write(clause_2 + " 0\n")
            cnf_file.write(clause_3 + " 0\n")
            clause_count += 3

    #Encoding cardinality variables on the triangles adjacent to each vertex
    for v in range(1, n+1):
        v_tri_lst = [tri for tri in all_tri if v in tri] #triangles containing v
        small_tri_lst = [tri_dict[tri] for tri in v_tri_lst]
        clauses, extra_var_matrix, var_count = generate_adder_clauses(small_tri_lst, t, var_count)
        for clause in clauses:
            if clause is not None:
                converted_clause = ' '.join(clause) + ' 0'
                cnf_file.write(converted_clause + "\n")
                clause_count += 1
        extra_var_dict_master[v] = extra_var_matrix

    ind_dict = {}
    #have a ind_var for each bowtie, such that ind_var <-> bowtie and ind_1 and ind_2 and ind_3 and ind_4 and ind_5
    clause = ""
    for bowtie in bowtie_dict:
        ind_var = var_count + 1
        ind_dict[bowtie] = ind_var
        bowtie_lst = list(bowtie)
        v1, v2, v3, v4, v5 = bowtie_lst[0], bowtie_lst[1], bowtie_lst[2], bowtie_lst[3], bowtie_lst[4]
        deg1, deg2, deg3, deg4, deg5 = tri_count_lst[0], tri_count_lst[1], tri_count_lst[2], tri_count_lst[3], tri_count_lst[4]
        #vi can be accessed at extra_var_dict_master[vi][len(extra_var_dict_master[vi])-1][deg1]
        v1_ind = extra_var_dict_master[v1][len(extra_var_dict_master[v1])-1][deg1]
        v2_ind = extra_var_dict_master[v2][len(extra_var_dict_master[v2])-1][deg2]
        v3_ind = extra_var_dict_master[v3][len(extra_var_dict_master[v3])-1][deg3]
        v4_ind = extra_var_dict_master[v4][len(extra_var_dict_master[v3])-1][deg4]
        v5_ind = extra_var_dict_master[v5][len(extra_var_dict_master[v3])-1][deg5]
        #ind_var <-> bowtie and ind_1 and ind_2 and ind_3 and ind_4 and ind_5
        clause_1 = str(ind_var) + " -" + str(bowtie_dict[bowtie]) + " -" + str(v1_ind) + " -" + str(v2_ind) + " -" + str(v3_ind) + " -" + str(v4_ind) + " -" + str(v5_ind)
        clause_2 = "-" + str(ind_var) + " " + str(bowtie_dict[bowtie])
        clause_3 = "-" + str(ind_var) + " " + str(v1_ind)
        clause_4 = "-" + str(ind_var) + " " + str(v2_ind)
        clause_5 = "-" + str(ind_var) + " " + str(v3_ind)
        clause_6 = "-" + str(ind_var) + " " + str(v4_ind)
        clause_7 = "-" + str(ind_var) + " " + str(v5_ind)
        cnf_file.write(clause_1 + " 0\n")
        cnf_file.write(clause_2 + " 0\n")
        cnf_file.write(clause_3 + " 0\n")
        cnf_file.write(clause_4 + " 0\n")
        cnf_file.write(clause_5 + " 0\n")
        cnf_file.write(clause_6 + " 0\n")
        cnf_file.write(clause_7 + " 0\n")
        clause = clause + str(ind_var) + " "
        clause_count += 7
        var_count += 1
    cnf_file.write(clause + "0\n")
    clause_count += 1

    return var_count, clause_count