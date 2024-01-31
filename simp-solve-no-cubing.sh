#!/bin/bash

n=$1 #order
f=$2 #input file name to solve

echo "Simplifying $f for 10000 conflicts using CaDiCaL+CAS"
./simplification/simplify-by-conflicts.sh $f $n 10000

echo "Solving $f using MapleSAT+CAS"
./maplesat-solve-verify.sh $n $f