import subprocess
import multiprocessing
import os
import queue
import argparse
import sys

remove_file = True

def run_command(command):
    process_id = os.getpid()
    print(f"Debug: Process {process_id}: Executing command: {command}", flush=True)

    file_to_cube = command.split()[-1]

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()

        if stderr:
            print(f"Error executing command: {stderr.decode()}", flush=True)

        if "UNSAT" in stdout.decode():
            print("Debug: UNSAT found, terminating process", flush=True)
            process.terminate()
        else:
            print("Debug: Continue cubing this subproblem...", flush=True)
            command = f"cube('{file_to_cube}', 'N', 0, {mg}, '{orderg}', {numMCTSg}, queue, '{cutoffg}', {cutoffvg}, {dg}, 'True')"
            print(f"Debug: Adding to queue: {command}", flush=True)
            queue.put(command)

    except Exception as e:
        print(f"Failed to run command due to: {str(e)}", flush=True)

def run_cube_command(command):
    print(f"Debug: Executing cube command: {command}", flush=True)
    eval(command)

def remove_related_files(files_to_remove):
    global remove_file
    if not remove_file:
        return
        
    for file in files_to_remove:
        try:
            os.remove(file)
            print(f"Removed: {file}", flush=True)
        except OSError as e:
            print(f"Error: {e.strerror}. File: {file}", flush=True)

def rename_file(filename):
    # Remove .simp from file name
    
    if filename.endswith('.simp'):
        filename = filename[:-5]
    
    return filename
    
def worker(queue):
    while True:
        args = queue.get()
        if args is None:
            queue.task_done()
            break
        if args.startswith("./solve"):
            run_command(args)
        else:
            run_cube_command(args)
        queue.task_done()

