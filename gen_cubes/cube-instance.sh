#!/bin/bash

# Default value for s
s=2
use_s_flag=false

# Parsing the -m flag and its argument
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
if $use_s_flag
then
    command="python -u alpha-zero-general/main.py $dir/$((i-1)).cubes$c -d 1 -m $m -o $dir/$((i-1)).cubes$c.cubes -order $n -prod -numMCTSSims $s | tee $logdir/$((i-1)).cubes$c.log"
else
	#command="python ams_no_mcts.py $dir/$((i-1)).cubes$c -d 1 -m $m -o $dir/$((i-1)).cubes$c.cubes | tee $logdir/$((i-1)).cubes$c.log"
  command="./gen_cubes/march_cu/march_cu $dir/$((i-1)).cubes$c -o $dir/$((i-1)).cubes$c.cubes -d 1 -m $m | tee $logdir/$((i-1)).cubes$c.log"
fi

echo $command
eval $command

# Adjoin the newly generated cubes to the literals in the current cube
cubeprefix=`head $dir/$((i-1)).cubes -n $c | tail -n 1 | sed -E 's/(.*) 0/\1/'`
sed -E "s/^a (.*)/$cubeprefix \1/" $dir/$((i-1)).cubes$c.cubes > $dir/$i-$c.cubes
rm $dir/$((i-1)).cubes$c
