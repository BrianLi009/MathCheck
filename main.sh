#!/bin/bash

# Description and Usage
[ "$1" = "-h" -o "$1" = "--help" ] && echo "
Description:
    This is a driver script that handles generating the SAT encoding, simplifying the instance with CaDiCaL+CAS,
    solving the instance with MapleSAT+CAS, then finally determine if a KS system exists for a certain order through embeddability checking.

Usage:
    ./main.sh <option> n [c] [r] [a]

Options:
    -n: No cubing, just solve
    -s: Cubing with sequential solving
    -l: Cubing with parallel solving
    <n>: Order of the instance/number of vertices in the graph
    <c>: Percentage of vertices that are color 1 (default: 0.5)
    <r>: Number of variables to remove in cubing (default: 0, assuming no cubing needed)
    <a>: Amount of additional variables to remove for each cubing call (default: 0)
" && exit

# Option Handling
solve_mode=""
while getopts "nsl" opt
do
    case $opt in
        n) solve_mode="no_cubing" ;;
        s) solve_mode="seq_cubing" ;;
        l) solve_mode="par_cubing" ;;
        *) echo "Invalid option: -$OPTARG. Use -n, -s, or -l. Use -h or --help for help" >&2
           exit 1 ;;
    esac
done
shift $((OPTIND-1))

# Input Parameters
if [ -z "$1" ]
then
    echo "Need instance order (number of vertices), use -h or --help for further instruction"
    exit
fi

n=$1 # Order
c=${2:-0.5} # Color percentage
r=${3:-0} # Number of variables to eliminate during first cubing stage
a=${4:-0} # Amount of additional variables to remove for each cubing call

# Dependency Setup
./dependency-setup.sh

# Check if Instance Already Solved
dir="."

# Generate Instance
./generate-instance.sh $n $c

# Solve Based on Mode
case $solve_mode in
    "no_cubing")
        echo "No cubing, just solve"
        ./simp-solve-no-cubing.sh $n constraints_${n}_${c}
        ;;
    "seq_cubing")
        echo "Cubing with sequential solving"
        ./simplification/simplify-by-conflicts.sh constraints_${n}_${c} $n 10000
        ./cube-solve.sh $n constraints_${n}_${c}.simp $r $a
        ;;
    "par_cubing")
        echo "Cubing with parallel solving"
        ./simplification/simplify-by-conflicts.sh constraints_${n}_${c} $n 10000
        ./prepare-parallel-solve.sh $n constraints_${n}_${c}.simp $r $a 50
        ;;
    *)
        echo "No solving mode selected, use -n by default"
        ./simp-solve-no-cubing.sh $n constraints_${n}_${c}
        ;;
esac

