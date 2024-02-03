#!/bin/bash

while getopts "s" opt
do
	case $opt in
        s) s="-s" ;;
	esac
done
shift $((OPTIND-1))

n=$1 #order
f=$2 #instance file name

[ "$1" = "-h" -o "$1" = "--help" -o "$#" -ne 2 ] && echo "
Description:
    Script for solving and generating drat proof for instance

Usage:
    ./maplesat-solve-verify.sh n f e

Options:
    [-l]: generate learnt clauses
    <n>: the order of the instance/number of vertices in the graph
    <f>: file name of the CNF instance to be solved
" && exit

./simplification/simplify-by-conflicts.sh -s $f $n 10000 | tee $f.simplog

./maplesat-ks/simp/maplesat_static $f.simp $f.simp.drat -perm-out=$f.simp.perm -exhaustive=$f.simp.exhaust -order=$n -no-pre -minclause -max-proof-size=7168 -unembeddable-check=17 -unembeddable-out="$f.simp.nonembed" | tee $f.simp.log

if ! grep -q "UNSAT" "$f.simp.log" || [ "$s" == "-s" ]; then
    echo "instance not solved, no need to verify unless learnt clause or skipping verification"
else
    ./proof-module.sh $n $f $f.simp.verify
fi
