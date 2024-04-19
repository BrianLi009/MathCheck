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
    -s: Cubing with parallel solving on one node
    -l: Cubing with parallel solving across different nodes
    <n>: Order of the instance/number of vertices in the graph
    <c>: Percentage of vertices that are color 1 (default: 0.5)
    <m>: Number of MCTS simulations (default: 2)
    <d>: Cubing cutoff criteria, choose d(depth) as default #d, v (default: d)
    <dv>: By default cube to depth 5 (default: 5)
    <nodes>: Number of nodes to submit to if using -l (default: 1)
" && exit

# Option Handling
solve_mode=""
while getopts "nsl" opt
do
    case $opt in
        n) solve_mode="no_cubing" ;;
        s) solve_mode="sin_cubing" ;;
        l) solve_mode="mul_cubing" ;;
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
o=${3:-1} #definition used
m=${4:-2} #Num of MCTS simulations. m=0 activate march
d=${5:-d} #Cubing cutoff criteria, choose d(depth) as default #d, v
dv=${6:-5} #By default cube to depth 5
nodes=${7:-1} #Number of nodes to submit to if using -l

di="${1}-${c}-${o}-${m}-${d}-${dv}-${nodes}-$(date +%Y%m%d%H%M%S)"

# Dependency Setup
./dependency-setup.sh

mkdir $di

# Generate Instance
./generate-instance.sh $n $c $o
cp constraints_${n}_${c}_${o} $di

# Solve Based on Mode
case $solve_mode in
    "no_cubing")
        echo "No cubing, just solve"
        
        echo "Simplifying $f for 10000 conflicts using CaDiCaL+CAS"
        ./simplification/simplify-by-conflicts.sh ${di}/constraints_${n}_${c}_${d} $n 10000

        echo "Solving $f using MapleSAT+CAS"
        ./solve-verify.sh $n ${di}/constraints_${n}_${c}_${d}.simp
        ;;
    "sin_cubing")
        echo "Cubing and solving in parallel on local machine"
        python parallel-solve.py $n ${di}/constraints_${n}_${c}_${d} $m $d $dv
        ;;
    "mul_cubing")
        echo "Cubing and solving in parallel on Compute Canada"
        python parallel-solve.py $n ${di}/constraints_${n}_${c}_${d} $m $d $dv False
        found_files=()

        # Populate the array with the names of files found by the find command

        while IFS= read -r -d $'\0' file; do
        found_files+=("$file")
        done < <(find "${di}" -mindepth 1 -regex ".*\.\(00\|01\|10\|11\)$" -print0)

        
        # Calculate the number of files to distribute names across and initialize counters
        total_files=${#found_files[@]}
        files_per_node=$(( (total_files + nodes - 1) / nodes )) # Ceiling division to evenly distribute
        counter=0
        file_counter=1

        # Check if there are files to distribute
        if [ ${#found_files[@]} -eq 0 ]; then
            echo "No files found to distribute."
            exit 1
        fi

        # Create $node number of files and distribute the names of found files across them
        for file_name in "${found_files[@]}"; do
            # Determine the current output file to write to
            output_file="${di}/node_${file_counter}.txt"
            submit_file="${di}/node_${file_counter}.sh"
            cat <<EOF > "$submit_file"
#!/bin/bash
#SBATCH --account=rrg-cbright
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=0
#SBATCH --time=1-00:00
#SBATCH --output=${di}/node_${file_counter}_%N_%j.out

module load python/3.10

python parallel-solve.py $n $output_file $m $d $dv

EOF
            
            # Write the current file name to the output file
            echo "$file_name" >> "$output_file"
            
            # Update counters
            ((counter++))
            if [ "$counter" -ge "$files_per_node" ]; then
                counter=0
                ((file_counter++))
            fi
        done


        ;;
esac



