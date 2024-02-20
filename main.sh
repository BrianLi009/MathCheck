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
d=${4:-d} #Cubing cutoff criteria, choose d(depth) as default #d, v
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
        ./solve-verify.sh $n ${di}/constraints_${n}_${c}.simp
        ;;
    "seq_cubing")
        echo "Cubing and solving in parallel on local machine"
        python parallel-solve.py $n ${di}/constraints_${n}_${c} $m $d $dv
        ;;
    "par_cubing")
        echo "Cubing and solving in parallel on Compute Canada"
        python parallel-solve.py $n ${di}/constraints_${n}_${c} $m $d $dv False
        found_files=()

        # Populate the array with the names of files found by the find command
        while IFS= read -r -d $'\0' file; do
        found_files+=("$file")
        done < <(find "${di}" ! -name '*.drat' ! -name '*.ext' ! -name '*.ext1' ! -name '*.simp1' ! -name '*.simplog' ! -name '*.cubes' -print0)

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



