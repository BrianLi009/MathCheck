import subprocess
import multiprocessing
import os
import queue
import tempfile

def run_command(command):
    process_id = os.getpid()
    print(f"Process {process_id}: Executing command: {command}")

    file_to_cube = command.split()[-1]

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()

        if stderr:
            print(f"Error executing command: {stderr.decode()}")

        if "UNSAT" in stdout.decode():
            print("solved")
            remove_related_files(file_to_cube)
            process.terminate()
        else:
            print("Continue cubing this subproblem...")
            command = f"cube('{file_to_cube}', 'N', 0, {mg}, '{orderg}', {numMCTSg}, queue, '{cutoffg}', {cutoffvg}, {dg}, 'True', '{solver_optsg}')"
            queue.put(command)

    except Exception as e:
        print(f"Failed to run command due to: {str(e)}")

def run_cube_command(command):
    print(command)
    eval(command)

def remove_related_files(new_file):
    extensions = ['.simp', '.perm', '.nonembed', '.drat']
    for ext in extensions:
        try:
            os.remove(new_file + ext)
        except OSError:
            pass

def worker(queue):
    while True:
        args = queue.get()
        if args is None:
            break
        if args.startswith("./solve-verify"):
            run_command(args)
        else:
            run_cube_command(args)
        queue.task_done()

def cube(original_file, cube, index, m, order, numMCTS, queue, cutoff='d', cutoffv=5, d=0, extension="False", solver_opts=""):
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
        if cube != "N":
            subprocess.run(f"./gen_cubes/apply.sh {original_file} {cube} {index} | ./simplification/simplify-by-conflicts.sh -s - {order} 10000", shell=True, stdout=temp_file, stderr=subprocess.DEVNULL)
            file_to_cube = temp_file.name
        else:
            subprocess.run(f"./simplification/simplify-by-conflicts.sh -s {original_file} {order} 10000", shell=True, stdout=temp_file, stderr=subprocess.DEVNULL)
            file_to_cube = temp_file.name

        temp_file.seek(0)
        if "c exit 20" in temp_file.read():
            print("the cube is UNSAT")
            return

    var_removed = subprocess.run(f"sed -E 's/.* 0 [-]*([0-9]*) 0$/\\1/' < {file_to_cube} | awk '$0<={m}' | sort -u | wc -l", shell=True, capture_output=True, text=True).stdout.strip()
    var_removed = int(var_removed)

    if extension == "True":
        cutoffv = var_removed + 40

    print(f'{var_removed} variables removed from the cube')

    if (cutoff == 'd' and d >= cutoffv) or (cutoff == 'v' and var_removed >= cutoffv):
        if solveaftercubeg == 'True':
            command = f"./solve-verify.sh {solver_opts} {order} {file_to_cube}"
            queue.put(command)
        return

    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_output:
        subprocess.run(f"python3 -u alpha-zero-general/main.py {file_to_cube} -d 1 -m {m} -o - -order {order} -prod -numMCTSSims {numMCTS}", shell=True, stdout=temp_output, stderr=subprocess.DEVNULL)
        
        d += 1
        if cube != "N":
            next_cube = f'{cube}{index}'
            subprocess.run(f'''sed -E "s/^a (.*)/$(head -n {index} {cube} | tail -n 1 | sed -E 's/(.*) 0/\\1/') \\1/" {temp_output.name} > {next_cube}''', shell=True)
        else:
            next_cube = f'{original_file}0'
            subprocess.run(f"cp {temp_output.name} {next_cube}", shell=True)

    os.unlink(temp_output.name)

    command1 = f"cube('{original_file}', '{next_cube}', 1, {m}, '{order}', {numMCTS}, queue, '{cutoff}', {cutoffv}, {d}, 'False', '{solver_opts}')"
    command2 = f"cube('{original_file}', '{next_cube}', 2, {m}, '{order}', {numMCTS}, queue, '{cutoff}', {cutoffv}, {d}, 'False', '{solver_opts}')"
    queue.put(command1)
    queue.put(command2)

def main(order, file_name_solve, numMCTS=2, cutoff='d', cutoffv=5, solveaftercube='True', solver_opts=""):
    # Convert arguments if they're passed with flag format
    if isinstance(numMCTS, str) and numMCTS.startswith('--numMCTS'):
        numMCTS = int(numMCTS.split(' ')[1])
    if isinstance(cutoff, str) and cutoff.startswith('--cutoff'):
        cutoff = cutoff.split(' ')[1]
    if isinstance(cutoffv, str) and cutoffv.startswith('--cutoffv'):
        cutoffv = int(cutoffv.split(' ')[1])
    if isinstance(solveaftercube, str) and solveaftercube.startswith('--solveaftercube'):
        solveaftercube = solveaftercube.split(' ')[1]

    # Combine remaining args into solver_opts
    if isinstance(solver_opts, (list, tuple)):
        solver_opts = ' '.join(str(x) for x in solver_opts)

    global queue, orderg, numMCTSg, cutoffg, cutoffvg, dg, mg, solveaftercubeg, file_name_solveg, solver_optsg
    orderg, numMCTSg, cutoffg, cutoffvg, dg, mg, solveaftercubeg, file_name_solveg, solver_optsg = (
        order, numMCTS, cutoff, cutoffv, 0, int(int(order)*(int(order)-1)/2), 
        solveaftercube, file_name_solve, solver_opts
    )
    
    queue = multiprocessing.JoinableQueue()
    num_worker_processes = multiprocessing.cpu_count()

    with multiprocessing.Pool(num_worker_processes) as pool:
        pool.apply_async(worker, (queue,))

    with open(file_name_solve, 'r') as file:
        first_line = file.readline().strip()

        if first_line.startswith('p cnf'):
            print("input file is a CNF file")
            cube(file_name_solve, "N", 0, mg, order, numMCTS, queue, cutoff, int(cutoffv), 0, "False", solver_opts)
        else:
            print("input file contains name of multiple CNF file, solving them first")
            instance_lst = [first_line] + [line.strip() for line in file]
            for instance in instance_lst:
                command = f"./solve-verify.sh {solver_opts} {order} {instance}"
                queue.put(command)

    queue.join()

    for _ in range(num_worker_processes):
        queue.put(None)

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    
    # Parse named arguments
    parsed_args = {}
    i = 0
    while i < len(args):
        if args[i].startswith('--'):
            if i + 1 < len(args) and not args[i + 1].startswith('--'):
                parsed_args[args[i]] = args[i + 1]
                i += 2
            else:
                parsed_args[args[i]] = args[i]
                i += 1
        else:
            if 'order' not in parsed_args:
                parsed_args['order'] = args[i]
            elif 'file_name_solve' not in parsed_args:
                parsed_args['file_name_solve'] = args[i]
            i += 1

    # Extract main arguments
    main_args = [
        parsed_args.get('order'),
        parsed_args.get('file_name_solve'),
        parsed_args.get('--numMCTS', 2),
        parsed_args.get('--cutoff', 'd'),
        parsed_args.get('--cutoffv', 5),
        parsed_args.get('--solveaftercube', 'True')
    ]
    
    # Collect remaining args as solver_opts
    solver_opts = [arg for arg in args if arg.startswith('--') and 
                  arg not in ('--numMCTS', '--cutoff', '--cutoffv', '--solveaftercube')]
    
    main_args.append(solver_opts)
    main(*main_args)