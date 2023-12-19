#!/bin/bash

while getopts "p" opt
do
	case $opt in
        p) p="-p" ;;
	esac
done
shift $((OPTIND-1))

n=$1 #order
f=$2 #instance file name
d=$3 #directory to store into
v=$4 #num of var to eliminate during first cubing stage
a=$5 #amount of additional variables to remove for each cubing call
m=$((n*(n-1)/2)) # Number of edge variables in instance

mkdir -p $d/$v

dir="$d/$v"

command="python -u alpha-zero-general/main.py $f -n $v -m $m -o $dir/$v.cubes -order $n -numMCTSSims 30 -prod | tee $dir/$v.log"
echo $command
eval $command

cube_file=$dir/$v.cubes

new_index=$(< $cube_file wc -l)

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

                command="./3-cube-merge-solve-iterative.sh $n $child_instance "$d/$v-$i" $(($v + $a)) $a"
                #for parallization, simply submit the command below using sbatch
                echo $command >> ${n}-iterative.commands
                eval $command
        fi
done