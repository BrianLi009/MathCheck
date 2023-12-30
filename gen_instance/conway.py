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
                        
def conway(n, edge_dict, tri_dict, count_dict, tri_count_dict, cnf, var_count):
    #at least vs vertices are connected to at least t triangles
    clause_count = 0
    cnf_file = open(cnf, 'a+')
    vertices_lst = list(range(1, n+1))
    all_tri = list(itertools.combinations(vertices_lst, 3))
    t = max(count_dict.values())
    extra_var_dict_master = {}

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

    for v in range(1, n+1):
        v_tri_lst = [tri for tri in all_tri if v in tri] #triangles containing v
        small_tri_lst = [tri_dict[tri] for tri in v_tri_lst]
        clauses, extra_var_matrix, var_count = generate_adder_clauses(small_tri_lst, 3, var_count)
        for clause in clauses:
            if clause is not None:
                converted_clause = ' '.join(clause) + ' 0'
                cnf_file.write(converted_clause + "\n")
                clause_count += 1
        #want to include that at least t of the vars are True
        extra_var_dict_master[v] = extra_var_matrix
    for vs in count_dict:
        t = count_dict[vs]
        #out of all counting variables for each counting matrix at position S[len(S)][t], vs of them must be True
        count_lst = []
        for i in range(1, n+1):
            count_lst.append(extra_var_dict_master[i][len(extra_var_dict_master[i])-1][t])
        clauses, ind_matrix, var_count = generate_adder_clauses(count_lst, vs, var_count, True)
        for clause in clauses:
            if clause is not None:
                converted_clause = ' '.join(clause) + ' 0'
                cnf_file.write(converted_clause + "\n")
                clause_count += 1
    for structure in tri_count_dict:
        #have a ind_var for each triangle, such that ind_var <-> tri and ind_1 and ind_2 and ind_3 (need to find ind_1, ind_2, ind_3 correspondingly)
        clause = ""
        for tri in all_tri:
            ind_var = var_count + 1
            v1, v2, v3 = tri[0], tri[1], tri[2]
            deg1, deg2, deg3 = structure[0], structure[1], structure[2]
            #vi can be accessed at extra_var_dict_master[vi][len(extra_var_dict_master[vi])-1][deg1]
            v1_ind = extra_var_dict_master[v1][len(extra_var_dict_master[v1])-1][deg1]
            v2_ind = extra_var_dict_master[v2][len(extra_var_dict_master[v2])-1][deg2]
            v3_ind = extra_var_dict_master[v3][len(extra_var_dict_master[v3])-1][deg3]
            #ind_var <-> tri and ind_1 and ind_2 and ind_3
            clause_1 = str(ind_var) + " -" + str(tri_dict[tri]) + " -" + str(v1_ind) + " -" + str(v2_ind) + " -" + str(v3_ind)
            clause_2 = "-" + str(ind_var) + " " + str(tri_dict[tri])
            clause_3 = "-" + str(ind_var) + " " + str(v1_ind)
            clause_4 = "-" + str(ind_var) + " " + str(v2_ind)
            clause_5 = "-" + str(ind_var) + " " + str(v3_ind)
            cnf_file.write(clause_1 + " 0\n")
            cnf_file.write(clause_2 + " 0\n")
            cnf_file.write(clause_3 + " 0\n")
            cnf_file.write(clause_4 + " 0\n")
            cnf_file.write(clause_5 + " 0\n")
            clause = clause + str(ind_var) + " "
            clause_count += 5
            var_count += 1
        cnf_file.write(clause + "0\n")
        clause_count += 1
    return var_count, clause_count