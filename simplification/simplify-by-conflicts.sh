#!/bin/bash

s=false
pseudo_check=true
lex_order="smallest"
orbit_val=""
unembeddable=true

# Option parsing
#if the s flag is enabled, DRAT file will still be generated but verification will be skipped
while getopts ":spluo:c" opt; do
  case $opt in
    s) s=true ;;
    p) pseudo_check=false ;;
    l) lex_order="greatest" ;;
    u) unembeddable=false ;;
    o) orbit_val="$OPTARG" ;;
    c) : ;;
    \?) echo "Invalid option: -$OPTARG" >&2; exit 1 ;;
  esac
done

shift $((OPTIND -1))

# Ensure parameters are specified on the command-line
if [ -z "$3" ]; then
  echo "Need filename, order, and the number of conflicts for which to simplify"
  echo "Options:"
  echo "  -s: Skip DRAT verification"
  echo "  -p: Disable pseudo check"
  echo "  -l: Use lex-greatest ordering"
  echo "  -u: Disable unembeddable check"
  echo "  -o VALUE: Set orbit value"
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

# Construct base CaDiCaL command
cmd="./cadical-ks/build/cadical-ks"
[ "$s" != "true" ] && cmd="$cmd $f_dir $f_dir.drat" || cmd="$cmd $f_dir"
cmd="$cmd --order $o"
#[ "$unembeddable" = true ] && cmd="$cmd --unembeddable-check 13"
[ "$pseudo_check" = false ] && cmd="$cmd --no-pseudo-check"
[ "$lex_order" = "greatest" ] && cmd="$cmd --lex-greatest"
[ -n "$orbit_val" ] && cmd="$cmd --orbit $orbit_val"
cmd="$cmd -o $f_dir.simp1 -e $f_dir.ext -n -c $m"

# Simplify m seconds
echo "simplifying for $m conflicts"

# Execute CaDiCaL command
if [ "$s" = true ]; then
    echo "skipping generation of DRAT file and verification"
    $cmd | tee "$f_dir".simplog
else
    $cmd | tee "$f_dir".simplog
    echo "verifying the simplification now..."
    if grep -q "exit 20" "$f_dir".simplog; then
        # Pass lex-greatest flag to proof-module.sh if needed
        lex_opt=""
        [ "$lex_order" = "greatest" ] && lex_opt="-lex-greatest"
        ./proof-module.sh $o $f_dir $f_dir.verify "" $lex_opt
    else
        echo "CaDiCaL returns UNKNOWN, using forward proof checking..."
        # Pass lex-greatest flag to proof-module.sh if needed
        lex_opt=""
        [ "$lex_order" = "greatest" ] && lex_opt="-lex-greatest"
        ./proof-module.sh $o $f_dir $f_dir.verify "f" $lex_opt
    fi
fi

# Output final simplified instance
./gen_cubes/concat-edge.sh $o "$f_dir".simp1 "$f_dir".ext > "$f_dir".simp
rm -f "$f_dir".simp1
