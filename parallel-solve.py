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
        else:
            print("Continue cubing this subproblem...")
            command = f"cube('{file_to_cube}', {mg}, '{orderg}', {numMCTSg}, queue, '{cutoffg}', {cutoffvg}, {dg}, {ng})"
            queue.put(command)

    except Exception as e:
        print(f"Failed to run command due to: {str(e)}")

def run_cube_command(command):
    print (command)
    eval(command)

def process_file(args):
    order, file_name_solve, directory, cube_initial, cube_next, numMCTS = args
    if numMCTS == 0:
        subprocess.run(f"./cube-solve-cc.sh {order} {file_name_solve} {directory} {cube_initial} {cube_next}", shell=True)
    else:
        subprocess.run(f"./cube-solve-cc.sh -s {numMCTS} {order} {file_name_solve} {directory} {cube_initial} {cube_next}", shell=True)
    with open(f"{file_name_solve}.commands", "r") as file:
        for line in file:
            print(line)
            queue.put((line.strip(), order, directory, cube_initial, cube_next))

def process_initial(args):
    order, file_name_solve, directory, cube_initial, cube_next, commands, numMCTS = args
    with open(commands, "r") as file:
        for line in file:
            print(line)
            queue.put((line.strip(), order, directory, cube_initial, cube_next, numMCTS))

def remove_related_files(new_file):
    base_file = new_file.rsplit('.', 1)[0]
    files_to_remove = [
        base_file,
        new_file,
        #f"{new_file}.permcheck",
        f"{new_file}.nonembed",
        f"{new_file}.drat",
        f"{base_file}.drat"
    ]

    for file in files_to_remove:
        try:
            os.remove(file)
            print(f"Removed: {file}")
        except OSError as e:
            print(f"Error: {e.strerror}. File: {file}")

def worker(queue):
    while True:
        args = queue.get()
        if args is None:
            break
        if args.startswith("./maplesat"):
            run_command(args)
        else:
            run_cube_command(args)
        queue.task_done()

def cube(file_to_cube, m, order, numMCTS, queue, cutoff='d', cutoffv=5, d=0, n=0):
    if cutoff == 'd':
        if d > cutoffv:
            command = f"./maplesat-solve-verify.sh {order} {file_to_cube}"
            run_command(command)
            return
    if cutoff == 'n':
        if n > cutoffv:
            command = f"./maplesat-solve-verify.sh {order} {file_to_cube}"
            run_command(command)
            return
    subprocess.run(f"python -u alpha-zero-general/main.py {file_to_cube} -d 1 -m {m} -o {file_to_cube}.cubes -order {order} -prod -numMCTSSims {numMCTS}", shell=True)
    #for i in number of line in 
    with open(f"{file_to_cube}.cubes", 'r') as file:
        lines = file.readlines()
    if len(lines) == 1:
        subprocess.run(['rm', '-f', file_to_cube + ".cubes"], check=True)
        command = f"./maplesat-solve-verify.sh {order} {file_to_cube}"
        run_command(command)
        return
    subprocess.run(f"./gen_cubes/apply.sh {file_to_cube} {file_to_cube}.cubes 1 > {file_to_cube}{1}", shell=True)
    subprocess.run(f"./gen_cubes/apply.sh {file_to_cube} {file_to_cube}.cubes 2 > {file_to_cube}{2}", shell=True)
    subprocess.run(['rm', '-f', file_to_cube], check=True)
    subprocess.run(['rm', '-f', file_to_cube + ".cubes"], check=True)
    d += 1
    n += 2
    command1 = f"cube('{file_to_cube}{1}', {m}, '{order}', {numMCTS}, queue, '{cutoff}', {cutoffv}, {d}, {n})"
    command2 = f"cube('{file_to_cube}{2}', {m}, '{order}', {numMCTS}, queue, '{cutoff}', {cutoffv}, {d}, {n})"
    queue.put(command1)
    queue.put(command2)

def main(order, file_name_solve, directory, numMCTS=2, cutoff='d', cutoffv=5, d=0, n=0):
    m = int(int(order)*(int(order)-1)/2)
    global queue, orderg, numMCTSg, cutoffg, cutoffvg, dg, ng, mg
    orderg, numMCTSg, cutoffg, cutoffvg, dg, ng, mg = order, numMCTS, cutoff, cutoffv, d, n, m
    queue = multiprocessing.JoinableQueue()
    num_worker_processes = multiprocessing.cpu_count()

    # Start worker processes
    processes = [multiprocessing.Process(target=worker, args=(queue,)) for _ in range(num_worker_processes)]
    for p in processes:
        p.start()

    cube(file_name_solve, m, order, numMCTS, queue, cutoff, cutoffv, d, n)

    #process_initial((order, file_name_solve, directory, cube_initial, cube_next, commands, numMCTS))

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
