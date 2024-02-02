import subprocess
import multiprocessing
import os

def run_command(args):
    command, order, directory, cube_initial, cube_next, numMCTS = args
    process_id = os.getpid()

    print(f"Process {process_id}: Executing command: {command}")
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()
    nextfile_pos = command.find("nextfile=")

    if nextfile_pos != -1:
        newfile = command[nextfile_pos + len("nextfile="):]
        
        print (newfile)
        if "UNSAT" in stdout.decode():
            print ("removing files no longer needed for" + newfile)
            remove_related_files(newfile)
        else:
            print("continue cubing this subproblem...")
            # Extract the string up to, but not including, "19-cubes"
            new_di = newfile.replace(order + "-cubes/", "")
            print (order, newfile, new_di, cube_next, cube_next)
            process_file((order, newfile, new_di, cube_next, cube_next, numMCTS))
    else:
        print("next cubing file not found")

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
        print (args)
        if isinstance(args, str):
            run_cube_command(args)
        else:
            run_command(args)
        queue.task_done()

def cube(file_to_cube, m, order, numMCTS, logdir, queue):
    subprocess.run(f"python -u alpha-zero-general/main.py {file_to_cube} -d 1 -m {m} -o {file_to_cube}.cubes -order {order} -prod -numMCTSSims {numMCTS}", shell=True)
    #for i in number of line in 
    with open({file_to_cube}.cubes, 'r') as file:
        lines = file.readlines()
    if len(lines) == 1:
        return
    subprocess.run(f"./gen_cubes/apply.sh {file_to_cube} {file_to_cube}.cubes 1 > {file_to_cube}{1}", shell=True)
    subprocess.run(f"./gen_cubes/apply.sh {file_to_cube} {file_to_cube}.cubes 2 > {file_to_cube}{2}", shell=True)
    command1 = f"cube('{file_to_cube}{1}', {m}, '{order}', {numMCTS}, '{logdir}', queue)"
    command2 = f"cube('{file_to_cube}{2}', {m}, '{order}', {numMCTS}, '{logdir}', queue)"
    queue.put(command1)
    queue.put(command2)

def main(order, file_name_solve, directory, cube_initial, cube_next, numMCTS=2):
    global queue
    queue = multiprocessing.JoinableQueue()
    num_worker_processes = multiprocessing.cpu_count()

    m = int(int(order)*(int(order)-1)/2)
    logdir = f"{directory}/{order}-log"

    # Start worker processes
    processes = [multiprocessing.Process(target=worker, args=(queue,)) for _ in range(num_worker_processes)]
    for p in processes:
        p.start()

    cube(file_name_solve, m, order, numMCTS, logdir, queue)

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
    if len(sys.argv) == 7:
        main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
    elif len(sys.argv) >= 6:
        main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    else:
        print("Usage: python script.py <order> <file_name_solve> <directory> <cube_initial> <cube_next>")
