#!/bin/bash
#SBATCH --account=rrg-cbright
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=0
#SBATCH --time=1-00:00

module load python/3.10
python parallel-solve.py 17 constraints_17_0.5 constraints_17_0.5-d 20 10 constraints_17_0.5.commands1
