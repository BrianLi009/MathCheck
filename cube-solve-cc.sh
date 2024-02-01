#!/bin/bash

# Check for the -m flag and its associated value
s=2 # Default value for s
use_s_flag=false
while getopts ":s:" opt; do
  case $opt in
    s)
      s=$OPTARG
      use_s_flag=true
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done
shift $((OPTIND-1))

# Now handle the positional arguments
n=$1   # order
f=$2   # instance file name
d=$3   # directory to store into
v=$4   # num of cubes to cutoff at initial depth
a=$5   # num of cubes to cutoff at initial depth for each proceeding cubing call
ins=${6:-$f}

mkdir -p $d/$v/$n-cubes

di="$d/$v"

if $use_s_flag
then
    ./gen_cubes/cube.sh -s $s $n $ins $v $di
else
    ./gen_cubes/cube.sh $n $ins $v $di
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
    command2="./simplification/simplify-by-conflicts.sh -s $cube_file$i.adj $n 10000 | tee $cube_file$i.adj.simplog"
    command3="./maplesat-solve-verify.sh -s $n $cube_file$i.adj.simp"
    child_instance="$cube_file$i.adj.simp"
    file="$cube_file$i.adj.simp.log"
    vfile="$cube_file$i.adj.simp.verify"
    command4="nextfile=$child_instance"
    command="$command1 && $command2 && $command3 && $command4"
    echo $command >> $f.commands
done
