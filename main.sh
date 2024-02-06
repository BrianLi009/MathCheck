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
d=${4:-d} #Cubing cutoff criteria, choose d(depth) as default
dv=${5:-5} #By default cube to depth 5
nodes=${6:-1} #Number of nodes to submit to if using -l

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
        
        echo "Simplifying $f for 10000 conflicts using CaDiCaL+CAS"
        ./simplification/simplify-by-conflicts.sh constraints_${n}_${c} $n 10000

        echo "Solving $f using MapleSAT+CAS"
        ./maplesat-solve-verify.sh $n constraints_${n}_${c}.simp
        ;;
    "seq_cubing")
        echo "Cubing and solving in parallel on local machine"
        python parallel-solve.py $n constraints_${n}_${c} $m True $d $dv
        ;;
    "par_cubing")
        echo "Cubing and solving in parallel on Compute Canada"
        python parallel-solve.py $n constraints_${n}_${c} $m False n $nodes
        i=1
        for file in constraints_${n}_${c}*.simp; do
            cat <<EOF > "script_${i}.sh"
#!/bin/bash
#SBATCH --account=rrg-cbright
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=0
#SBATCH --time=1-00:00

module load python/3.10

python parallel-solve.py ${n} $file $m 'True' $d $dv

EOF
    i=$((i + 1))
    done
        ;;
    *)
        echo "No solving mode selected, use -n by default"
        echo "Simplifying $f for 10000 conflicts using CaDiCaL+CAS"
        ./simplification/simplify-by-conflicts.sh constraints_${n}_${c} $n 10000

        echo "Solving $f using MapleSAT+CAS"
        ;;
esac

