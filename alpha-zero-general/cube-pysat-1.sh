#!/bin/bash
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G       
#SBATCH --account=def-vganesh
#SBATCH --mail-type=ALL
#SBATCH --mail-user=piyush.jha@uwaterloo.ca
#SBATCH --time=0-06:00      # time (DD-HH:MM)
#SBATCH --output=cubing_outputs/e4_20_pysat_varm_unsat-%N-%j.out  # %N for node name, %j for jobID

module load python/3.10
source ~/alphacube_env/bin/activate

python -u march_pysat_m_unsatrecomp.py "constraints_20_c_100000_2_2_0_final.simp" -n 40 -m 190 -o "e4_20_pysat_varm_unsat.cubes"
