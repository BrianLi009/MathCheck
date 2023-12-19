#!/bin/bash

while getopts "l" opt
do
	case $opt in
        l) l="-l" ;;
	esac
done
shift $((OPTIND-1))

n=$1 #order
f=$2 #instance file name

[ "$1" = "-h" -o "$1" = "--help" -o "$#" -ne 2 ] && echo "
Description:
    Script for solving and generating drat proof for instance

Usage:
    ./solve-verify.sh n f e

Options:
    [-l]: generate learnt clauses
    <n>: the order of the instance/number of vertices in the graph
    <f>: file name of the CNF instance to be solved
    <e>: file name to output exhaustive SAT solutions
" && exit

if [ "$l" == "-l" ]
then
    echo "CaDiCaL will output short learnt clauses"
    ./cadical-ks/build/cadical-ks $f $f.drat --order $n --unembeddable-check 17 --perm-out $f.perm --no-binary | tee $f.log
else
    ./cadical-ks/build/cadical-ks $f $f.drat --order $n --unembeddable-check 17 --perm-out $f.perm --no-binary | tee $f.log
fi

if ! grep -q "UNSAT" "$f.log"; then
        ./proof-module.sh $n $f $f.verify f
else
        ./proof-module.sh $n $f $f.verify
fi
