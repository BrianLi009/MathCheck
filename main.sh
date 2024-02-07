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
m=${3:-2} #Num of MCTS simulations. m=0 activate march
d=${4:-d} #Cubing cutoff criteria, choose d(depth) as default #d, n, v
dv=${5:-5} #By default cube to depth 5
nodes=${6:-1} #Number of nodes to submit to if using -l

di="${1}-${c}-${m}-${d}-${dv}-${nodes}-$(date +%Y%m%d%H%M%S)"

# Dependency Setup
./dependency-setup.sh

mkdir $di

# Generate Instance
./generate-instance.sh $n $c
cp constraints_${n}_${c} $di

# Solve Based on Mode
case $solve_mode in
    "no_cubing")
        echo "No cubing, just solve"
        
        echo "Simplifying $f for 10000 conflicts using CaDiCaL+CAS"
        ./simplification/simplify-by-conflicts.sh ${di}/constraints_${n}_${c} $n 10000

        echo "Solving $f using MapleSAT+CAS"
        ./maplesat-solve-verify.sh $n ${di}/constraints_${n}_${c}.simp
        ;;
    "seq_cubing")
        echo "Cubing and solving in parallel on local machine"
        python parallel-solve.py $n ${di}/constraints_${n}_${c} $m $d $dv
        ;;
    "par_cubing")
        echo "Cubing and solving in parallel on Compute Canada"
        python parallel-solve.py $n ${di}/constraints_${n}_${c} $m $d $dv False
        i=1
        find . -regextype posix-extended -regex "./constraints_${n}_${c}[^/]*" ! -regex '.*\.(simplog|ext)$' -print0 | while IFS= read -r -d $'\0' file; do
            echo "Processing $file"
            # Your commands here
        done


        ;;
esac



