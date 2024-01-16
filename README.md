`embedability`: check whether kochen specker candidates are embedable, if a candidate is indeed embedable, it is a Kochen Specker graph as desired, can be ran using check-embed.sh

`gen_cubes`: generate the cubes used in cube-and-conquer.

`gen_instance`: include scripts that generate SAT instance of certain order with satisfying certain contraints, can be ran using generate-instance.sh

`maplesat-ks`: MapleSAT solver with orderly generation (SAT + CAS)

`cadical-ks`: CaDiCaL solver with orderly generation (SAT + CAS)

`simplification`: contains script relavant to simplification in the pipeline

`generate-instance.sh`: script that initiate instance geenration for order n, can be called with ./generate-instance.sh n

`cube-solve.sh`: script that perform iterative cubing, merge cubes into instance, simplify with CaDiCaL+CAS and solve with maplesat+CAS

`check-embed`: script that perform embedability checking on n.exhaust, which is the file that contains all kochen specker candidates output by MapleSAT. can be called with ./check-embed.sh n(graph order)

`dependency-setup.sh`: script that set up all dependencies, see the script documentation for details, can be called with ./dependency-setup.sh

`main.sh`: driver script that connects all script stated above, running this script will execute the entire pipeline, can be called with ./main.sh n(graph order)

`verify.sh`: verify all KS candidates satisfy the constraints

`Pipeline`: 

dependencies: maplesat-ks, cadical, networkx, z3-solver, and march_cu from cube and conquer. Run dependency-setup.sh for dependency setup

![Showing pipeline and which directory to enter for each step](pipeline.png?raw=true "Pipeline")
