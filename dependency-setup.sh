#!/bin/bash
set -e  # Exit immediately if any command fails
set -o pipefail  # Fail piped commands

# Updated help function
function display_help() {
    echo "
    Description:
        This script manages dependencies including installation and cleanup

    Usage:
        ./dependency-setup.sh [options]

    Options:
        -h, --help      Show this help
        -x              Enable verbose mode
        --clean         Remove all built artifacts
    "
    exit
}

# Check if help is requested
[ "$1" = "-h" -o "$1" = "--help" ] && display_help

# Add -x flag for verbose output if needed
[ "$1" = "-x" ] && set -x

echo "Prerequisite: Checking for pip and make..."
command -v pip3 >/dev/null 2>&1 || { echo "pip3 not found. Aborting."; exit 1; }
command -v make >/dev/null 2>&1 || { echo "make not found. Aborting."; exit 1; }

# Networkx version check with better python parsing
required_version="2.5"
if ! python3 -c "import networkx as nx; exit(not (tuple(map(int, nx.__version__.split('.'))) >= (2,5)))" 2>/dev/null; then
    echo "Upgrading networkx to >=${required_version}..."
    pip3 install --upgrade "networkx>=${required_version}"
else
    echo "Networkx >=${required_version} already installed"
fi

# Check if z3-solver is installed
if pip3 list | grep z3-solver
then
    echo "Z3-solver package installed"
else 
    pip3 install z3-solver
fi

# Modified build_dependency function
build_dependency() {
    local dir="$1"
    local target="$2"
    local build_cmd="${3:-make}"
    
    echo "Building ${dir}..."
    (cd "$dir" || exit 1
     # Add -f flag to make clean to ignore missing files
     [ -f "$target" ] || { eval "make clean -f Makefile 2>/dev/null || true; $build_cmd" && echo "Build successful"; })
}

build_dependency drat-trim drat-trim "make -f Makefile"
build_dependency cadical-ks build/cadical-ks "./configure && make"
build_dependency maplesat-ks simp/maplesat_static "make clean && make"
build_dependency nauty2_8_8 nauty "./configure && make"

# More robust submodule handling
echo "Updating git submodules..."
git submodule update --init --recursive

# New clean function
clean_artifacts() {
    echo "Cleaning all artifacts..."
    
    # Clean drat-trim
    (cd drat-trim && make clean -f Makefile 2>/dev/null || true)
    
    # Clean cadical-ks
    (cd cadical-ks && [ -f Makefile ] && make clean 2>/dev/null || true)
    
    # Clean maplesat-ks
    (cd maplesat-ks && make clean 2>/dev/null || true)
    
    # Clean march_cu
    (cd gen_cubes/march_cu && make clean 2>/dev/null || true)
    
    # Clean nauty
    (cd nauty2_8_8 && [ -f Makefile ] && make clean 2>/dev/null || true)
    
    echo "Cleanup completed"
}

# Handle clean mode
[ "$1" = "--clean" ] && { clean_artifacts; exit; }

echo "Dependency setup completed successfully"