from mpi4py import MPI
import subprocess
import os

def run_command(command):
    """Function to execute a given command and return its output."""
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()
        return stdout.decode(), stderr.decode()
    except Exception as e:
        return None, str(e)

def mpi_root(mpi_comm, tasks):
    """Distribute tasks to workers and collect results."""
    # Scatter tasks to all processes (including root)
    distributed_tasks = mpi_comm.scatter(tasks, root=0)

    # Root also executes its part of the task
    root_result = run_command(distributed_tasks)

    # Gather results from all processes
    results = mpi_comm.gather(root_result, root=0)

    # Process results
    for result in results:
        stdout, stderr = result
        if stderr:
            print(f"Error: {stderr}")
        else:
            print(f"Output: {stdout}")

def mpi_nonroot(mpi_comm):
    """Receive a task, execute it, and return the result."""
    # Receive a task distributed by the root
    task = mpi_comm.scatter(None, root=0)

    # Execute the task and collect the result
    result = run_command(task)

    # Send the result back to the root
    mpi_comm.gather(result, root=0)

def main():
    mpi_comm = MPI.COMM_WORLD
    mpi_rank = mpi_comm.Get_rank()

    # Example: Define tasks (commands) to be distributed
    if mpi_rank == 0:
        tasks = ["ls", "whoami", "hostname"] * mpi_comm.Get_size()
    else:
        tasks = None

    # Root process distributes tasks and collects results
    if mpi_rank == 0:
        mpi_root(mpi_comm, tasks)
    else:
        mpi_nonroot(mpi_comm)

if __name__ == "__main__":
    main()
