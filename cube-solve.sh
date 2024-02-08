#!/bin/bash

n=$1 #order
f=$2 #instance file name
v=$3 #num of cubes to cutoff at initial depth
a=$4 #num of cubes to cutoff at initial depth for each proceeding cubing call

d=${f}-d

mkdir -p $d/$v/$n-cubes

di="$d/$v"
./gen_cubes/cube.sh -a $n $f $v $di

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
        command="$command1 && $command2"
        echo $command >> $d/$v/solve.commands
        echo $command
        eval $command1
        eval $command2
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

                command="./cube-solve.sh $n $child_instance "$d/$v-$i" $a $a"
                #for parallization, simply submit the command below using sbatch
                echo $command >> ${n}-iterative.commands
                eval $command
        fi
done