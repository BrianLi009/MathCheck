import subprocess
import multiprocessing
import os

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
        else:
            print("Continue cubing this subproblem...")
            command = f"cube('{file_to_cube}', {mg}, '{orderg}', {numMCTSg}, queue, '{cutoffg}', {cutoffvg}, {dg}, {ng})"
            queue.put(command)

    except Exception as e:
        print(f"Failed to run command due to: {str(e)}")

def run_cube_command(command):
    print (command)
    eval(command)

def remove_related_files(new_file):
    files_to_remove = [
        new_file,
        #f"{new_file}.permcheck",
        #f"{new_file}.nonembed",
        f"{new_file}.drat",
        #f"{base_file}.drat"
    ]

    for file in files_to_remove:
        try:
            os.remove(file)
            print(f"Removed: {file}")
        except OSError as e:
            print(f"Error: {e.strerror}. File: {file}")

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
        if args.startswith("./solve-verify"):
            run_command(args)
        else:
            run_cube_command(args)
        queue.task_done()

def cube(file_to_cube, m, order, numMCTS, queue, cutoff='d', cutoffv=5, d=0, n=0, v=0):
    command = f"./cadical-ks/build/cadical-ks {file_to_cube} --order {order} --unembeddable-check 17 -o {file_to_cube}.simp -e {file_to_cube}.ext -n -c 10000 | tee {file_to_cube}.simplog"
    # Run the command and capture the output
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Decode the output and error to utf-8
    output = result.stdout.decode('utf-8') + result.stderr.decode('utf-8')

    # Check if the output contains "c exit 20"
    if "c exit 20" in output:
        os.remove(file_to_cube)
        os.remove(f'{file_to_cube}.simp')
        print("the cube is UNSAT")
        return
    else:
        n += 1

    if file_to_cube != file_name_solveg:
        previous_ext = file_to_cube[:-1] + ".ext"
        command = f'cat {previous_ext} >> {file_to_cube}.ext'
        subprocess.run(command, shell=True)

    command = f"sed -E 's/.* 0 [-]*([0-9]*) 0$/\\1/' < {file_to_cube}.ext | awk '$0<={mg}' | sort | uniq | wc -l"

    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    var_removed = int(result.stdout.strip())

    print (f'{var_removed} variables removed from the cube')

    subprocess.run(['rm', '-f', file_to_cube], check=True)
    os.rename(f"{file_to_cube}.simp", rename_file(file_to_cube))

    if cutoff == 'd':
        if d >= cutoffv:
            if solveaftercubeg == 'True':
                command = f"./solve-verify.sh {order} {file_to_cube}"
                queue.put(command)
            return
    if cutoff == 'n':
        if n >= cutoffv:
            if solveaftercubeg == 'True':
                command = f"./solve-verify.sh {order} {file_to_cube}"
                queue.put(command)
            return
    if cutoff == 'v':
        if var_removed >= cutoffv:
            if solveaftercubeg == 'True':
                command = f"./solve-verify.sh {order} {file_to_cube}"
                queue.put(command)
            return
    if int(numMCTS) == 0:
        subprocess.run(f"./gen_cubes/march_cu/march_cu {file_to_cube} -o {file_to_cube}.cubes -d 1 -m {m}", shell=True)
    else:
        subprocess.run(f"python -u alpha-zero-general/main.py {file_to_cube} -d 1 -m {m} -o {file_to_cube}.cubes -order {order} -prod -numMCTSSims {numMCTS}", shell=True)
    subprocess.run(f"./gen_cubes/apply.sh {file_to_cube} {file_to_cube}.cubes 1 > {file_to_cube}{0}", shell=True)
    subprocess.run(f"./gen_cubes/apply.sh {file_to_cube} {file_to_cube}.cubes 2 > {file_to_cube}{1}", shell=True)
    subprocess.run(['rm', '-f', file_to_cube], check=True)
    subprocess.run(['rm', '-f', file_to_cube + ".cubes"], check=True)
    d += 1
    command1 = f"cube('{file_to_cube}{0}', {m}, '{order}', {numMCTS}, queue, '{cutoff}', {cutoffv}, {d}, {n}, {var_removed})"
    command2 = f"cube('{file_to_cube}{1}', {m}, '{order}', {numMCTS}, queue, '{cutoff}', {cutoffv}, {d}, {n}, {var_removed})"
    queue.put(command1)
    queue.put(command2)

def main(order, file_name_solve, numMCTS=2, cutoff='d', cutoffv=5, solveaftercube='True'):

    d=0
    n=0
    v=0
    
    cutoffv = int(cutoffv)
    m = int(int(order)*(int(order)-1)/2)
    global queue, orderg, numMCTSg, cutoffg, cutoffvg, dg, ng, mg, solveaftercubeg, file_name_solveg
    orderg, numMCTSg, cutoffg, cutoffvg, dg, ng, mg, solveaftercubeg, file_name_solveg = order, numMCTS, cutoff, cutoffv, d, n, m, solveaftercube, file_name_solve
    queue = multiprocessing.JoinableQueue()
    num_worker_processes = multiprocessing.cpu_count()

    # Start worker processes
    processes = [multiprocessing.Process(target=worker, args=(queue,)) for _ in range(num_worker_processes)]
    for p in processes:
        p.start()

    #file_name_solve is a file where each line is a filename to solve
    with open(file_name_solve, 'r') as file:
        first_line = file.readline().strip()  # Read the first line and strip whitespace

        # Check if the first line starts with 'p cnf'
        if first_line.startswith('p cnf'):
            print("input file is a CNF file")
            cube(file_name_solve, m, order, numMCTS, queue, cutoff, cutoffv, d, n, v)
        else:
            print("input file contains name of multiple CNF file, solving them first")
            # Prepend the already read first line to the list of subsequent lines
            instance_lst = [first_line] + [line.strip() for line in file]
            for instance in instance_lst:
                command = f"./solve-verify.sh {order} {instance}"
                queue.put(command)

    # Wait for all tasks to be completed
    queue.join()

    # Stop workers
    for _ in processes:
        queue.put(None)
    for p in processes:
        p.join()

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])