#!/bin/bash

# Check for the -s flag and its associated value
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

n=$1 # Order
f=$2 # Instance filename
r=$3 # Number of cubes cutoff
t=$4 #directory to work in

echo $n
echo $f 
echo $r 
echo $t 

m=$((n*(n-1)/2)) # Number of edge variables in instance
dir=$t/$n-cubes # Directory to store cubes
logdir=$t/$n-log # Directory to store logs
mkdir -p $dir
mkdir -p $logdir

# Check that instance exists
if [ ! -s $f ]
then
    echo "File $f must exist and be nonempty"
    exit
fi

# Get starting depth
if [ -z $6 ]
then
    # Start from depth 0 by default
    d=0
else
    d=$6
fi

# Get ending depth
if [ -z $7 ]
then
    # Default finish depth is maximum possible
    e=$((n*(n-1)/2))
else
    e=$7
fi


# Solve initial depth if d is 0 and the top-level cube file doesn't exist
if [ "$d" == "0" ]
then
	if [ ! -s $dir/0.cubes ]
	then
		if $use_s_flag
		then
			echo "Number of simulations set to $s"
			command="python -u alpha-zero-general/main.py $f -d 1 -m $m -o $dir/0.cubes -order $n -prod -numMCTSSims $s | tee $logdir/0.log"
		else
			#command="python ams_no_mcts.py $f -d 1 -m $m -o $dir/0.cubes | tee $logdir/0.log"
			command="./gen_cubes/march_cu/march_cu $f -o $dir/0.cubes -d 1 -m $m | tee $logdir/0.log"
		fi
	echo $command
	eval $command
	fi
	d=1
fi

# Solve depths d to e
for i in $(seq $d $e)
do
	if [ ! -f $dir/$((i-1)).cubes ]
	then
		echo "$dir/$((i-1)).cubes doesn't exist; stopping"
		break
	fi

	# Clear cube/commands files at depth i if it already exists
	rm $dir/$i.cubes 2> /dev/null
	rm $dir/$i.commands 2> /dev/null

	# Number of cubes at the previous depth
	numcubes=`wc -l < $dir/$((i-1)).cubes`
	echo "$numcubes cubes in $dir/$((i-1)).cubes"

	# Stop cubing when number of cubes exceed cutoff
	if (( $numcubes > $r ))
	then
		echo "reached number of cubes cutoff"
		# Remove cubes marked as unsatisfiable from last cube file
		sed -i '/^u/d' $dir/$((i-1)).cubes
		break
	fi

	# Generate a new instance for every cube generated from the previous depth
	for c in `seq 1 $numcubes`
	do
		# Get the c-th cube
		cubeline=`head $dir/$((i-1)).cubes -n $c | tail -n 1`

		echo "$n $f $r $i $c $t"
		if $use_s_flag
		then
			command="./gen_cubes/cube-instance.sh -s $s $n $f $i $c $t"
		else
			command="./gen_cubes/cube-instance.sh $n $f $i $c $t"
		fi
		
		echo $command >> $dir/$i.commands
		eval $command 
	done
	for c in `seq 1 $numcubes`
	do
		cat $dir/$i-$c.cubes >> $dir/$i.cubes
	done

	# Remove unnecessary files
	rm $dir/$i.commands 2> /dev/null
	rm $dir/$i-*.cubes 2> /dev/null
	rm $dir/$((i-1)).cubes*.cubes 2> /dev/null

	# Stop cubing when no additional cubes have been generated
	if [ "$(wc -l < $dir/$((i-1)).cubes)" == "$(wc -l < $dir/$i.cubes)" ]
	then
		# Remove cubes marked as unsatisfiable from last cube file
		sed -i '/^u/d' $dir/$i.cubes
		break
	fi
done