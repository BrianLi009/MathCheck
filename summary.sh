#!/bin/bash

# Check if a directory name was provided
if [ $# -eq 0 ]; then
  echo "Usage: $0 <directory-name>"
  exit 1
fi

# Change to the specified directory
cd "$1" || exit

# Initialize variables
solving_time=0
verification_time=0
num_cubes=0

# Compute Solving Time and Verification Time together
while IFS= read -r file; do
    if [[ "$file" == *.log ]]; then
        # Count as a cube file
        ((num_cubes++))
        # Add to solving time
        time=$(grep "CPU time" "$file" | awk '{total += $(NF-1)} END {print total}')
        solving_time=$(echo "$solving_time + $time" | bc)
    elif [[ "$file" == *.verify ]]; then
        # Add to verification time
        time=$(grep 'c verification time:' "$file" | awk '{sum += $4} END {print sum}')
        verification_time=$(echo "$verification_time + $time" | bc)
    fi
done < <(find . -type f \( -name "*.log" -o -name "*.verify" \))

# Compute Cubing Time
cubing_time=$(grep 'Tool runtime' slurm-*.out | awk '{sum += $3} END {print sum}')

# Compute Simp Time
simp_time=$(grep 'c total process time since initialization:' *.simplog | awk '{SUM += $(NF-1)} END {print SUM}' | bc)

# Output the results
echo "Solving Time: $solving_time"
echo "Cubing Time: $cubing_time"
echo "Simp Time: $simp_time"
echo "Verification Time: $verification_time seconds"
echo "# of Cubes: $num_cubes"
