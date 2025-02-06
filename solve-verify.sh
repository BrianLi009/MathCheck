#!/bin/bash

# Default values
solver="maplesat"
pseudo_check=true
lex_order="smallest"
orbit_val=""
unembeddable=true
skip_verify=false

# Parse command line options
while getopts "scpluo:h" opt; do
	case $opt in
		s) skip_verify=true ;;
		c) solver="cadical" ;;
		p) pseudo_check=false ;;
		l) lex_order="greatest" ;;
		o) orbit_val="$OPTARG" ;;
		u) unembeddable=false ;;
		h) echo "
Description:
    Script for solving and generating drat proof for instance

Usage:
    ./solve-verify.sh [options] <n> <f>

Required Arguments:
    <n>: the order of the instance/number of vertices in the graph
    <f>: file name of the CNF instance to be solved

Options:
    -s: Skip verification step
    -c: Use CaDiCal solver (default: MapleSAT)
    -p: Disable pseudo check
    -l: Use lex-greatest ordering (default: lex-smallest)
    -o VALUE: Set orbit value (required if -o is used)
    -u: Disable unembeddable check (default: enabled)
    -h: Show this help message

Example:
    ./solve-verify.sh -c -l -o 42 17 instance.cnf
" 
			exit 0 ;;
		:) echo "Option -$OPTARG requires an argument." >&2; exit 1 ;;
		\?) echo "Invalid option: -$OPTARG" >&2; exit 1 ;;
	esac
done

# Shift to get positional arguments
shift $((OPTIND-1))

# Check required arguments
if [ $# -ne 2 ]; then
	echo "Error: Required arguments missing. Use -h for help."
	exit 1
fi

n=$1  # order
f=$2  # instance file name

# Construct solver command based on options
if [ "$solver" = "cadical" ]; then
	cmd="./cadical-ks/build/cadical-ks $f $f.drat --no-binary --order $n"
	[ "$unembeddable" = true ] && cmd="$cmd --unembeddable-check 13"
	[ "$pseudo_check" = false ] && cmd="$cmd --no-pseudo-check"
	[ "$lex_order" = "greatest" ] && cmd="$cmd --lex-greatest"
	[ -n "$orbit_val" ] && cmd="$cmd --orbit $orbit_val"
	cmd="$cmd --perm-out $f.perm"
	# Add proofsize parameter for single/multi modes
	if [[ "$f" =~ .*"single".* ]] || [[ "$f" =~ .*"multi".* ]]; then
		cmd="$cmd --proofsize 7168"
	fi
else
	cmd="./maplesat-ks/simp/maplesat_static $f $f.drat -order=$n -no-pre -minclause"
	[ "$unembeddable" = true ] && cmd="$cmd -unembeddable-check=13"
	[ "$pseudo_check" = false ] && cmd="$cmd -pseudo-test=false"
	[ "$lex_order" = "greatest" ] && cmd="$cmd -lex-greatest"
	[ -n "$orbit_val" ] && cmd="$cmd -orbit=$orbit_val"
	cmd="$cmd -perm-out=$f.perm -exhaustive=$f.exhaust"
	# Add proof size parameter for single/multi modes
	if [[ "$f" =~ .*"single".* ]] || [[ "$f" =~ .*"multi".* ]]; then
		cmd="$cmd -max-proof-size=7168"
	fi
fi

# Print the command
echo "Executing command: $cmd"

# Execute solver command
$cmd | tee $f.log

# Check if UNSAT was found
if ! grep -q "UNSAT" "$f.log"; then
	echo "Instance not solved (SAT/UNKNOWN) - no verification needed"
elif [ "$skip_verify" = true ]; then
	echo "Verification step skipped due to -s flag"
else
	# Pass lex-greatest flag to proof-module.sh if needed
	lex_opt=""
	[ "$lex_order" = "greatest" ] && lex_opt="-lex-greatest"
	./proof-module.sh $n $f $f.verify "" $lex_opt
fi