def cube(original_file, cube, index, m, order, numMCTS, queue, cutoff='d', cutoffv=5, d=0, extension="False"):
    global cubing_mode_g, solver_options_g
    
    print(f"Debug: Cube parameters - file:{original_file}, cube:{cube}, index:{index}, m:{m}, order:{order}, numMCTS:{numMCTS}, cutoff:{cutoff}, cutoffv:{cutoffv}, d:{d}", flush=True)
    print(f"Debug: Using solver options: '{solver_options_g}'", flush=True)
    
    # Log the cube to the depth-specific file
    cube_log_file = f"cubes_depth_{d}.txt"
    with open(cube_log_file, "a") as log_file:
        if cube != "N":
            log_file.write(f"{cube}{index}\n")
        else:
            log_file.write(f"root_cube\n")
    
    # Extract relevant options for simplify-by-conflicts.sh
    simplify_opts = []
    if solver_options_g:
        opts = solver_options_g.split()
        for i, opt in enumerate(opts):
            if opt in ['-s', '-p', '-l', '-u']:  # Single options
                simplify_opts.append(opt)
            elif opt == '-o' and i + 1 < len(opts):  # Option with value
                simplify_opts.extend(['-o', opts[i + 1]])
    
    simplify_opts_str = ' '.join(simplify_opts)
    print(f"Debug: Using simplify options: '{simplify_opts_str}'", flush=True)
    
    if cube != "N":
        command = f"./gen_cubes/apply.sh {original_file} {cube} {index} > {cube}{index}.cnf && ./simplification/simplify-by-conflicts.sh {simplify_opts_str} {cube}{index}.cnf {order} 10000"
        file_to_cube = f"{cube}{index}.cnf.simp"
        simplog_file = f"{cube}{index}.cnf.simplog"
        file_to_check = f"{cube}{index}.cnf.ext"
    else:
        command = f"./simplification/simplify-by-conflicts.sh {simplify_opts_str} {original_file} {order} 10000"
        file_to_cube = f"{original_file}.simp"
        simplog_file = f"{original_file}.simplog"
        file_to_check = f"{original_file}.ext"
    
    print(f"Debug: Executing command: {command}", flush=True)
    subprocess.run(command, shell=True)

    # Check if the output contains "c exit 20"
    with open(simplog_file, "r") as file:
        if "c exit 20" in file.read():
            print("Debug: Found 'c exit 20' in simplog - the cube is UNSAT", flush=True)
            if cube != "N":
                files_to_remove = [f'{cube}{index}.cnf', file_to_cube, file_to_check]
                print(f"Debug: Cleaning up files for UNSAT cube: {files_to_remove}", flush=True)
            return
    
    command = f"sed -E 's/.* 0 [-]*([0-9]*) 0$/\\1/' < {file_to_check} | awk '$0<={m}' | sort | uniq | wc -l"
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    var_removed = int(result.stdout.strip())
    if extension == "True":
        if cutoff == 'v':
            cutoffv = var_removed + 20
            print(f"Debug: Extension enabled, adjusting variable cutoff to: {cutoffv}", flush=True)
        else:
            cutoffv = cutoffv + 5
            print(f"Debug: Extension enabled, adjusting depth cutoff to: {cutoffv}", flush=True)

    print(f"Debug: {var_removed} variables removed from the cube", flush=True)

    if cutoff == 'd':
        print(f"Debug: Using depth-based cutoff. Current depth: {d}, Cutoff value: {cutoffv}", flush=True)
        if d >= cutoffv:
            print(f"Debug: Reached depth cutoff ({d} >= {cutoffv})", flush=True)
            if solveaftercubeg == 'True':
                files_to_remove = [f'{cube}{index}.cnf']
                remove_related_files(files_to_remove)
                # Fix: Use -P instead of -p
                solver_opts = solver_options_g.strip()
                print(f"Debug: Base solver options: '{solver_opts}'", flush=True)
                if solver_opts:
                    solver_opts = f"{solver_opts} -P"  # Use -P instead of -p
                else:
                    solver_opts = "-P"  # Use -P instead of -p
                print(f"Debug: Final solver options: '{solver_opts}'", flush=True)
                command = f"./solve-verify.sh {solver_opts} {order} {file_to_cube}"
                print(f"Debug: Depth cutoff reached, adding solve task to queue: {command}", flush=True)
                queue.put(command)
            return
    if cutoff == 'v':
        print(f"Debug: Using variable-based cutoff. Variables removed: {var_removed}, Cutoff value: {cutoffv}", flush=True)
        if var_removed >= cutoffv:
            print(f"Debug: Reached variable cutoff ({var_removed} >= {cutoffv})", flush=True)
            if solveaftercubeg == 'True':
                files_to_remove = [f'{cube}{index}.cnf']
                remove_related_files(files_to_remove)
                # Fix: Use -P instead of -p
                solver_opts = solver_options_g.strip()
                print(f"Debug: Base solver options: '{solver_opts}'", flush=True)
                if solver_opts:
                    solver_opts = f"{solver_opts} -P"  # Use -P instead of -p
                else:
                    solver_opts = "-P"  # Use -P instead of -p
                print(f"Debug: Final solver options: '{solver_opts}'", flush=True)
                command = f"./solve-verify.sh {solver_opts} {order} {file_to_cube}"
                print(f"Debug: Variable cutoff reached, adding solve task to queue: {command}", flush=True)
                queue.put(command)
            return

    print(f"Debug: Cutoff not reached, continuing with cubing", flush=True)
    # Select cubing method based on cubing_mode
    if cubing_mode_g == "march":
        print(f"Debug: Using march cubing mode", flush=True)
        subprocess.run(f"./march/march_cu {file_to_cube} -d 1 -m {m} -o {file_to_cube}.temp", shell=True)
    else:  # ams mode
        print(f"Debug: Using ams cubing mode", flush=True)
        subprocess.run(f"python3 -u alpha-zero-general/main.py {file_to_cube} -d 1 -m {m} -o {file_to_cube}.temp -prod -numMCTSSims {numMCTS}", shell=True)

    d += 1
    if cube != "N":
        subprocess.run(f'''sed -E "s/^a (.*)/$(head -n {index} {cube} | tail -n 1 | sed -E 's/(.*) 0/\\1/') \\1/" {file_to_cube}.temp > {cube}{index}''', shell=True)
        next_cube = f'{cube}{index}'
    else:
        subprocess.run(f'mv {file_to_cube}.temp {original_file}0', shell=True)
        next_cube = f'{original_file}0'

    print(f"Debug: Generated next cube: {next_cube}", flush=True)
    
    if cube != "N":
        files_to_remove = [
            f'{cube}{index}.cnf',
            f'{file_to_cube}.temp',
            file_to_cube,
            file_to_check
        ]
        print(f"Debug: Cleaning up intermediate files: {files_to_remove}", flush=True)
        remove_related_files(files_to_remove)
    else:
        files_to_remove = [file_to_cube, file_to_check]
        print(f"Debug: Cleaning up intermediate files: {files_to_remove}", flush=True)
        remove_related_files(files_to_remove)

    command1 = f"cube('{original_file}', '{next_cube}', 1, {m}, '{order}', {numMCTS}, queue, '{cutoff}', {cutoffv}, {d})"
    command2 = f"cube('{original_file}', '{next_cube}', 2, {m}, '{order}', {numMCTS}, queue, '{cutoff}', {cutoffv}, {d})"
    print(f"Debug: Adding new cube tasks to queue:", flush=True)
    print(f"Debug: Task 1: {command1}", flush=True)
    print(f"Debug: Task 2: {command2}", flush=True)
    queue.put(command1)
    queue.put(command2)

