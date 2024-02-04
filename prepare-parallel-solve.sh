#!/bin/bash

# Check for the -s flag and its associated value
use_s_flag=false
while getopts ":s:" opt; do
  case $opt in
    s)
      s=$OPTARG
      use_s_flag=true
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
d=$3 #directory
nodes=$4 #number of nodes to submit to in total
s=$5 #number of MCTS simulation, only used if -s is used

if $use_s_flag
then
    ./gen_cubes/cube.sh -s $s $n $f $nodes $d
else
    ./gen_cubes/cube.sh $n $f $nodes $d
fi

files=$(ls $d/$v/$n-cubes/*.cubes)
highest_num=$(echo "$files" | awk -F '[./]' '{print $(NF-1)}' | sort -nr | head -n 1)
echo "currently the cubing depth is $highest_num"
cube_file=$d/$v/$n-cubes/$highest_num.cubes

numline=$(< $cube_file wc -l)
new_index=$((numline))

for i in $(seq 1 $new_index) #1-based indexing for cubes
    do 
        ./gen_cubes/apply.sh $f $cube_file $i > $cube_file$i.adj
        cat <<EOF > "script_${i}.sh"
#!/bin/bash
#SBATCH --account=rrg-cbright
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=0
#SBATCH --time=1-00:00

module load python/3.10

python parallel-solve.py ${n} $cube_file$i.adj $s d 8

EOF
done

