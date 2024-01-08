#!/bin/bash

# Initialize a flag variable
c_flag=0

# Parse command-line options
while getopts 'c' flag; do
    case "${flag}" in
        c) c_flag=1 ;;
        *) echo "Unexpected option ${flag}" ;;
    esac
done

# Shift processed options away
shift $((OPTIND -1))

# Now handle the positional arguments
n=$1   # order
f=$2   # instance file name
d=$3   # directory to store into
v=$4   # num of cubes to cutoff at initial depth
a=$5   # num of cubes to cutoff at initial depth for each proceeding cubing call
ins=${6:-$f}
nodes=${7:-1}   # number of nodes to use

mkdir -p $d/$v/$n-cubes

di="$d/$v"

if [ -e "$f.drat" ]; then
    grep 't' $f.drat | cut -d' ' -f 2- >> $ins
    lines=$(wc -l < "$ins")
    sed -i -E "s/p cnf ([0-9]*) ([0-9]*)/p cnf \1 $((lines-1))/" "$ins"
fi

if [ "$c_flag" -eq 1 ]; then
    echo "not the first layer, cubing sequentially..."
    ./gen_cubes/cube.sh -a $n $ins $v $di
else
    ./gen_cubes/cube.sh -a $n $ins $v $di
fi

files=$(ls $d/$v/$n-cubes/*.cubes)
highest_num=$(echo "$files" | awk -F '[./]' '{print $(NF-1)}' | sort -nr | head -n 1)
echo "currently the cubing depth is $highest_num"
cube_file=$d/$v/$n-cubes/$highest_num.cubes
cube_file_name=$(echo $cube_file | sed 's:.*/::')
new_cube=$((highest_num + 1))

numline=$(< $cube_file wc -l)
new_index=$((numline))

solvefile=$cube_file-solve.sh

for i in $(seq 1 $new_index); do
    command1="./gen_cubes/apply.sh $f $cube_file $i > $cube_file$i.adj"
    command2="./simplification/simplify-by-conflicts.sh $cube_file$i.adj $n 10000"
    command3="./maplesat-solve-verify.sh $n $cube_file$i.adj.simp"
    child_instance="$cube_file$i.adj.simp"
    file="$cube_file$i.adj.simp.log"
    vfile="$cube_file$i.adj.simp.verify"
    command4="if ! grep -q 'UNSATISFIABLE' '$file'; then ./3-cube-merge-solve-iterative-cc.sh -c $n $child_instance '$d/$v-$i' $a $a; elif grep -q 'VERIFIED' '$vfile'; then find $cube_file$i.* | grep -v '$cube_file$i.adj.simp.verify\|$cube_file$i.adj.simp.log' | xargs rm; fi"
    command="$command1 && $command2 && $command3 && $command4"
    echo $command >> $solvefile
done

# given n nodes, we create n solvefile, and n slurm submission script
# then execute parallel --will-cite solvefile inside the slurm script
#!/bin/bash
# Extract directory from solvefile path
dir=$(dirname "$solvefile")
# Extract base filename without path
base=$(basename "$solvefile")

split_lines=$(wc -l < "$solvefile")       # Count the number of lines in the file

lines_per_file=$((split_lines / nodes + (split_lines % nodes > 0)))  # Calculate lines per file

# Shuffle and split the file, storing output files in the same directory
shuf "$solvefile" | split -l "$lines_per_file" - "$dir/${base}_"

if [ "$c_flag" -eq 1 ]; then
    # Code to execute when -c flag is used
    echo "run command in parallel without submitting slurm file"
    parallel --will-cite $solvefile
else
    echo "submit slurm files"
    # Rename output files to the desired format
    i=1
    for file in "$dir/${base}_"*; do
        mv "$file" "$dir/${base}-$i.commands"
        echo "creating slurm files"
        cat > "$dir/script_$i.sh" <<- EOM
#!/bin/bash
#SBATCH --account=rrg-cbright
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=0
#SBATCH --time=06:00:00

local_dir=\$SLURM_TMPDIR
cp /project/rrg-cbright/zhengyu/IJCAI/PhysicsCheckp/constraints_${n}_0.5 \$local_dir/
cp /project/rrg-cbright/zhengyu/IJCAI/PhysicsCheckp/${dir}/*.cubes \$local_dir/

module load python/3.10
parallel --will-cite < ${dir}/${base}-$i.commands

cp \$local_dir}/*.log /project/rrg-cbright/zhengyu/IJCAI/PhysicsCheckp/${dir}
cp \$local_dir}/*.verify /project/rrg-cbright/zhengyu/IJCAI/PhysicsCheckp/${dir}
EOM
        i=$((i+1))
    done
  
fi
