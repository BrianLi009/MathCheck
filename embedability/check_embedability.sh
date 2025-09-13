#!/bin/bash

[ "$1" = "-h" -o "$1" = "--help" ] && echo "
Description:
    This script takes in an exhaust file with kochen specker candidates, and determine whether each
    of them is embeddable, if it is embeddable, then it will be outputted into a file as a Kochen
    Specker graph. We require the existance of n.exhaust in the directory.

Usage:
    Must be called from the root directory
    ./embedability/check_embedability.sh [-s] [-p] [-v] [-b] n f

Options:
    [-s]: check if a graph contains a minimal unembeddable subgraph, if it does, it's not embeddable
    [-p]: applying proposition 1 and skip graph with vertex of degree less than 2
    [-v]: verify satisfiable embeddability result
    [-b]: use binary input format (default: maple format)
    <n>: the order of the instance/number of vertices in the graph
    <f>: file to check embedability on
    <s>: optional parameter to specify starting index of f
    <e>: optional parameter to specify ending index of f. If s is provided, e must be provided.

Input Formats:
    Maple format: a -1 -2 3 4 0 (original format)
    Binary format: Solution: 000000000000000000000000000000000000000000000000000000100000000100000000001001000000110000000000101001000000001100100000000000000110010000011000000010000001010000001000000010010001000000000010000100000001001000100000010100000100000001100001000000000010010000010001000100000000010100000001000000100000011000000000100001000000000000000100000000000000000010001000000000000001000101001000010000001000100000001000001010000000000100000100110100100000000000001001000000010
                Result: False
                --
" && exit

while getopts "spvb" opt
do
    case $opt in
        s) s="-s" ;;
        p) p="-p" ;;
        v) v="-v" ;;
        b) b="-b" ;;
    esac
done
shift $((OPTIND-1))

if [ -z "$1" ]
then
    echo "Need the order of the instance and file to check embedability on, use -h or --help for further instruction"
    exit
fi

using_subgraph=False
if [ "$s" == "-s" ]
    then
        echo "enabling using minimal nonembeddable subgraph"
        using_subgraph=True
    fi

verify=False
if [ "$v" == "-v" ]
    then
        echo "enable embeddability verification"
        verify=True
    fi

input_format="maple"
if [ "$b" == "-b" ]
    then
        echo "using binary input format"
        input_format="binary"
    fi

n=$1
f=$2
s=${3:-none}
e=${4:-none}

index=0

touch $f-embeddable.txt
touch $f-nonembeddable.txt

#if $f is empty, nothing to check and exit
if [ ! -s "$f" ]; then
    echo "File $f is empty. No candidate to check. Exiting embedability check..."
    exit 1
fi

python3 embedability/main.py "$f" "$n" "$index" $using_subgraph False $f-nonembeddable.txt $f-embeddable.txt $verify $s $e $input_format

noncount=`wc -l "$f-nonembeddable.txt" | awk '{print $1}'`
count=`wc -l "$f-embeddable.txt" | awk '{print $1}'`

echo $noncount nonembeddable candidates
echo $count embeddable candidates


