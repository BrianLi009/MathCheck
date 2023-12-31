#!/bin/bash

n=$1 #order
f=$2 #instance file name
d=$3 #directory to store into
v=$4 #num of var to eliminate during first cubing stage
a=$5 #amount of additional variables to remove for each cubing call

#we want the script to: cube, for each cube, submit sbatch to solve, if not solved, call the script again

mkdir -p $d/$v/$n-solve
mkdir -p $d/$v/simp
mkdir -p $d/$v/log
mkdir -p $d/$v/$n-cubes

di="$d/$v"
./gen_cubes/cube.sh -a -p $n $f $v $di $z

files=$(ls $d/$v/$n-cubes/*.cubes)
highest_num=$(echo "$files" | awk -F '[./]' '{print $(NF-1)}' | sort -nr | head -n 1)
echo "currently the cubing depth is $highest_num"
cube_file=$d/$v/$n-cubes/$highest_num.cubes
cube_file_name=$(echo $cube_file | sed 's:.*/::')
new_cube=$((highest_num + 1))

numline=$(< $cube_file wc -l)
new_index=$((numline))

for i in $(seq 1 $new_index) #1-based indexing for cubes
    do
        command1="./gen_cubes/apply.sh $f $cube_file $i > $cube_file$i.adj"
        command2="./solve-verify.sh $n $cube_file$i.adj"
        child_instance="$cube_file$i.adj"
        file="$cube_file$i.adj.log"
        command3="if ! grep -q 'UNSATISFIABLE' '$file'; then sbatch $child_instance-cube.sh; fi"
        #sbatch this line
        command4="./3-cube-merge-solve-iterative-cc.sh $n $child_instance '$d/$v-$i' $(($v + $a)) $a $ins"
        command="$command1 && $command2"
        echo "#!/bin/bash" > $child_instance-solve.sh
        echo "#SBATCH --account=rrg-cbright" >> $child_instance-solve.sh
        echo "#SBATCH --time=2-00:00" >> $child_instance-solve.sh
        echo "#SBATCH --mem-per-cpu=4G" >> $child_instance-solve.sh
        echo "#!/bin/bash" > $child_instance-cube.sh
        echo "#SBATCH --account=rrg-cbright" >> $child_instance-cube.sh
        echo "#SBATCH --time=2-00:00" >> $child_instance-cube.sh
        echo "#SBATCH --mem-per-cpu=4G" >> $child_instance-cube.sh
	echo "module load python/3.10" >> $child_instance-cube.sh
        echo $command >> $child_instance-solve.sh
        echo $command3 >> $child_instance-solve.sh
        echo $command4 >> $child_instance-cube.sh
        sbatch $child_instance-solve.sh
    done