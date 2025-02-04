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

def generate(n, block, lex_greatest=False):
    """
    n: size of the graph
    block: color ratio to block
    lex_greatest: whether to use lex-greatest ordering
    Given n, the function calls each individual constraint-generating function, then write them into a DIMACS file as output
    The variables are listed in the following order:
    edges - n choose 2 variables
    triangles - n choose 3 variables
    extra variables from cubic
    """
    base_name = f"constraints_{n}_{block}_1"
    cnf_file = base_name + "_lex_greatest" if lex_greatest else base_name
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
    # Choose which cubic implementation to use
    cubic_impl = cubic_lex_greatest if lex_greatest else cubic
    var_count, c_count = cubic_impl(n, count, cnf_file)
    clause_count += c_count
    print ("isomorphism blocking applied")
    firstline = 'p cnf ' + str(var_count) + ' ' + str(clause_count)
    subprocess.call(["./gen_instance/append.sh", cnf_file, cnf_file+"_new", firstline])

if __name__ == "__main__":
    lex_greatest = len(sys.argv) > 3 and sys.argv[3] == "lex-greatest"
    generate(int(sys.argv[1]), sys.argv[2], lex_greatest)
