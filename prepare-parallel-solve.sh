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

n=$1 #order
f=$2 #filename
d=$3 #directory
nodes=$4 #number of nodes to submit to in total

if $use_s_flag
then
    ./gen_cubes/cube.sh -s $n $f $nodes $d
else
    ./gen_cubes/cube.sh $n $f $nodes $d
fi




