#!/bin/bash

n=$1 #order
f=$2 #instance file name
d=$3 #directory to store into
v=$4 #num of cubes to cutoff at initial depth
a=$5 #num of cubes to cutoff at initial depth for each proceeding cubing call
ins=${6:-$f}

#we want the script to: cube, for each cube, submit sbatch to solve, if not solved, call the script again

mkdir -p $d/$v/$n-cubes

di="$d/$v"

if [ -e "$f.drat" ]; then
    grep 't' $f.drat | cut -d' ' -f 2- >> $ins
    lines=$(wc -l < "$ins")
    sed -i -E "s/p cnf ([0-9]*) ([0-9]*)/p cnf \1 $((lines-1))/" "$ins"
fi

./gen_cubes/cube.sh -a -p $n $ins $v $di
#./gen_cubes/cube.sh -a $n $ins $v $di

files=$(ls $d/$v/$n-cubes/*.cubes)
highest_num=$(echo "$files" | awk -F '[./]' '{print $(NF-1)}' | sort -nr | head -n 1)
echo "currently the cubing depth is $highest_num"
cube_file=$d/$v/$n-cubes/$highest_num.cubes
cube_file_name=$(echo $cube_file | sed 's:.*/::')
new_cube=$((highest_num + 1))

numline=$(< $cube_file wc -l)
new_index=$((numline))

solvefile=$cube_file-solve.sh

for i in $(seq 1 $new_index) #1-based indexing for cubes
    do
        command1="./gen_cubes/apply.sh $f $cube_file $i > $cube_file$i.adj"
        command2="./simplification/simplify-by-conflicts.sh $cube_file$i.adj $n 10000"
        command3="./maplesat-solve-verify.sh $n $cube_file$i.adj.simp"
        child_instance="$cube_file$i.adj.simp"
        file="$cube_file$i.adj.simp.log"
        vfile="$cube_file$i.adj.simp.verify"
        command4="if ! grep -q 'UNSATISFIABLE' '$file'; then ./3-cube-merge-solve-iterative-cc.sh $n $child_instance '$d/$v-$i' $a $a; elif grep -q 'VERIFIED' '$vfile'; then find $cube_file$i.* | grep -v '$cube_file$i.adj.simp.verify\|$cube_file$i.adj.simp.log' | xargs rm; fi"
        command="$command1 && $command2 && $command3 && $command4"
        echo $command >> $solvefile
    done

parallel --will-cite < $solvefile