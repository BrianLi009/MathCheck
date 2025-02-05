#!/bin/bash

show_help() {
    cat << EOF
Description:
    Driver script for SAT encoding generation, instance simplification (CaDiCaL+CAS),
    solving (MapleSAT+CAS), and KS system existence verification through embeddability checking.

Usage:
    ./main.sh -m=MODE [OPTIONS] ORDER

Modes (-m):
    none     No cubing, just solve
    single   Cubing with parallel solving on one node
    multi    Cubing with parallel solving across different nodes

Required:
    ORDER                   Number of vertices in the graph

Options:
    -m, --mode=MODE        Solving mode (required)
    -c, --color=FLOAT      Color percentage (default: 0.5)
    -o, --def=INT         Definition used (default: 1)
    -s, --sims=INT         Number of MCTS simulations (default: 2)
    -d, --criteria=CHAR    Cubing cutoff criteria: 'd' for depth, 'v' for vertices (default: d)
    -v, --value=INT        Cubing depth/vertex value (default: 5)
    -n, --nodes=INT        Number of nodes for multi mode (default: 1)
    -h, --help            Show this help message

Solver Options:
    --skip-verify, -S      Skip verification step
    --cadical, -C          Use CaDiCal solver (default: MapleSAT)
    --no-pseudo, -P        Disable pseudo check
    --lex-greatest, -L     Use lex-greatest ordering (default: lex-smallest)
    --orbit=VALUE, -O=VALUE Set orbit value
    --no-unembeddable, -U  Disable unembeddable check

Examples:
    ./main.sh -m=single 10
    ./main.sh --mode=single --color=0.6 --def=2 --sims=3 10
    ./main.sh -m=multi -n=4 10
EOF
    exit 0
}

# Default values
mode=""
color_pct=0.5
definition=1
mcts_sims=2
cutoff_criteria="d"
cutoff_value=5
num_nodes=1
# Add new solver-related defaults
solver_skip_verify=false
solver_use_cadical=false
solver_disable_pseudo=false
solver_lex_greatest=false
solver_orbit_val=""
solver_disable_unembeddable=false

# Parse long and short options
while [ $# -gt 0 ]; do
    case "$1" in
        --mode=*|-m=*)
            mode="${1#*=}"
            ;;
        --color=*|-c=*)
            color_pct="${1#*=}"
            ;;
        --def=*|-o=*)
            definition="${1#*=}"
            ;;
        --sims=*|-s=*)
            mcts_sims="${1#*=}"
            ;;
        --criteria=*|-d=*)
            cutoff_criteria="${1#*=}"
            ;;
        --value=*|-v=*)
            cutoff_value="${1#*=}"
            ;;
        --nodes=*|-n=*)
            num_nodes="${1#*=}"
            ;;
        --skip-verify|-S)
            solver_skip_verify=true
            ;;
        --cadical|-C)
            solver_use_cadical=true
            ;;
        --no-pseudo|-P)
            solver_disable_pseudo=true
            ;;
        --lex-greatest|-L)
            solver_lex_greatest=true
            ;;
        --orbit=*|-O=*)
            solver_orbit_val="${1#*=}"
            ;;
        --no-unembeddable|-U)
            solver_disable_unembeddable=true
            ;;
        -h|--help)
            show_help
            ;;
        -*)
            echo "Error: Unknown option: $1" >&2
            exit 1
            ;;
        *)
            # First non-option argument is ORDER
            if [ -z "$order" ]; then
                order="$1"
            else
                echo "Error: Unexpected argument: $1" >&2
                exit 1
            fi
            ;;
    esac
    shift
done

# Validate required parameters
if [ -z "$order" ]; then
    echo "Error: ORDER parameter is required"
    echo "Use -h for help"
    exit 1
fi

if [ -z "$mode" ]; then
    echo "Error: Mode (-m) is required"
    echo "Use -h for help"
    exit 1
fi

# Validate mode
case $mode in
    "none"|"single"|"multi") ;;
    *) echo "Error: Invalid mode. Use none, single, or multi"; exit 1 ;;
esac

