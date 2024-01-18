`embedability`: Check whether Kochen–Specker candidates are embeddable, if a candidate is indeed embeddable, it is a Kochen–Specker graph as desired. Can be ran using check-embed.sh

`gen_cubes`: Generate the cubes to used in cube-and-conquer

`gen_instance`: Include scripts that generate SAT instance of certain order with satisfying certain constraints. Can be ran using generate-instance.sh

`maplesat-ks`: MapleSAT solver with orderly generation (SAT + CAS)

`cadical-ks`: CaDiCaL solver with orderly generation (SAT + CAS)

`simplification`: Contains scripts relevant to simplification in the pipeline

`generate-instance.sh`: Script that initiates the instance generation in order n. Can be called with ./generate-instance.sh n

`cube-solve.sh`: Script that performs iterative cubing, merges cubes into the instance, simplifies with CaDiCaL+CAS, and solves with MapleSAT+CAS

`check-embed`: Script that performs embeddability checking on n.exhaust, which is the file that contains all Kochen–Specker candidates output by MapleSAT. Can be called with ./check-embed.sh n (graph order)

`dependency-setup.sh`: Script that sets up all dependencies; see the script documentation for details. Can be called with ./dependency-setup.sh

`main.sh`: Driver script that connects all scripts stated above; running this script will execute the entire pipeline. Can be called with ./main.sh n (graph order)

`verify.sh`: Verify all KS candidates satisfy the constraints

`Pipeline`:

dependencies: MapleSAT-ks, CaDiCaL-ks, NetworkX, z3-solver, and AlphaMapleSAT. Run dependency-setup.sh for dependency setup

![Showing pipeline and which directory to enter for each step](pipeline.png?raw=true "Pipeline")
