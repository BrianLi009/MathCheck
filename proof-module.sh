#!/bin/bash

n=$1 #order
f=$2 #input file
o=$3 #output .verify file
m=$f #verification mode

# Verify DRAT proof
if [ "$m" = "f" ]; then
    ./drat-trim/drat-trim $f $f.drat -f -b | tee $o
else
    ./drat-trim/drat-trim $f $f.drat -b | tee $o
fi

if ! grep -E "s DERIVATION|s VERIFIED" -q $o
then
	echo "ERROR: Proof not verified"
fi
# Verify trusted clauses
if [ -f "$f.perm" ]; then
	grep 't' $f.drat | ./drat-trim/check-perm.py $n $f.perm| tee $f.permcheck
	if ! grep "VERIFIED" -q $f.permcheck
	then
		echo "ERROR: Trusted clauses not verified"
	fi
fi
