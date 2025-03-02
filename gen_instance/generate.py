#!/usr/bin/python
import sys, getopt
from squarefree import squarefree
from triangle import triangle
from mindegree import mindegree
from noncolorable import noncolorable
from cubic import cubic
from cubic_lex_greatest import cubic as cubic_lex_greatest
import subprocess
import os

def generate(n, block, lex_option="lex-least"):
    """
    n: size of the graph
    block: color ratio to block
    lex_option: "lex-least", "lex-greatest", or "no-lex" to control isomorphism blocking
    Given n, the function calls each individual constraint-generating function, then write them into a DIMACS file as output
    The variables are listed in the following order:
    edges - n choose 2 variables
    triangles - n choose 3 variables
    extra variables from cubic
    """
    base_name = f"constraints_{n}_{block}_1"
    
    if lex_option == "lex-greatest":
        cnf_file = base_name + "_lex_greatest"
    elif lex_option == "no-lex":
        cnf_file = base_name + "_no_lex"
    else:  # lex-least is the default
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
    clause_count += noncolorable(n,  edge_dict, tri_dict, cnf_file, block)
    print ("graph is noncolorable")
    clause_count += mindegree(n, 3, edge_dict, cnf_file)
    print ("minimum degree of each vertex is 3")
    """
    conway(n, edge_dict, tri_dict, 1, 3)
    conway(n, edge_dict, tri_dict, 2, 4)
    conway(n, edge_dict, tri_dict, 3, 4)
    print ("conway constraint")
    """
    # Apply isomorphism blocking only if not using no-lex
    if lex_option != "no-lex":
        # Choose which cubic implementation to use
        cubic_impl = cubic_lex_greatest if lex_option == "lex-greatest" else cubic
        print(f"Using {lex_option} ordering for isomorphism blocking")
        var_count, c_count = cubic_impl(n, count, cnf_file)
        clause_count += c_count
        print("isomorphism blocking applied")
    else:
        print("Skipping isomorphism blocking (no-lex option)")
        var_count = count  # No additional variables added
    
    firstline = 'p cnf ' + str(var_count) + ' ' + str(clause_count)
    subprocess.call(["./gen_instance/append.sh", cnf_file, cnf_file+"_new", firstline])

if __name__ == "__main__":
    lex_option = "lex-least"  # Default
    if len(sys.argv) > 3:
        if sys.argv[3] == "lex-greatest":
            lex_option = "lex-greatest"
        elif sys.argv[3] == "no-lex":
            lex_option = "no-lex"
    
    generate(int(sys.argv[1]), sys.argv[2], lex_option)
