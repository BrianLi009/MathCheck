#!/bin/bash

# The SAT solver to use to verify the correctness of the cubes
SOLVER=minisat

# Ensure parameters are given on the command-line
if [ -z $2 ]
then
	echo "Need filename of cubes to verify and order of instance"
	exit
fi

n=$2 # Order of graph
maxvar=$(grep -Eo '[0-9]+' $1 | sort -rn | head -n 1) # Largest variable in cubes

# Ensure all cube variables are edge variables
if (( n*(n-1)/2 < maxvar ))
then
	echo "ERROR: Cube file contains a non-edge variable"
	exit
fi

tmpfile=$(mktemp)

# Generate a SAT instance by negating the file containing the disjunction of cubes
echo "p cnf $maxvar $(wc -l < $1)" > $tmpfile
sed -e 's/ / -/g' -e 's/--//g' -e 's/-0/0/g' -e 's/a //g' -e 's/u //g' $1 >> $tmpfile

# Ensure cubes exhaustively partition the space
# This occurs exactly when the negation of the disjunction of cubes is UNSAT
if [[ $($SOLVER $tmpfile) =~ "UNSAT" ]]
then
	echo "Cubes exhaustively partition the search space"
else
	echo "ERROR: Cubes do not exhaustively partition the search space"
fi

rm $tmpfile
