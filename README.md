# Kochen-Specker Graph Generation and Verification

This repository contains a collection of scripts and tools for generating and verifying Kochen-Specker graphs. 

## Components

- `embedability`: Checks whether Kochen–Specker candidates are embeddable. If a candidate is embeddable, it is a Kochen–Specker graph. Use `check-embed.sh` to run this check.

- `gen_cubes`: Generates the cubes used in the cube-and-conquer approach.

- `gen_instance`: Includes scripts that generate SAT instances of a certain order satisfying certain constraints. Use `generate-instance.sh` to run these scripts.

- `maplesat-ks`: A MapleSAT solver with orderly generation (SAT + CAS).

- `cadical-ks`: A CaDiCaL solver with orderly generation (SAT + CAS).

- `simplification`: Contains scripts relevant to the simplification process in the pipeline.

## Scripts

- `generate-instance.sh`: Initiates the instance generation in order `n`. Run with `./generate-instance.sh n`.

- `cube-solve.sh`: Performs iterative cubing, merges cubes into the instance, simplifies with CaDiCaL+CAS, and solves with MapleSAT+CAS.

- `check-embed.sh`: Performs embeddability checking on `n.exhaust`, which is the file that contains all Kochen–Specker candidates output by MapleSAT. Run with `./check-embed.sh n` (graph order).

- `dependency-setup.sh`: Sets up all dependencies. See the script documentation for details. Run with `./dependency-setup.sh`.

- `main.sh`: Driver script that connects all scripts stated above. Running this script will execute the entire pipeline. Run with `./main.sh n` (graph order).

- `verify.sh`: Verifies all KS candidates satisfy the constraints.

## Pipeline

The pipeline depends on MapleSAT-ks, CaDiCaL-ks, NetworkX, z3-solver, and AlphaMapleSAT. Run `dependency-setup.sh` for dependency setup.