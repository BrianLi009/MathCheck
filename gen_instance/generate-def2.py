#!/usr/bin/python
import sys, getopt
from squarefree import squarefree
from triangle_e import triangle
from neighbor import neighbor
from mindegree import mindegree
from noncolorable import noncolorable
from cubic import cubic
from cubic_lex_greatest import cubic as cubic_lex_greatest
from b_b_card import generate_edge_clauses
import subprocess
import os
import argparse

def generate(n, block, lower_bound=None, upper_bound=None, lex_option="lex-least"):
    """
    n: size of the graph
    block: color ratio to block
    lower_bound: lower bound for triangle count
    upper_bound: upper bound for triangle count
    lex_option: "lex-least", "lex-greatest", or "no-lex" to control isomorphism blocking
    """
    cnf_file = "constraints_" + str(n) + "_" + str(block)
    if lower_bound and upper_bound:
        cnf_file += f"_{lower_bound}_{upper_bound}"
    
    if lex_option == "no-lex":
        cnf_file += "_no_lex"
    elif lex_option == "lex-greatest":
        cnf_file += "_lex_greatest"
    else:
        cnf_file += "_2"  # Default suffix for definition 2
    
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
    
    # Only apply isomorphism blocking if not using no-lex
    if lex_option != "no-lex":
        cubic_impl = cubic_lex_greatest if lex_option == "lex-greatest" else cubic
        print(f"Using {lex_option} ordering for isomorphism blocking")
        var_count, c_count = cubic_impl(n, count, cnf_file) #total number of variables
        clause_count += c_count
        print ("isomorphism blocking applied")
    else:
        var_count = count  # If not applying isomorphism blocking, use current count as var_count
        print("Skipping isomorphism blocking (no-lex option)")
    
    # Convert triangle dictionary values to sorted list and apply constraints only if bounds are provided
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
    parser.add_argument('block', type=str, help='Block identifier')
    parser.add_argument('lex_option', type=str, nargs='?', default="lex-least", 
                      help='Isomorphism blocking option: "lex-least" (default), "lex-greatest", or "no-lex"')
    parser.add_argument('--lower', type=int, help='Lower bound for triangle count')
    parser.add_argument('--upper', type=int, help='Upper bound for triangle count')
    
    args = parser.parse_args()
    
    # Validate lex_option
    if args.lex_option not in ["lex-least", "lex-greatest", "no-lex"]:
        parser.error("lex_option must be one of: lex-least, lex-greatest, no-lex")
    
    # Validate bounds
    if (args.lower is None) != (args.upper is None):
        parser.error("Both lower and upper bounds must be provided together or omitted")
    
    generate(args.n, args.block, args.lower, args.upper, args.lex_option)
