#!/bin/bash

[ "$1" = "-h" -o "$1" = "--help" -o "$#" -lt 1 -o "$#" -gt 3 ] && echo "
Description:
    Updated on 2023-01-11
    This script call the python file generate.py in gen_instance to generate the SAT encoding for a Kochen Specker candidates. Such candidate satisfies the following condition:
    1. The graph is squarefree, hence does not contain C4 subgraph
    2. All vertices are part of a triangle
    3. Graph is not 010-colorable (refer to the paper for definition)
    4. Minimum degree of each vertex is 3
    5. We also applied the cubic isomorphism blocking clauses

Usage:
    ./generate-instance.sh n m

Options:
    <n>: the order of the instance/number of vertices in the graph
    <m>: (optional) additional parameter
    
" && exit

n=$1 #order
c=${2:-0.5} #ratio of color-1 vertices to block
o=${3:-1} #assume using definition 1, can use definition 2 as well

if [ -f constraints_$n_$c ]
then
    echo "instance already generated"
else
    if [ $o -eq 1 ]
    then
        python3 gen_instance/generate.py $n $c 1 #generate the instance of order n
    else
        echo "using extended finition of KS system..."
        python3 gen_instance/generate-def2.py $n $c 2 #generate the instance of order n
    fi
fi
