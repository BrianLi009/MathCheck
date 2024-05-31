import itertools

def squarefree(n, edge_dict, cnf):
    """
    input number of vertices n, and the variable dictionary, generate the SAT encoding for squarefree graph
    return a list of tuple, where each tuple is a clause, and each integer is a variable
    """
    clause_count = 0
    cnf_file = open(cnf, 'a+')
    edges =  (list(edge_dict.keys()))
    
    all_comb = list(itertools.combinations(edges, 4)) #list of all possible squares
    for comb in all_comb:
        if check_occurrences(comb):
            cnf_file.write('{} {} {} {} 0\n'.format(str(-edge_dict[comb[0]]), str(-edge_dict[comb[1]]), str(-edge_dict[comb[2]]), str(-edge_dict[comb[3]])))
            clause_count += 1
    return clause_count

def check_occurrences(tuple_data):
    occurrence_dict = {}
    unique_integers = set()

    # Count the occurrences of each integer and track unique integers
    for tuple_element in tuple_data:
        for integer in tuple_element:
            if integer in occurrence_dict:
                occurrence_dict[integer] += 1
            else:
                occurrence_dict[integer] = 1
            unique_integers.add(integer)
    #print (unique_integers)
    # Check if there are exactly four unique integers
    if len(unique_integers) != 4:
        return False
    #print (occurrence_dict)
    # Check if each integer occurs exactly twice
    for count in occurrence_dict.values():
        if count != 2:
            return False

    return True