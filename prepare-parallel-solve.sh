#!/bin/bash

n=$1 #order
s=$2 #time to simplify
d=$3 #directory
c1=$4 #number of cubes initially
c2=$4 #number of cubes for deeper layers
nodes=$5 #number of nodes to submit to in total

./generate-instance.sh $n
./generate-instance.sh $n 0
./simplification/simplify.sh constraints_${n}_0 $n $s
./simplification/simplify.sh constraints_${n}_0.5 $n $s

./cube-solve-cc.sh $n constraints_${n}_0.5.simp $d $c1 $c2 constraints_${n}_0.simp

total_lines=$(wc -l < "constraints_${n}_0.5.simp.commands")
((lines_per_file = (total_lines + $nodes - 1) / $nodes))

# Shuffle and split the file
shuf "constraints_${n}_0.5.simp.commands" | split -l "$lines_per_file" - shuffled_

counter=1
for file in shuffled_*; do
    mv "$file" "constraints_${n}_0.5.simp.commands${counter}"
    cat <<EOF > "script_${counter}.sh"
#!/bin/bash
#SBATCH --account=rrg-cbright
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=0
#SBATCH --time=1-00:00

module load python/3.10
python parallel-solve.py $n constraints_${n}_0.5.simp $d $c1 $c2 constraints_${n}_0.5.simp.commands${counter}
EOF

    ((counter++))
done



