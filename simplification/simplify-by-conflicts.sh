#!/bin/bash

s=false

# Option parsing
while getopts ":s" opt; do
  case $opt in
    s) s=true ;;
    \?) echo "Invalid option: -$OPTARG" >&2; exit 1 ;;
  esac
done

shift $((OPTIND -1))

# Ensure parameters are specified on the command-line
if [ -z "$2" ]; then
  echo "Need filename, order, and the number of conflicts for which to simplify"
  exit
fi

f=$1 # Filename
o=$2 # Order
m=$3 # Number of conflicts
e=$((o*(o-1)/2)) # Number of edge variables

# Create necessary directories
mkdir -p log

f_dir=$f
f_base=$(basename "$f")

# Simplify m seconds
echo "simplifying for $m conflicts"
i=1
./cadical-ks/build/cadical-ks "$f_dir" "$f_dir.drat" --order $o --unembeddable-check 17 -o "$f_dir".simp1 -e "$f_dir".ext -n -c $m

if [ "$s" != "true" ]; then
    echo "verifying the simplification now..."
    ./drat-trim/drat-trim "$f_dir" "$f_dir.drat" -f | tee "$f_dir".verify
    if ! grep -E "s DERIVATION|s VERIFIED" -q "$f_dir".verify; then
        echo "ERROR: Proof not verified"
    fi
    rm -f "$f_dir.drat"
fi

# Output final simplified instance
./gen_cubes/concat-edge.sh $o "$f_dir".simp1 "$f_dir".ext > "$f_dir".simp
rm -f "$f_dir".simp1
