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
# Check if no simplification mode (or mode -m) or at initial depth
if [ -z $s ] || [ "$s" == "-m" ] || (( i == 1 ))
then
	# Adjoin the literals in the current cube to the instance and simplify the resulting instance with CaDiCaL
	./gen_cubes/apply.sh $f $dir/$((i-1)).cubes $c > $dir/$((i-1)).cubes$c
	command="./cadical/build/cadical $dir/$((i-1)).cubes$c $dir/$((i-1)).cubes$c.drat -o $dir/$((i-1)).cubes$c.simp -e $dir/$((i-1)).cubes$c.ext -n -c 1000 > $logdir/$((i-1)).cubes$c.simp"
	echo $command
	eval $command
	
# Check if current cube appears in previous list of cubes
elif grep -q "$cubeline" $dir/$((i-2)).cubes
then
	# Line number of current cube in previous list of cubes
	l=$(grep -n "$cubeline" $dir/$((i-2)).cubes | cut -d':' -f1)

	cp $dir/$((i-2)).cubes$l.simp $dir/$((i-1)).cubes$c.simp
	cp $dir/$((i-2)).cubes$l.ext $dir/$((i-1)).cubes$c.ext
else
	# Parent cube
	parentcube=$(echo "$cubeline" | xargs -n 1 | head -n -2 | xargs)

	# Line number of parent cube
	l=$(grep -n "$parentcube" $dir/$((i-2)).cubes | cut -d':' -f1)

	# Adjoin the literals in the current cube to the simplified parent instance and simplify the resulting instance with CaDiCaL
	command="./gen_cubes/concat-edge-and-apply.sh $n $dir/$((i-2)).cubes$l.simp $dir/$((i-2)).cubes$l.ext $dir/$((i-1)).cubes $c | ./cadical/build/cadical -o $dir/$((i-1)).cubes$c.simp -e $dir/$((i-1)).cubes$c.ext -n -c 10000 > $logdir/$((i-1)).cubes$c.simp"
	echo $command
	eval $command
fi

# Check if simplified instance was unsatisfiable
if grep -q "^0$" $dir/$((i-1)).cubes$c.simp
then
	removedvars=$m # Instance was unsatisfiable so all variables were removed
	echo "  Depth $i instance $c was shown to be UNSAT; skipping"
	head $dir/$((i-1)).cubes -n $c | tail -n 1 > $dir/$i-$c.cubes
	sed 's/a/u/' $dir/$i-$c.cubes -i # Mark cubes that have been shown to be unsatisfiable with 'u'
	unsat=1
else
	# Determine how many edge variables were removed
	removedvars=$(sed -E 's/.* 0 [-]*([0-9]*) 0$/\1/' < $dir/$((i-1)).cubes$c.ext | awk "\$0<=$m" | sort | uniq | wc -l)
fi

# Check if current cube should be split
if (( removedvars <= r ))
then
	echo "  Depth $i instance $c has $removedvars removed edge variables; splitting..."
	# Split this cube by running march_cu on the simplified instance

	command="python -u alpha-zero-general/main.py $dir/$((i-1)).cubes$c.simp -d 1 -m $m -o $dir/$((i-1)).cubes$c.cubes -order $n -numMCTSSims 10 -prod | tee $logdir/$((i-1)).cubes$c.log"
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