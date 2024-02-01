#!/bin/bash
#SBATCH --account=rrg-cbright
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=0
#SBATCH --time=1-00:00

module load python/3.10
python parallel-solve.py -m 2  17 constraints_17_0.5 2.commands1
