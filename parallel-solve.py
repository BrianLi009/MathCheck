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
            eval(command)

    except Exception as e:
        print(f"Error in process {process_id}: {str(e)}")

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
        command = queue.get()
        if command is None:
            break
        run_command(command)
        queue.task_done()

def cube(file_name, mode, d, m, order, numMCTS, queue, cutoff, cutoffv, dg, simplify, solver_opts):
    if mode == "N":
        if cutoff == "d":
            if d >= cutoffv:
                command = f"./solve-verify.sh {solver_opts} {order} {file_name}"
                queue.put(command)
                return
        else:
            if m >= cutoffv:
                command = f"./solve-verify.sh {solver_opts} {order} {file_name}"
                queue.put(command)
                return

    # Create temporary files for cubing
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    temp_file_name = temp_file.name

    # Run march_cu
    march_command = f"./gen_cubes/march_cu/march_cu {file_name} -o {temp_file_name}"
    process = subprocess.Popen(march_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()

    if stderr:
        print(f"Error in march_cu: {stderr.decode()}")
        return

    # Process march_cu output
    with open(temp_file_name, 'r') as f:
        lines = f.readlines()

    for line in lines:
        if line.startswith('a'):
            # Create new file with cube
            new_file = f"{file_name}.{line[2:-1].replace(' ', '')}"
            with open(new_file, 'w') as f:
                f.write(f"p cnf {m} {d}\n")
                f.write(line[2:])

            # Simplify if needed
            if simplify == "True":
                simp_command = f"./simplification/simplify-by-conflicts.sh {solver_opts} {new_file} {order} 10000"
                process = subprocess.Popen(simp_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                stdout, stderr = process.communicate()

                if stderr:
                    print(f"Error in simplification: {stderr.decode()}")
                    continue

            # Recursive cube call
            cube(f"{new_file}.simp" if simplify == "True" else new_file, "N", d+1, m, order, numMCTS, queue, cutoff, cutoffv, dg, simplify, solver_opts)

    os.unlink(temp_file_name)

def main(*args):
    if len(args) < 5:
        print("Usage: python parallel-solve.py order file_name numMCTS cutoff cutoffv [simplify] [solver_opts]")
        return

    global mg, orderg, numMCTSg, cutoffg, cutoffvg, dg, solver_optsg
    mg = int(args[0])
    orderg = args[0]
    numMCTSg = args[2]
    cutoffg = args[3]
    cutoffvg = int(args[4])
    dg = 0
    solver_optsg = args[6] if len(args) > 6 else ""  # Get solver options if provided

    file_name_solve = args[1]
    simplify = args[5] if len(args) > 5 else "True"

    num_worker_processes = multiprocessing.cpu_count()
    queue = multiprocessing.JoinableQueue()

    with multiprocessing.Pool(num_worker_processes) as pool:
        pool.apply_async(worker, (queue,))

    with open(file_name_solve, 'r') as file:
        first_line = file.readline().strip()

        if first_line.startswith('p cnf'):
            print("input file is a CNF file")
            cube(file_name_solve, "N", 0, mg, orderg, numMCTSg, queue, cutoffg, cutoffvg, 0, simplify, solver_optsg)
        else:
            print("input file contains name of multiple CNF file, solving them first")
            instance_lst = [first_line] + [line.strip() for line in file]
            for instance in instance_lst:
                command = f"./solve-verify.sh {solver_optsg} {orderg} {instance}"
                queue.put(command)

    queue.join()

    for _ in range(num_worker_processes):
        queue.put(None)

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])
