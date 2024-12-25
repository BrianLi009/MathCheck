#!/usr/bin/python
import sys, getopt
from squarefree import squarefree
from triangle_e import triangle
from neighbor import neighbor
from noncolorable import noncolorable
from cubic import cubic
from b_b_card import generate_edge_clauses
import subprocess
import os

def generate(n, block, lower_bound, upper_bound):
    """
    n: size of the graph
    Given n, the function calls each individual constraint-generating function, then write them into a DIMACS file as output
    The variables are listed in the following order:
    edges - n choose 2 variables
    triangles - n choose 3 variables
    extra variables from cubic
    """
    cnf_file = "constraints_" + str(n) + "_" + str(block) + "_2"
    if os.path.exists(cnf_file):
        print(f"File '{cnf_file}' already exists. Terminating...")
        sys.exit()
    edge_dict = {}
    tri_dict = {}
    count = 0
    clause_count = 0
    for j in range(1, n+1):             #generating the edge variables
        for i in range(1, j):
            count += 1
            edge_dict[(i,j)] = count
    for a in range(1, n-1):             #generating the triangle variables
        for b in range(a+1, n):
            for c in range(b+1, n+1):
                count += 1
                tri_dict[(a,b,c)] = count
    clause_count += squarefree(n, edge_dict, cnf_file)
    print ("graph is squarefree")
    clause_count += triangle(n, edge_dict, tri_dict, cnf_file)
    print ("all edges are part of a triangle")
    clause_count += noncolorable(n,  edge_dict, tri_dict, cnf_file, block)
    print ("graph is noncolorable")
    clause_count += neighbor(n, edge_dict, cnf_file)
    print ("every vertex has a neightbor")
    var_count, c_count = cubic(n, count, cnf_file) #total number of variables
    clause_count += c_count
    print ("isomorphism blocking applied")
    
    # Convert triangle dictionary values to sorted list
    tri_vars = [v for k, v in sorted(tri_dict.items())]
    var_count_card, clause_count_card = generate_edge_clauses(tri_vars, int(sys.argv[3]), int(sys.argv[4]), var_count, cnf_file)
    var_count = var_count_card
    clause_count += clause_count_card
    print("triangle count constraints applied")
    
    firstline = 'p cnf ' + str(var_count) + ' ' + str(clause_count)
    subprocess.call(["./gen_instance/append.sh", cnf_file, cnf_file+"_new", firstline])

if __name__ == "__main__":
   generate(int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4])