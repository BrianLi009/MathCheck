import subprocess
import multiprocessing
import os

def run_command(args):
    command, order, directory, cube_initial, cube_next = args
    process_id = os.getpid()

    print(f"Process {process_id}: Executing command: {command}")
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()
    nextfile_pos = command.find("nextfile=")

    if nextfile_pos != -1:
        newfile = command[nextfile_pos + len("nextfile="):]
        
        print (newfile)
        if "UNSAT" not in stdout.decode():
            print("continue cubing this subproblem...")
            # Extract the string up to, but not including, "19-cubes"
            new_di = newfile.replace(order + "-cubes/", "")
            print (order, newfile, new_di, cube_next, cube_next, newfile)
            process_file((order, newfile, new_di, cube_next, cube_next, newfile))
        else:
            remove_related_files(newfile)
    else:
        print("next cubing file not found")

def process_file(args):
    order, file_name_solve, directory, cube_initial, cube_next, file_name_cube = args
    subprocess.run(f"./cube-solve-cc.sh {order} {file_name_solve} {directory} {cube_initial} {cube_next} {file_name_cube}", shell=True)
    with open(f"{file_name_solve}.commands", "r") as file:
        for line in file:
            print(line)
            queue.put((line.strip(), order, directory, cube_initial, cube_next))

def remove_related_files(new_file):
    base_file = new_file.rsplit('.', 1)[0]
    files_to_remove = [
        base_file,
        new_file,
        f"{new_file}.permcheck",
        f"{new_file}.nonembed",
        f"{new_file}.drat"
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
        run_command(args)
        queue.task_done()

def main(order, file_name_solve, directory, cube_initial, cube_next, file_name_cube):
    global queue
    queue = multiprocessing.JoinableQueue()
    num_worker_processes = multiprocessing.cpu_count()

    # Start worker processes
    processes = [multiprocessing.Process(target=worker, args=(queue,)) for _ in range(num_worker_processes)]
    for p in processes:
        p.start()

    process_file((order, file_name_solve, directory, cube_initial, cube_next, file_name_cube))

    # Wait for all tasks to be completed
    queue.join()

    # Stop workers
    for _ in processes:
        queue.put(None)
    for p in processes:
        p.join()

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 7:
        main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
    else:
        print("Usage: python script.py <order> <file_name_solve> <directory> <cube_initial> <cube_next> <file_name_cube>")
