from mpi4py import MPI
import subprocess
import os
import time  # Used for simulating processing time

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

print(f"Hello from process {rank}")


def run_cube_command(instance_id):
    print(f"Process {rank}: Cubing instance {instance_id}...")
    # Simulate cubing process
    time.sleep(1)  # Simulate some processing time
    needs_more_cubing = True  # Simulate decision: even ranks need more cubing, odd ranks don't
    print(f"Process {rank}: Cubing done. Needs more cubing: {needs_more_cubing}")
    comm.send((rank, instance_id, "cube_done", needs_more_cubing), dest=0, tag=0)

def run_solve_command(instance_id):
    print(f"Process {rank}: Solving cube {instance_id}...")
    # Simulate solving process
    time.sleep(1)  # Simulate some processing time
    too_hard_to_solve = rank % 3 == 0  # Simulate decision: every third rank finds it too hard to solve
    print(f"Process {rank}: Solving done. Too hard to solve: {too_hard_to_solve}")
    comm.send((rank, instance_id, "solve_done", too_hard_to_solve), dest=0, tag=0)

def manager(sat_instance):
    tasks = {"cube": [sat_instance]}
    solved_instances = []
    cube_history = {}

    while tasks["cube"] or tasks.get("solve", []):
        new_cube_tasks = []
        new_solve_tasks = []

        for instance_id in tasks["cube"]:
            for i in range(1, size):
                comm.send(("cube", instance_id), dest=i, tag=0)
                cube_history[instance_id] = {"status": "cubing", "worker": i}
                break

        for instance_id in tasks.get("solve", []):
            for i in range(1, size):
                if cube_history.get(instance_id, {}).get("status") != "cubing":
                    comm.send(("solve", instance_id), dest=i, tag=0)
                    cube_history[instance_id] = {"status": "solving", "worker": i}
                    break

        tasks["cube"] = new_cube_tasks
        tasks["solve"] = new_solve_tasks

        # Collect results and decide on next steps
        while cube_history:
            received_data = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG)
            worker_rank, instance_id, task_done, needs_action = received_data
            if task_done == "cube_done":
                if needs_action:
                    tasks["cube"].append(instance_id)
                else:
                    tasks["solve"].append(instance_id)
            elif task_done == "solve_done":
                if needs_action:
                    tasks["cube"].append(instance_id)
                else:
                    solved_instances.append(instance_id)
                    del cube_history[instance_id]

    print("All instances solved:", solved_instances)

if rank == 0:
    sat_instance = "SAT_instance_identifier"
    manager(sat_instance)
else:
    while True:
        received_task = comm.recv(source=0, tag=0)
        print (received_task)
        if received_task[0] == "cube":
            print ("recieved cubing task")
            run_cube_command(received_task[1])
        elif received_task[0] == "solve":
            print ("recieved solving task")
            run_solve_command(received_task[1])
        else:
            break  # Exit the loop if no valid task is received
