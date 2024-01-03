#!/bin/bash

# Ensure necessary parameters are provided on the command-line
if [ -z $5 ]
then
	echo "Need order, instance filename, number of edge variables to remove, depth, cube index, folder to work in, and optionally a simplification mode parameter"
	exit
fi

n=$1 # Order
f=$2 # Instance filename
i=$3 # Depth
c=$4 # Cube index
t=$5 # folder to work in

m=$((n*(n-1)/2)) # Number of edge variables in instance
dir=$t/$n-cubes # Directory to store cubes
logdir=$t/$n-log # Directory to store logs

if [ ! -d "log" ]; then
  mkdir log
fi

# Get the c-th cube
cubeline=`head $dir/$((i-1)).cubes -n $c | tail -n 1`
echo "Processing $cubeline..."
./gen_cubes/apply.sh $f $dir/$((i-1)).cubes $c > $dir/$((i-1)).cubes$c
#command="python -u alpha-zero-general/main.py $dir/$((i-1)).cubes$c -d 1 -m $m -o $dir/$((i-1)).cubes$c.cubes -order $n -numMCTSSims 10 -prod | tee $logdir/$((i-1)).cubes$c.log"
command="python ams_no_mcts.py $dir/$((i-1)).cubes$c -d 1 -m $m -o $dir/$((i-1)).cubes$c.cubes | tee $logdir/$((i-1)).cubes$c.log"
echo $command
eval $command
# Adjoin the newly generated cubes to the literals in the current cube
cubeprefix=`head $dir/$((i-1)).cubes -n $c | tail -n 1 | sed -E 's/(.*) 0/\1/'`
sed -E "s/^a (.*)/$cubeprefix \1/" $dir/$((i-1)).cubes$c.cubes > $dir/$i-$c.cubes
rm $dir/$((i-1)).cubes$c