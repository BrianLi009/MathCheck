#!/bin/bash

n=$1 #order
f=$2 #instance file name
d=$3 #directory to store into
v=$4 #num of var to eliminate during first cubing stage
a=$5 #amount of additional variables to remove for each cubing call
b=${6:-0} #starting cubing depth, default is 0
c=${7:-} #cube file to build on if exist

mkdir -p $d/$v/$n-cubes

echo "Cubing starting at depth $b"
di="$d/$v"
./gen_cubes/cube.sh -a $n $f $v $di $b

files=$(ls $d/$v/$n-cubes/*.cubes)
highest_num=$(echo "$files" | awk -F '[./]' '{print $(NF-1)}' | sort -nr | head -n 1)
echo "currently the cubing depth is $highest_num"
cube_file=$d/$v/$n-cubes/$highest_num.cubes
cp $(echo $cube_file) .
cube_file=$(echo $cube_file | sed 's:.*/::')
new_cube=$((highest_num + 1))
new_cube_file=$d/$v/$n-cubes/$new_cube.cubes

numline=$(< $cube_file wc -l)
new_index=$((numline))

for i in $(seq 1 $new_index) #1-based indexing for cubes
    do 
        command1="./gen_cubes/apply.sh $f $cube_file $i > $cube_file$i.adj"
        command2="./solve-verify.sh $n $cube_file$i.adj"
        command="$command1 && $command2"
        echo $command >> $d/$v/solve.commands
        echo $command
        eval $command1
        eval $command2
    done

all_solved="T"
for i in $(seq 1 $new_index)
    do
        file="$d/$v/$n-solve/$i-solve.log"
        if grep -q "UNSATISFIABLE" $file 
        then
                #do something
                continue
        elif grep -q "SATISFIABLE" $file
        then
                #do something
                continue
        else
                all_solved="F"
                echo $file is not solved
                sed -n "${i}p" $cube_file >> $new_cube_file
        fi
done

for i in $(seq 1 $new_index)
    do
        file="$cube_file$i.adj.log"
        if grep -q "UNSATISFIABLE" $file 
        then
                #do something
                continue
        elif grep -q "SATISFIABLE" $file
        then
                #do something
                continue
        else
                echo $file is not solved
                child_instance="$cube_file$i.adj"
                echo "further cube instance $child_instance"

                command="./3-cube-merge-solve-iterative.sh $n $child_instance "$d/$v-$i" $(($v + $a)) $a"
                #for parallization, simply submit the command below using sbatch
                echo $command >> ${n}-iterative.commands
                eval $command
        fi
done