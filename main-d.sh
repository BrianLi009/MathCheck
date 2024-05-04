n=$1 #order
c=$2 #ratio of color-1 vertices to block
d=$3 #definition used

./generate-instance.sh $n $c $d

python3 gen_instance/generate-color.py $n $c 0.5

./maplesat-d/simp/maplesat_static constraints_${n}_${c}_${d} -exhaustive=$n.exhaust -order=$n -no-pre -coloring-enc=colors_${n}_${c}_0.5