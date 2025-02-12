#!/bin/bash

# Check if a directory name was provided
if [ $# -lt 1 ]; then
  echo "Usage: $0 <directory-name>"
  exit 1
fi

# Change to the specified directory
cd "$1" || exit

# Initialize variables
solving_time=0
verification_time=0
leaf_cubes=0
total_cubes=0
timeouted_cubes=0
sat_time=0
unsat_time=0
unknown_time=0

# Read the timeout parameter
timeout=$2

# Compute Solving Time and Verification Time together
while IFS= read -r file; do
    if [[ "$file" == *.log ]]; then
        # Count as a total cube file
        ((total_cubes++))
        
        # Check if it's a leaf cube (contains SAT or UNSAT)
        if grep -q -E "SAT|UNSAT" "$file"; then
            ((leaf_cubes++))
        else
            # Count as a timeouted cube
            ((timeouted_cubes++))
        fi
        
        # Check for CPU time in the file using both formats
        if grep -q "CPU time" "$file" || grep -q 'c total process time since initialization:' "$file"; then
            # Get CPU time from either format
            time=$(grep -E "CPU time|c total process time since initialization:" "$file" | awk '
                /CPU time/ {total += $(NF-1)}
                /c total process time since initialization:/ {total += $(NF-1)}
                END {print total}
            ')
            solving_time=$(echo "$solving_time + $time" | bc)
            
            # Categorize time based on SAT/UNSAT/Unknown
            if grep -q "UNSAT" "$file"; then
                unsat_time=$(echo "$unsat_time + $time" | bc)
            elif grep -q "SAT" "$file"; then
                sat_time=$(echo "$sat_time + $time" | bc)
            else
                unknown_time=$(echo "$unknown_time + $time" | bc)
            fi
        fi
    elif [[ "$file" == *.verify ]]; then
        # Add to verification time
        time=$(grep 'c verification time:' "$file" | awk '{sum += $4} END {print sum}')
        verification_time=$(echo "$verification_time + $time" | bc)
    fi
done < <(find . -type f \( -name "*.log" -o -name "*.verify" \))

# Count number of nodes in the cubing tree
num_nodes=$(find . -name "*.simplog" | wc -l)

# Compute Cubing Time - check both "Tool runtime" and "c time" formats
cubing_time=$(grep -E 'Tool runtime|c time = ' slurm-*.out | awk '
    /Tool runtime/ {sum += $3}
    /c time = / {sum += $4}
    END {print sum}
')

# Compute Simp Time (now handled in the main loop)
simp_time=$(grep 'c total process time since initialization:' *.simplog | awk '{SUM += $(NF-1)} END {print SUM}' | bc)

# Output the results
echo "Number of nodes in cubing tree: $num_nodes"
echo "Total cubes: $total_cubes"
echo "Leaf cubes: $leaf_cubes"
echo "Timeouted cubes: $timeouted_cubes"
echo "Solving Time: $solving_time"
echo "SAT Time: $sat_time"
echo "UNSAT Time: $unsat_time"
echo "Unknown Time: $unknown_time"
echo "Cubing Time: $cubing_time"
echo "Simp Time: $simp_time"
echo "Verification Time: $verification_time seconds"
