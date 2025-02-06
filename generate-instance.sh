#!/bin/bash

[ "$1" = "-h" -o "$1" = "--help" -o "$#" -lt 1 -o "$#" -gt 4 ] && echo "
Description:
    Updated on 2023-01-11
    This script call the python file generate.py in gen_instance to generate the SAT encoding for a Kochen Specker candidates. Such candidate satisfies the following condition:
    1. The graph is squarefree, hence does not contain C4 subgraph
    2. All vertices are part of a triangle
    3. Graph is not 010-colorable (refer to the paper for definition)
    4. Minimum degree of each vertex is 3
    5. We also applied the cubic isomorphism blocking clauses

Usage:
    ./generate-instance.sh n c o [lex-greatest]

Options:
    <n>: the order of the instance/number of vertices in the graph
    <c>: ratio of color-1 vertices to block
    <o>: definition used (1 or 2)
    lex-greatest: (optional) use lex-greatest ordering instead of lex-smallest
    
" && exit

n=$1 #order
c=$2 #ratio of color-1 vertices to block
o=$3 #definition used
lex_opt="" #default to lex-smallest

echo "Debug: Input parameters:"
echo "n=$n, c=$c, o=$o, \$4=$4"

# Check if fourth argument is lex-greatest
if [ "$4" = "lex-greatest" ]; then
    echo "Debug: Setting lex_opt to lex-greatest"
    lex_opt="lex-greatest"
fi

base_name="constraints_${n}_${c}_${o}"
file_name="$base_name"
[ "$lex_opt" = "lex-greatest" ] && file_name="${base_name}_lex_greatest"

echo "Debug: base_name=$base_name"
echo "Debug: file_name=$file_name"

if [ -f "$file_name" ]
then
    echo "instance already generated"
else
    if [ $o -eq 1 ]
    then
        echo "Debug: Calling generate.py with: $n $c $lex_opt"
        python3 gen_instance/generate.py $n $c "$lex_opt" #generate the instance of order n
    else
        echo "using extended definition of KS system..."
        echo "Debug: Calling generate-def2.py with: $n $c $lex_opt"
        python3 gen_instance/generate-def2.py $n $c "$lex_opt" #generate the instance of order n
    fi
fi
