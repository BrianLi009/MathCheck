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

def generate(n, block, lower_bound, upper_bound, nostatic=False):
    """
    n: size of the graph
    Given n, the function calls each individual constraint-generating function, then write them into a DIMACS file as output
    The variables are listed in the following order:
    edges - n choose 2 variables
    triangles - n choose 3 variables
    extra variables from cubic
    """
    cnf_file = "constraints_" + str(n) + "_" + str(block)
    if lower_bound and upper_bound:
        cnf_file += f"_{lower_bound}_{upper_bound}"
    cnf_file += "_nostatic" if nostatic else "_2"
    
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
    
    # Only call cubic if nostatic is False
    if not nostatic:
        var_count, c_count = cubic(n, count, cnf_file) #total number of variables
        clause_count += c_count
        print ("isomorphism blocking applied")
    else:
        var_count = count  # If not calling cubic, use current count as var_count
    
    # Convert triangle dictionary values to sorted list and apply constraints only if bounds are provided
    if lower_bound and upper_bound:  # Changed from checking sys.argv length
        tri_vars = [v for k, v in sorted(tri_dict.items())]
        var_count_card, clause_count_card = generate_edge_clauses(tri_vars, int(lower_bound), int(upper_bound), var_count, cnf_file)
        var_count = var_count_card
        clause_count += clause_count_card
        print("triangle count constraints applied")
    
    firstline = 'p cnf ' + str(var_count) + ' ' + str(clause_count)
    subprocess.call(["./gen_instance/append.sh", cnf_file, cnf_file+"_new", firstline])

if __name__ == "__main__":
    # Parse command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["nostatic"])
    except getopt.GetoptError:
        print('Usage: generate-def2.py <n> <block> [lower_bound upper_bound] [--nostatic]')
        sys.exit(2)

    nostatic = False
    for opt, arg in opts:
        if opt == '--nostatic':
            nostatic = True

    if len(args) < 2:
        print('Usage: generate-def2.py <n> <block> [lower_bound upper_bound] [--nostatic]')
        sys.exit(2)

    n = int(args[0])
    block = args[1]
    lower_bound = args[2] if len(args) > 2 else None
    upper_bound = args[3] if len(args) > 3 else None
    
    generate(n, block, lower_bound, upper_bound, nostatic)