# Create unique directory for this run
dir_name="${order}-${color_pct}-${definition}-${mcts_sims}-${cutoff_criteria}-${cutoff_value}-${num_nodes}-$(date +%Y%m%d%H%M%S)"

# Dependency Setup
./dependency-setup.sh

mkdir $dir_name

# Convert solver_lex_greatest to lex_opt for generate-instance.sh
lex_opt=""
[ "$solver_lex_greatest" = true ] && lex_opt="lex-greatest"

# Generate Instance
./generate-instance.sh $order $color_pct $definition "$lex_opt"
f=constraints_${order}_${color_pct}_${definition}
[ "$solver_lex_greatest" = true ] && f=${f}_lex_greatest
cp $f $dir_name

# Calculate number of edge variables
edge_vars=$((order * (order-1) / 2))

# Construct solver options string
solver_opts_str=""
# Skip verification (-s)
[ "$solver_skip_verify" = true ] && solver_opts_str="$solver_opts_str -s"
# Use CaDiCaL solver (-c)
[ "$solver_use_cadical" = true ] && solver_opts_str="$solver_opts_str -c"
# Disable pseudo check (-p)
[ "$solver_disable_pseudo" = true ] && solver_opts_str="$solver_opts_str -p"
# Use lex-greatest ordering (-l)
[ "$solver_lex_greatest" = true ] && solver_opts_str="$solver_opts_str -l"
# Set orbit value (-o)
[ -n "$solver_orbit_val" ] && solver_opts_str="$solver_opts_str -o $solver_orbit_val"
# Disable unembeddable check (-u)
[ "$solver_disable_unembeddable" = true ] && solver_opts_str="$solver_opts_str -u"

# Solve Based on Mode
case $mode in
    "none")
        echo "No cubing, just solve"
        
        echo "Simplifying $f for 10000 conflicts using CaDiCaL+CAS"
        ./simplification/simplify-by-conflicts.sh $solver_opts_str ${dir_name}/${f} $order 10000

        echo "Solving $f using MapleSAT+CAS"
        ./solve-verify.sh $solver_opts_str $order ${dir_name}/${f}.simp
        ;;
    "single")
        echo "Cubing and solving in parallel on local machine"
        cmd="python3 parallel-solve.py $order ${dir_name}/${f} -m $edge_vars --numMCTS $mcts_sims --cutoff $cutoff_criteria --cutoffv $cutoff_value --solver-options=\"$solver_opts_str\""
        echo "Executing command: $cmd"
        eval $cmd
        ;;
    "multi")
        echo "Cubing and solving in parallel on Compute Canada"
        cmd="python3 parallel-solve.py $order ${dir_name}/${f} -m $edge_vars --numMCTS $mcts_sims --cutoff $cutoff_criteria --cutoffv $cutoff_value --solveaftercube False --solver-options=\"$solver_opts_str\""
        echo "Executing command: $cmd"
        $cmd
        found_files=()

        # Populate the array with the names of files found by the find command

        while IFS= read -r -d $'\0' file; do
        found_files+=("$file")
        done < <(find "${dir_name}" -mindepth 1 -regex ".*\.\(00\|01\|10\|11\)$" -print0)

        
        # Calculate the number of files to distribute names across and initialize counters
        total_files=${#found_files[@]}
        files_per_node=$(( (total_files + num_nodes - 1) / num_nodes )) # Ceiling division to evenly distribute
        counter=0
        file_counter=1

        # Check if there are files to distribute
        if [ ${#found_files[@]} -eq 0 ]; then
            echo "No files found to distribute."
            exit 1
        fi

        # Create $num_nodes number of files and distribute the names of found files across them
        for file_name in "${found_files[@]}"; do
            # Determine the current output file to write to
            output_file="${dir_name}/node_${file_counter}.txt"
            submit_file="${dir_name}/node_${file_counter}.sh"
            cat <<EOF > "$submit_file"
#!/bin/bash
#SBATCH --account=rrg-cbright
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=0
#SBATCH --time=1-00:00
#SBATCH --output=${dir_name}/node_${file_counter}_%N_%j.out

module load python/3.10

python3 parallel-solve.py $order $output_file $mcts_sims $cutoff_criteria $cutoff_value "$solver_opts_str"

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