def main(order, file_name_solve, m, cubing_mode="ams", numMCTS=2, cutoff='d', cutoffv=5, solveaftercube='True', timeout=sys.maxsize, solver_options=""):
    print(f"Debug: Main parameters - order:{order}, file:{file_name_solve}, m:{m}, mode:{cubing_mode}, numMCTS:{numMCTS}, cutoff:{cutoff}, cutoffv:{cutoffv}, solver_options:'{solver_options}'", flush=True)
    
    # Validate input parameters
    if cubing_mode not in ["march", "ams"]:
        raise ValueError("cubing_mode must be either 'march' or 'ams'")
    if m is None:
        raise ValueError("m parameter must be specified")

    d = 0
    cutoffv = int(cutoffv)
    m = int(m)

    # Create a directory for cube logs if it doesn't exist
    os.makedirs("cube_logs", exist_ok=True)
    
    # Clear previous cube log files
    for existing_file in os.listdir("cube_logs"):
        if existing_file.startswith("cubes_depth_"):
            os.remove(os.path.join("cube_logs", existing_file))
    
    # Update global variables
    global queue, orderg, numMCTSg, cutoffg, cutoffvg, dg, mg, solveaftercubeg, file_name_solveg, cubing_mode_g, solver_options_g
    orderg, numMCTSg, cutoffg, cutoffvg, dg, mg, solveaftercubeg, file_name_solveg = order, numMCTS, cutoff, cutoffv, d, m, solveaftercube, file_name_solve
    cubing_mode_g = cubing_mode
    # Strip any extra whitespace from solver options
    solver_options_g = solver_options

    queue = multiprocessing.JoinableQueue()
    num_worker_processes = multiprocessing.cpu_count()
    print(f"Debug: Starting {num_worker_processes} worker processes", flush=True)

    # Start worker processes
    processes = [multiprocessing.Process(target=worker, args=(queue,)) for _ in range(num_worker_processes)]
    for p in processes:
        p.start()

    #file_name_solve is a file where each line is a filename to solve
    with open(file_name_solve, 'r') as file:
        first_line = file.readline().strip()  # Read the first line and strip whitespace
        print(f"Debug: First line of input file: {first_line}", flush=True)

        # Check if the first line starts with 'p cnf'
        if first_line.startswith('p cnf'):
            print("Debug: Input file is a CNF file", flush=True)
            cube(file_name_solve, "N", 0, m, order, numMCTS, queue, cutoff, cutoffv, d)
        else:
            print("Debug: Input file contains multiple CNF files", flush=True)
            # Prepend the already read first line to the list of subsequent lines
            instance_lst = [first_line] + [line.strip() for line in file]
            for instance in instance_lst:
                # Add -P to solver options to enable proof size limit
                solver_opts = (solver_options_g + " -P") if solver_options_g else "-P"
                command = f"./solve-verify.sh {solver_opts} {order} {instance}"
                print(f"Debug: Adding to queue: {command}", flush=True)
                queue.put(command)

    # Wait for all tasks to be completed
    queue.join()

    # Stop workers
    for _ in processes:
        queue.put(None)
    for p in processes:
        p.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        epilog='Example usage: python3 parallel-solve.py 17 instances/ks_17.cnf -m 136 --solver-options="-c -l -o 42"'
    )
    parser.add_argument('order', type=int, help='Order of the graph')
    parser.add_argument('file_name_solve', help='Input file name')
    parser.add_argument('-m', type=int, required=True,
                        help='Number of variables to consider for cubing')
    parser.add_argument('--cubing-mode', choices=['march', 'ams'], default='ams',
                        help='Cubing mode: ams (alpha-zero-general, default) or march')
    parser.add_argument('--numMCTS', type=int, default=2,
                        help='Number of MCTS simulations (only for ams mode)')
    parser.add_argument('--cutoff', choices=['d', 'v'], default='d',
                        help='Cutoff type: d (depth-based) or v (variable-based)')
    parser.add_argument('--cutoffv', type=int, default=5,
                        help='Cutoff value')
    parser.add_argument('--solveaftercube', choices=['True', 'False'], default='True',
                        help='Whether to solve after cubing')
    parser.add_argument('--solver-options', type=str, default="",
                        help='Additional options to pass to solve-verify.sh (e.g., -c -l -o 42)')
    parser.add_argument('--timeout', type=int, default=sys.maxsize,
                        help='Timeout in seconds (default: maximum possible)')

    args = parser.parse_args()
    
    # Clean up solver options
    solver_options = args.solver_options
    if solver_options:
        solver_options = solver_options.strip('"\'')
        solver_options = ' '.join(solver_options.split())
        print(f"Debug: Cleaned solver options: '{solver_options}'", flush=True)

    main(args.order, args.file_name_solve, args.m, args.cubing_mode,
         args.numMCTS, args.cutoff, args.cutoffv, args.solveaftercube,
         args.timeout, solver_options)