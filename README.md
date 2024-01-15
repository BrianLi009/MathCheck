`embedability`: check whether kochen specker candidates are embedable, if a candidate is indeed embedable, it is a Kochen Specker graph as desired, can be ran using check-embed.sh

`gen_cubes`: generate the cubes used in cube and conquer, merge cubes into the instance then solve using MapleSAT, can be ran using cube-solve.sh

`gen_instance`: include scripts that generate SAT instance of certain order with satisfying certain contraints, can be ran using generate-instance.sh

`maplesat-ks`: MapleSAT solver with orderly generation (SAT + CAS)

`non_can`: pre-generated noncanonical blocking clauses that can be added to the instance

`simplification`: contains script relavant to simplification in the pipeline

`generate-instance.sh`: script that initiate instance geenration for order n, can be called with ./generate-instance.sh n

`cube-solve.sh`: script that perform incremental cubing, merge cubes into instance and solve with maplesat, can be called with ./cube-solve.sh n(graph order) r(number of variables to eliminate) f(instance file name)

`check-embed`: script that perform embedability checking on n.exhaust, which is the file that contains all kochen specker candidates output by MapleSAT. can be called with ./check-embed.sh n(graph order)

`dependency-setup.sh`: script that set up all dependencies, see the script documentation for details, can be called with ./dependency-setup.sh

`main.sh`: driver script that connects all script stated above, running this script will execute the entire pipeline, can be called with ./main.sh n(graph order) s(number of times to simplify, default to be 3) r(number of variables to eliminate during incremental cubing)

`verify.sh`: verify all KS candidates satisfy the constraints

`Pipeline`: 

dependencies: maplesat-ks, cadical, networkx, z3-solver, and march_cu from cube and conquer. Run dependency-setup.sh for dependency setup

![Showing pipeline and which directory to enter for each step](pipeline.png?raw=true "Pipeline")
