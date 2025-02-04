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
        --force        Force rebuild all dependencies
    "
    exit
}

# Improved clean function
clean_artifacts() {
    echo "Cleaning all artifacts..."
    
    # Clean drat-trim
    if [ -d "drat-trim" ]; then
        echo "Cleaning drat-trim..."
        (cd drat-trim && make clean -f Makefile 2>/dev/null || true)
    fi
    
    # Clean cadical-ks
    if [ -d "cadical-ks" ]; then
        echo "Cleaning cadical-ks..."
        (cd cadical-ks && make clean 2>/dev/null || true)
    fi
    
    # Clean maplesat-ks
    if [ -d "maplesat-ks" ]; then
        echo "Cleaning maplesat-ks..."
        (cd maplesat-ks && make clean 2>/dev/null || true)
    fi
    
    # Clean march_cu
    if [ -d "gen_cubes/march_cu" ]; then
        echo "Cleaning march_cu..."
        (cd gen_cubes/march_cu && make clean 2>/dev/null || true)
    fi
    
    # Clean nauty
    if [ -d "nauty2_8_8" ]; then
        echo "Cleaning nauty..."
        (cd nauty2_8_8 && make clean 2>/dev/null || true)
    fi
    
    echo "Cleanup completed"
}

# Check for help and clean flags first
[ "$1" = "-h" -o "$1" = "--help" ] && display_help
[ "$1" = "--clean" ] && { clean_artifacts; exit; }

# Add -x flag for verbose output if needed
[ "$1" = "-x" ] && set -x

# Check if force rebuild is requested
force_rebuild=false
[ "$1" = "--force" ] && force_rebuild=true

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

# Modified build_dependency function with target existence check
build_dependency() {
    local dir="$1"
    local target="$2"
    local build_cmd="${3:-make}"
    
    if [ ! -f "$dir/$target" ] || [ "$force_rebuild" = true ]; then
        echo "Building ${dir}..."
        (cd "$dir" || exit 1
         # Add -f flag to make clean to ignore missing files
         make clean -f Makefile 2>/dev/null || true
         eval "$build_cmd" && echo "Build successful")
    else
        echo "Target $dir/$target already exists, skipping build"
    fi
}

# Build dependencies only if targets don't exist or force rebuild is requested
build_dependency drat-trim drat-trim "make -f Makefile"
build_dependency cadical-ks build/cadical-ks "./configure && make"
build_dependency maplesat-ks simp/maplesat_static "make clean && make"
build_dependency nauty2_8_8 nauty "./configure && make"

# More robust submodule handling
echo "Updating git submodules..."
git submodule update --init --recursive

echo "Dependency setup completed successfully"