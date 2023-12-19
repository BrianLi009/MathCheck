#!/bin/bash

# Ensure necessary parameters are provided on the command-line
if [ -z $5 ]
then
	echo "Need order, instance filename, number of edge variables to remove, depth, cube index, folder to work in, and optionally a simplification mode parameter"
	exit
fi

n=$1 # Order
f=$2 # Instance filename
r=$3 # Number of free edge variables to remove
i=$4 # Depth
c=$5 # Cube index
t=$6 #folder to work in

m=$((n*(n-1)/2)) # Number of edge variables in instance
dir=$t/$n-cubes # Directory to store cubes
logdir=$t/$n-log # Directory to store logs

if [ ! -d "log" ]; then
  mkdir log
fi

# Get the c-th cube
cubeline=`head $dir/$((i-1)).cubes -n $c | tail -n 1`
echo "Processing $cubeline..."

# Check if current cube should be split
if (( removedvars <= r ))
then
	echo "  Depth $i instance $c has $removedvars removed edge variables; splitting..."
	# Split this cube by running march_cu on the simplified instance

	#Add 3 options here:
	command="python -u alpha-zero-general/main.py $dir/$((i-1)).cubes$c.simp -d 1 -m $m -o $dir/$((i-1)).cubes$c.cubes -order $n -numMCTSSims 100 -prod | tee $logdir/$((i-1)).cubes$c.log"
	echo $command
	eval $command
	echo "c Depth $i instance $c has $removedvars removed edge variables" >> $logdir/$((i-1)).cubes$c.log
	# Adjoin the newly generated cubes to the literals in the current cube
	cubeprefix=`head $dir/$((i-1)).cubes -n $c | tail -n 1 | sed -E 's/(.*) 0/\1/'`
	sed -E "s/^a (.*)/$cubeprefix \1/" $dir/$((i-1)).cubes$c.cubes > $dir/$i-$c.cubes
elif [ -z $unsat ]
then
	# Current cube should not be split
	echo "  Depth $i instance $c has $removedvars removed edge variables; not splitting"
	head $dir/$((i-1)).cubes -n $c | tail -n 1 > $dir/$i-$c.cubes
fi
# Delete simplified instance if not needed anymore
if [ -z $s ] || [ "$s" == "-m" ]
then
	rm $dir/$((i-1)).cubes$c.simp 2> /dev/null
	rm $dir/$((i-1)).cubes$c.ext 2> /dev/null
fi
