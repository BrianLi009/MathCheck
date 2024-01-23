#!/bin/bash

n=$1 #order
s=$2 #time to simplify
d=$3 #directory
c1=$4 #number of cubes initially
c2=$4 #number of cubes for deeper layers
nodes=$5 #number of nodes to submit to in total

./generate-instance.sh $n
./generate-instance.sh $n 0
./simplification/simplify.sh constraints_${n}_0 $n $s
./simplification/simplify.sh constraints_${n}_0.5 $n $s

./cube-solve-cc.sh $n constraints_${n}_0.5.simp $d $c1 $c2 constraints_${n}_0.simp
