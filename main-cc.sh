n=$1 #order
t=${2:-10000} #conflicts for which to simplify each time CaDiCal is called, or % of variables to eliminate
s=${3:-2} #by default we only simplify the instance using CaDiCaL after adding noncanonical blocking clauses
b=${4:-2} #by default we generate noncanonical blocking clauses in real time
r=${5:-0} #num of var to eliminate during first cubing stage
a=${6:-10} #amount of additional variables to remove for each cubing call
z=${7:-1} #cubing strategy 1: march 2: ams with no mcts 3: ams with mcts

#step 2: setp up dependencies
./dependency-setup.sh

#step 3 and 4: generate pre-processed instance

dir="."

if [ -f constraints_${n}_${t}_${s}_${b}_${r}_${a}_final.simp.log ]
then
    echo "Instance with these parameters has already been solved."
    exit 0
fi

./generate-simp-instance.sh $n $t $s $b $r $a

if [ -f "$n.exhaust" ]
then
    rm $n.exhaust
fi

if [ -f "embedability/$n.exhaust" ]
then
    rm embedability/$n.exhaust
fi

#need to fix the cubing part for directory pointer
#step 5: cube and conquer if necessary, then solve
if [ "$r" != "0" ]
then
    dir="${n}_${t}_${s}_${b}_${r}_${a}_${z}"
    #./3-cube-merge-solve-ams.sh constraints_${n}_${t}_${s}_${b}_${r}_${a}_final.simp $n $r $dir
    echo "cubing with option $z"
    ./3-cube-merge-solve-iterative-learnt-cc.sh $p $n constraints_${n}_${t}_${s}_${b}_${r}_${a}_final.simp $dir $r $t $a $z
    command="./summary-iterative.sh $dir $r $a $n"
    echo $command
    eval $command
    #join all exhaust file together and check embeddability
    find "$dir" -type f -name "*.exhaust" -exec cat {} + > "$dir/$n.exhaust"
    ./verify.sh $dir/$n.exhaust $n
    ./4-check-embedability.sh $n $dir/$n.exhaust
else
    ./maplesat-solve-verify.sh $n constraints_${n}_${t}_${s}_${b}_${r}_${a}_final.simp $n.exhaust
    #step 5.5: verify all constraints are satisfied
    ./verify.sh $n.exhaust $n

    #step 6: checking if there exist embeddable solution
    echo "checking embeddability of KS candidates using Z3..."
    ./4-check-embedability.sh $n $n.exhaust

    #output the number of KS system if there is any
    echo "$(wc -l < $n.exhaust) Kochen-Specker candidates were found."
    echo "$(wc -l < $n.exhaust-embeddable.txt) Kochen-Specker solutions were found."
fi