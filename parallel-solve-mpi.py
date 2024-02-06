from mpi4py import MPI
import subprocess
import os
import sys

def run_command(command):
    comm = MPI.COMM_WORLD
    process_id = comm.Get_rank()
    print(f"Process {process_id}: Executing command: {command}")

    file_to_cube = command.split()[-1]

    try:
        print(f"Process {process_id}: Starting subprocess for command execution.")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()
        print(f"Process {process_id}: Command executed, processing output.")

        if stderr:
            error_msg = f"Error executing command: {stderr.decode()}"
            print(error_msg)
            if process_id != 0:
                comm.send({"type": "error", "message": error_msg, "pid": process_id}, dest=0, tag=2)
        else:
            output = stdout.decode()
            if "UNSAT" in output:
                print(f"Process {process_id}: Problem solved. UNSAT found.")
                remove_related_files(file_to_cube)
                if process_id != 0:
                    comm.send({"type": "success", "message": "solved", "pid": process_id, "file": file_to_cube}, dest=0, tag=2)
            else:
                print(f"Process {process_id}: No solution found, continue processing.")
                # Further task distribution logic or communication with the master process can be added here

    except Exception as e:
        error_msg = f"Failed to run command due to: {str(e)}"
        print(error_msg)
        if process_id != 0:
            comm.send({"type": "exception", "message": error_msg, "pid": process_id}, dest=0, tag=2)


def remove_related_files(new_file):
    print(f"Starting cleanup for: {new_file}")
    base_file = new_file.rsplit('.', 1)[0]
    files_to_remove = [
        base_file,
        new_file,
        f"{new_file}.nonembed",
        f"{new_file}.drat",
    ]

    for file in files_to_remove:
        try:
            os.remove(file)
            print(f"Removed: {file}")
        except OSError as e:
            print(f"Error: {e.strerror}. File: {file}")

def mpi_cube(file_to_cube, m, order, numMCTS, rank, size, s='True', cutoff='d', cutoffv=5, d=0, n=0, v=0):
    comm = MPI.COMM_WORLD
    print(f"Process {rank}: Preparing to cube {file_to_cube}")
    command = f"./cadical-ks/build/cadical-ks {file_to_cube} --order {order} --unembeddable-check 17 -o {file_to_cube}.simp -e {file_to_cube}.ext -n -c 10000 | tee {file_to_cube}.simplog"
    try:
        print(f"Process {rank}: Running cubing command.")
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode('utf-8') + result.stderr.decode('utf-8')
        print(f"Process {rank}: Command execution finished, analyzing output.")

        if "c exit 20" in output:
            print(f"Process {rank}: Cube determined to be UNSAT.")
            comm.send({"type": "UNSAT", "file": file_to_cube, "rank": rank}, dest=0, tag=3)
        else:
            print(f"Process {rank}: Cube requires further processing.")
            comm.send({"type": "continue", "file": file_to_cube, "rank": rank}, dest=0, tag=3)

    except Exception as e:
        print(f"Process {rank}: Failed to run cube command due to: {str(e)}")
        comm.send({"type": "error", "message": str(e), "file": file_to_cube, "rank": rank}, dest=0, tag=3)


def mpi_main(order, file_name_solve, numMCTS=2, s='True', cutoff='d', cutoffv=5, d=0, n=0, v=0):
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    print(f"Master process initializing with {size} processes.")
    m = int(int(order)*(int(order)-1)/2)
    if rank == 0:
        tasks = [file_name_solve]
        print("Master process distributing tasks.")
        
        for i, task in enumerate(tasks, start=1):
            if i < size:
                print(f"Sending task to process {i}.")
                comm.send(task, dest=i, tag=1)
            else:
                break
        print("Master process finished task distribution.")
    else:
        status = MPI.Status()
        print(f"Process {rank} waiting for tasks.")
        while True:
            task = comm.recv(source=0, tag=MPI.ANY_TAG, status=status)
            if status.Get_tag() == 1:
                print(f"Process {rank} received task, starting processing.")
                mpi_cube(task, m, order, numMCTS, rank, size, s, cutoff, cutoffv, d, n, v)
            elif status.Get_tag() == 0:
                print(f"Process {rank} received termination signal, exiting.")
                break

    MPI.Finalize()

if __name__ == "__main__":
    mpi_main(*sys.argv[1:])
