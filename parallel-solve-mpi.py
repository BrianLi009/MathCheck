from mpi4py import MPI
import subprocess
import os

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

def run_command(command, comm, rank):
    print(f"Process {rank}: Executing command: {command}")

    process_id = os.getpid()
    print(f"Process {process_id}: Executing command: {command}")

    file_to_cube = command.split()[-1]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()

    if stderr:
        print(f"Error executing command: {stderr.decode()}")

    if "UNSAT" in stdout.decode():
        print("solved")
        remove_related_files(file_to_cube)
    else:
        print("Continue cubing this subproblem...")
        #command = f"cube('{file_to_cube}', {mg}, '{orderg}', {numMCTSg}, comm, '{sg}', '{cutoffg}', {cutoffvg}, {dg}, {ng})"
        print(f"Process {rank}: Sending new cube task: {command}")
        comm.send(command, dest=0)  # Send to master for distribution

def run_cube_command(command):
    print (command)
    eval(command)

def remove_related_files(new_file):
    base_file = new_file.rsplit('.', 1)[0]
    files_to_remove = [
        base_file,
        new_file,
        #f"{new_file}.permcheck",
        f"{new_file}.nonembed",
        f"{new_file}.drat",
        #f"{base_file}.drat"
    ]

    for file in files_to_remove:
        try:
            os.remove(file)
            print(f"Removed: {file}")
        except OSError as e:
            print(f"Error: {e.strerror}. File: {file}")

def worker(comm, rank):
    while True:
        try:
            args = comm.recv(source=0)  # Receive task from master
            if args is None:
                break  # Exit signal

            if args.startswith("./maplesat"):
                run_command(args, comm, rank)
            else:
                run_cube_command(args)

            comm.send("Task completed", dest=0)  # Send completion signal

        except Exception as e:
            print(f"Process {rank}: Error: {str(e)}")
            comm.send(f"Error: {str(e)}", dest=0)  # Send error message to master


def cube(file_to_cube, m, order, numMCTS, comm, s='True', cutoff='d', cutoffv=5, d=0, n=0, v=0):
    rank = comm.Get_rank()
    print(f"Process {rank}: Cubing file {file_to_cube}")

    command = f"./cadical-ks/build/cadical-ks {file_to_cube} --order {order} --unembeddable-check 17 -o {file_to_cube}.simp -e {file_to_cube}.ext -n -c 10000 | tee {file_to_cube}.simplog"
    # Run the command and capture the output
    print (command)
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

    command = f"sed -E 's/.* 0 [-]*([0-9]*) 0$/\\1/' < {file_to_cube}.ext | awk '$0<={m}' | sort | uniq | wc -l"

    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    var_removed = v + int(result.stdout.strip())

    print (f'{var_removed} variables removed from the cube')
    original_file = file_to_cube
    file_to_cube = f"{file_to_cube}.simp"

    # Replace queue usage with direct calls
    if cutoff == 'd' and d >= cutoffv and s == 'True':
        command = f"./maplesat-solve-verify.sh {order} {file_to_cube}"
        print(f"Process {rank}: Sending solve-verify command: {command}")
        comm.send(command, dest=0)  # Send to master
    elif cutoff == 'n' and n >= cutoffv and s == 'True':
        command = f"./maplesat-solve-verify.sh {order} {file_to_cube}"
        print(f"Process {rank}: Sending solve-verify command: {command}")
        comm.send(command, dest=0)  # Send to master
    elif cutoff == 'v' and v >= cutoffv and s == 'True':
        command = f"./maplesat-solve-verify.sh {order} {file_to_cube}"
        print(f"Process {rank}: Sending solve-verify command: {command}")
        comm.send(command, dest=0)  # Send to master
    else:
        if int(numMCTS) == 0:
            subprocess.run(f"./gen_cubes/march_cu/march_cu {file_to_cube} -o {file_to_cube}.cubes -d 1 -m {m}", shell=True)
        else:
            subprocess.run(f"python -u alpha-zero-general/main.py {file_to_cube} -d 1 -m {m} -o {file_to_cube}.cubes -order {order} -prod -numMCTSSims {numMCTS}", shell=True)
        subprocess.run(f"./gen_cubes/apply.sh {file_to_cube} {file_to_cube}.cubes 1 > {file_to_cube}{1}", shell=True)
        subprocess.run(f"./gen_cubes/apply.sh {file_to_cube} {file_to_cube}.cubes 2 > {file_to_cube}{2}", shell=True)
        subprocess.run(['rm', '-f', original_file], check=True)
        subprocess.run(['rm', '-f', file_to_cube], check=True)
        subprocess.run(['rm', '-f', file_to_cube + ".cubes"], check=True)
        d += 1
        command1 = f"cube('{file_to_cube}{1}', {m}, '{order}', {numMCTS}, comm, '{s}', '{cutoff}', {cutoffv}, {d}, {n}, {var_removed})"
        command2 = f"cube('{file_to_cube}{2}', {m}, '{order}', {numMCTS}, comm, '{s}', '{cutoff}', {cutoffv}, {d}, {n}, {var_removed})"
        print(f"Process {rank}: Sending new tasks: {command1}, {command2}")
        comm.send(command1, dest=0)  # Send to master for distribution
        comm.send(command2, dest=0)


def main(order, file_name_solve, numMCTS=2, s='True', cutoff='d', cutoffv=5, d=0, n=0, v=0):
    cutoffv = int(cutoffv)
    m = int(int(order) * (int(order) - 1) / 2)

    if rank == 0:
        # Master process
        tasks = [(file_name_solve, m, order, numMCTS, s, cutoff, cutoffv, d, n, v)]
        for task in tasks:
            comm.send(task, dest=rank + 1)
    else:
        # Worker processes
        while True:
            task = comm.recv(source=0)
            if task is None:
                break
            file_to_cube, m, order, numMCTS, s, cutoff, cutoffv, d, n, v = task
            cube(file_to_cube, m, order, numMCTS, comm, s, cutoff, cutoffv, d, n, v)
            comm.send(None, dest=0)  # Signal completion to master

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])