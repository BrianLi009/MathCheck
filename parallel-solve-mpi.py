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
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()

        if stderr:
            error_msg = f"Error executing command: {stderr.decode()}"
            print(error_msg)
            # Optionally send error message back to the master process
            if process_id != 0:  # Check to ensure not the master process itself
                comm.send({"type": "error", "message": error_msg, "pid": process_id}, dest=0, tag=2)
        else:
            output = stdout.decode()
            if "UNSAT" in output:
                print("solved")
                remove_related_files(file_to_cube)
                # Optionally send success message back to the master process
                if process_id != 0:
                    comm.send({"type": "success", "message": "solved", "pid": process_id, "file": file_to_cube}, dest=0, tag=2)
            else:
                print("Continue cubing this subproblem...")
                # Further task distribution logic or communication with the master process can be added here
                # This part needs to be adapted based on how you plan to manage distributed tasks and their results

    except Exception as e:
        error_msg = f"Failed to run command due to: {str(e)}"
        print(error_msg)
        # Optionally send exception message back to the master process
        if process_id != 0:
            comm.send({"type": "exception", "message": error_msg, "pid": process_id}, dest=0, tag=2)


def remove_related_files(new_file):
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
    command = f"./cadical-ks/build/cadical-ks {file_to_cube} --order {order} --unembeddable-check 17 -o {file_to_cube}.simp -e {file_to_cube}.ext -n -c 10000 | tee {file_to_cube}.simplog"
    try:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode('utf-8') + result.stderr.decode('utf-8')
        
        if "c exit 20" in output:
            print(f"Process {rank}: the cube is UNSAT")
            # Send a message to the master process about the UNSAT result
            comm.send({"type": "UNSAT", "file": file_to_cube, "rank": rank}, dest=0, tag=3)
        else:
            # If further action is needed, such as distributing subtasks or notifying the master process of continuation
            print(f"Process {rank}: Continue processing {file_to_cube}")
            # Example: Send a message to the master process to indicate continuation or request further instructions
            comm.send({"type": "continue", "file": file_to_cube, "rank": rank}, dest=0, tag=3)
            # Additional logic to handle continuation, like further cube operations or task distributions, would be added here

    except Exception as e:
        print(f"Process {rank}: Failed to run cube command due to: {str(e)}")
        # Send a message to the master process about the failure
        comm.send({"type": "error", "message": str(e), "file": file_to_cube, "rank": rank}, dest=0, tag=3)


def mpi_main(order, file_name_solve, numMCTS=2, s='True', cutoff='d', cutoffv=5, d=0, n=0, v=0):
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    if rank == 0:
        m = int(int(order)*(int(order)-1)/2)
        tasks = [file_name_solve]  # Simplified task list
        
        for i, task in enumerate(tasks, start=1):
            if i < size:
                comm.send(task, dest=i, tag=1)
            else:
                break
    else:
        status = MPI.Status()
        while True:
            task = comm.recv(source=0, tag=MPI.ANY_TAG, status=status)
            if status.Get_tag() == 1:
                mpi_cube(task, m, order, numMCTS, rank, size, s, cutoff, cutoffv, d, n, v)
            elif status.Get_tag() == 0:
                break

    MPI.Finalize()

if __name__ == "__main__":
    mpi_main(*sys.argv[1:])

