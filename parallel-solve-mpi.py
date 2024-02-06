from mpi4py import MPI
import subprocess
import os
import sys

def run_command(command):
    comm = MPI.COMM_WORLD
    process_id = comm.Get_rank()
    print(f"Process {process_id}: Starting execution of run_command function.")

    file_to_cube = command.split()[-1]
    print(f"Process {process_id}: Target file for cubing is {file_to_cube}.")

    try:
        print(f"Process {process_id}: Preparing to execute command.")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()
        print(f"Process {process_id}: Command execution completed.")

        if stderr:
            error_msg = f"Error executing command: {stderr.decode()}"
            print(error_msg)
            if process_id != 0:
                print(f"Process {process_id}: Reporting error to master process.")
                comm.send({"type": "error", "message": error_msg, "pid": process_id}, dest=0, tag=2)
        else:
            output = stdout.decode()
            print(f"Process {process_id}: Command executed successfully.")
            if "UNSAT" in output:
                print(f"Process {process_id}: Cube is unsolvable. Removing related files.")
                remove_related_files(file_to_cube)
                if process_id != 0:
                    print(f"Process {process_id}: Reporting success to master process.")
                    comm.send({"type": "success", "message": "solved", "pid": process_id, "file": file_to_cube}, dest=0, tag=2)
            else:
                print(f"Process {process_id}: Cube is solvable. Continue processing.")
    except Exception as e:
        error_msg = f"Failed to run command due to: {str(e)}"
        print(error_msg)
        if process_id != 0:
            print(f"Process {process_id}: Reporting exception to master process.")
            comm.send({"type": "exception", "message": error_msg, "pid": process_id}, dest=0, tag=2)

def remove_related_files(new_file):
    base_file = new_file.rsplit('.', 1)[0]
    files_to_remove = [
        base_file,
        new_file,
        f"{new_file}.nonembed",
        f"{new_file}.drat",
    ]
    print(f"Preparing to remove files related to {new_file}.")
    for file in files_to_remove:
        try:
            os.remove(file)
            print(f"Removed: {file}")
        except OSError as e:
            print(f"Error: {e.strerror}. File: {file}")

def mpi_cube(file_to_cube, m, order, numMCTS, rank, size, s='True', cutoff='d', cutoffv=5, d=0, n=0, v=0):
    comm = MPI.COMM_WORLD
    print(f"Process {rank}: Starting mpi_cube function.")
    command = f"./cadical-ks/build/cadical-ks {file_to_cube} --order {order} --unembeddable-check 17 -o {file_to_cube}.simp -e {file_to_cube}.ext -n -c 10000 | tee {file_to_cube}.simplog"
    print(f"Process {rank}: Running cube command.")
    try:
        print(f"Process {rank}: {command}")
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode('utf-8') + result.stderr.decode('utf-8')
        print(f"Process {rank}: Cube command completed.")

        if "c exit 20" in output:
            print(f"Process {rank}: the cube is UNSAT. Notifying master process.")
            comm.send({"type": "UNSAT", "file": file_to_cube, "rank": rank}, dest=0, tag=3)
        else:
            print(f"Process {rank}: Cube processing continues. Notifying master process for further instructions.")
            comm.send({"type": "continue", "file": file_to_cube, "rank": rank}, dest=0, tag=3)
    except Exception as e:
        print(f"Process {rank}: Failed to run cube command due to: {str(e)}")
        comm.send({"type": "error", "message": str(e), "file": file_to_cube, "rank": rank}, dest=0, tag=3)

def mpi_main(order, file_name_solve, numMCTS=2, s='True', cutoff='d', cutoffv=5, d=0, n=0, v=0):
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    print(f"Process {rank}: Starting mpi_main function with order {order} and file {file_name_solve}.")
    m = int(int(order)*(int(order)-1)/2)
    if rank == 0:
        print("Master process: Distributing tasks.")
        tasks = [file_name_solve]  # Simplified task list
        for i, task in enumerate(tasks, start=1):
            if i < size:
                print(f"Master process: Sending task {task} to process {i}.")
                comm.send(task, dest=i, tag=1)
            else:
                break
    else:
        status = MPI.Status()
        while True:
            print(f"Process {rank}: Waiting for task.")
            task = comm.recv(source=0, tag=MPI.ANY_TAG, status=status)
            if status.Get_tag() == 1:
                print(f"Process {rank}: Received task {task}. Executing mpi_cube.")
                mpi_cube(task, m, order, numMCTS, rank, size, s, cutoff, cutoffv, d, n, v)
            elif status.Get_tag() == 0:
                print(f"Process {rank}: Received termination signal. Exiting.")
                break

    print(f"Process {rank}: Finalizing MPI.")
    MPI.Finalize()

if __name__ == "__main__":
    mpi_main(*sys.argv[1:])
