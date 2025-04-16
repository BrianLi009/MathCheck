#!/usr/bin/python
import sys, getopt
from squarefree import squarefree
from triangle import triangle
from mindegree import mindegree
from noncolorable_sic import noncolorable
from cubic import cubic
from cubic_lex_greatest import cubic as cubic_lex_greatest
from b_b_card import generate_edge_clauses
import subprocess
import os
import argparse

def generate(n, lower_bound=None, upper_bound=None):
    """
    n: size of the graph
    lower_bound: lower bound for triangle count
    upper_bound: upper bound for triangle count
    Given n, the function calls each individual constraint-generating function, then write them into a DIMACS file as output
    The variables are listed in the following order:
    edges - n choose 2 variables
    triangles - n choose 3 variables
    extra variables from cubic
    """
    base_name = f"constraints_{n}"
    if lower_bound and upper_bound:
        base_name += f"_{lower_bound}_{upper_bound}"
    
    cnf_file = base_name
    
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
    print ("all vertices are part of a triangle")
    clause_count += noncolorable(n, edge_dict, tri_dict, cnf_file)
    print ("graph is noncolorable")
    clause_count += mindegree(n, 3, edge_dict, cnf_file)
    print ("minimum degree of each vertex is 3")
    """
    conway(n, edge_dict, tri_dict, 1, 3)
    conway(n, edge_dict, tri_dict, 2, 4)
    conway(n, edge_dict, tri_dict, 3, 4)
    print ("conway constraint")
    """
    
    var_count = count  # No additional variables added
    
    # Add triangle count constraints if bounds are provided
    if lower_bound and upper_bound:
        tri_vars = [v for k, v in sorted(tri_dict.items())]
        var_count_card, clause_count_card = generate_edge_clauses(tri_vars, int(lower_bound), int(upper_bound), var_count, cnf_file)
        var_count = var_count_card
        clause_count += clause_count_card
        print("triangle count constraints applied")
    
    firstline = 'p cnf ' + str(var_count) + ' ' + str(clause_count)
    subprocess.call(["./gen_instance/append.sh", cnf_file, cnf_file+"_new", firstline])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate constraints for graph problems.')
    parser.add_argument('n', type=int, help='Size of the graph')
    parser.add_argument('--lower', type=int, help='Lower bound for triangle count')
    parser.add_argument('--upper', type=int, help='Upper bound for triangle count')
    
    args = parser.parse_args()
    
    # Validate bounds
    if (args.lower is None) != (args.upper is None):
        parser.error("Both lower and upper bounds must be provided together or omitted")
    
    generate(args.n, args.lower, args.upper)
