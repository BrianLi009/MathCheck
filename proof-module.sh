#!/bin/bash

n=$1 #order
f=$2 #input file
o=$3 #output .verify file
m=$4 #verification mode
lex_opt=$5 #lex-greatest option

# Verify DRAT proof
if [ "$m" = "f" ]; then
	echo "forward verification enabled"
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
	# Pass lex-greatest option to check-perm.py if provided
	check_perm_cmd="grep 't' $f.drat | ./drat-trim/check-perm.py $n $f.perm"
	[ -n "$lex_opt" ] && check_perm_cmd="$check_perm_cmd $lex_opt"
	eval "$check_perm_cmd" | tee $f.permcheck
	if ! grep "VERIFIED" -q $f.permcheck
	then
		echo "ERROR: Trusted clauses not verified"
	fi
fi
