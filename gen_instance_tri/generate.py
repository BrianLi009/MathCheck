#!/usr/bin/python
import sys, getopt
import subprocess
import os
from squarefree import squarefree
from neighbor import neighbor
from tri_relation import tri_relation
from noncolorable import noncolorable

#squarefree
#each vertex has a neighbor
#

def generate(n, block):
    """
    n: size of the dual graph (number of triangles in the original graph)
    Given n, the function calls each individual constraint-generating function, then write them into a DIMACS file as output
    The variables are listed in the following order:
    edges - n choose 2 variables
    triangles - n choose 3 variables
    extra variables from cubic
    """
    cnf_file = "constraints_" + str(n) + "_" + str(block) + ".cnf"
    if os.path.exists(cnf_file):
        print(f"File '{cnf_file}' already exists. Terminating...")
        sys.exit()
    count = 0
    clause_count = 0
    dual_edge_dict = {}
    edge_mapping_dict = {}
    tri_dict = {}
    for j in range(1, n+1):             #generating the edge variables
        for i in range(1, j):
            count += 1
            dual_edge_dict[(i,j)] = count
    vertex_var = count + 1
    for a in range(1, n+1):             #generating the triangle variables
        edge_mapping_dict[(a,1)] = vertex_var
        edge_mapping_dict[(a,2)] = vertex_var + 1
        edge_mapping_dict[(a,3)] = vertex_var + 2
        vertex_var += 3
    tri_var = vertex_var
    for tri in range(1, n+1):
        tri_dict[tri] = tri_var
        tri_var += 1
    clause_count += tri_relation(n, dual_edge_dict, edge_mapping_dict, tri_dict, cnf_file)
    clause_count += squarefree(n, edge_mapping_dict, cnf_file)
    clause_count += neighbor(n, edge_mapping_dict, cnf_file)
    #clause_count += noncolorable(n, edge_mapping_dict, tri_dict, "test") #have to think about this
    firstline = 'p cnf ' + str(tri_var-1) + ' ' + str(clause_count)
    subprocess.call(["./gen_instance/append.sh", cnf_file, cnf_file+"_new", firstline])

if __name__ == "__main__":
   generate(int(sys.argv[1]), sys.argv[2])