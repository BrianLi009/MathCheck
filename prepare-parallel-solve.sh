#!/bin/bash

# Check for the -m flag and its associated value
s=2 # Default value for s
use_m_flag=false
while getopts ":m:" opt; do
  case $opt in
    m)
      s=$OPTARG
      use_m_flag=true
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
c1=$3 #number of cubes initially
c2=$4 #number of cubes for deeper layers
nodes=$5 #number of nodes to submit to in total

d=${f}-d

if $use_m_flag
then
    ./cube-solve-cc.sh -m $s $n $f $d $c1 $c2
else
    ./cube-solve-cc.sh $n $f $d $c1 $c2
fi

total_lines=$(wc -l < "${f}.commands")
((lines_per_file = (total_lines + $nodes - 1) / $nodes))

# Shuffle and split the file
shuf "${f}.commands" | split -l "$lines_per_file" - shuffled_

counter=1
for file in shuffled_*; do
    mv "$file" "${f}.commands${counter}"
    cat <<EOF > "script_${counter}.sh"
#!/bin/bash
#SBATCH --account=rrg-cbright
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=0
#SBATCH --time=1-00:00

module load python/3.10

if $use_m_flag
then
    python parallel-solve.py $n $f $d $c1 $c2 ${f}.commands${counter} $s
else
    python parallel-solve.py $n $f $d $c1 $c2 ${f}.commands${counter}
fi

EOF

    ((counter++))
done



