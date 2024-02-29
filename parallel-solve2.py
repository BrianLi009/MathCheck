import subprocess
import multiprocessing
import os
import sys

class CommandProcessor:
    def __init__(self, order, numMCTS, cutoff, cutoffv, d, m, solveaftercube, file_name_solve, queue):
        self.order = order
        self.numMCTS = numMCTS
        self.cutoff = cutoff
        self.cutoffv = cutoffv
        self.d = d
        self.m = m
        self.solveaftercube = solveaftercube
        self.file_name_solve = file_name_solve
        self.queue = queue
        self.local_cutoff = cutoffv

    def run_command(self, command):
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
                self.remove_related_files(file_to_cube)
            else:
                print("Continue cubing this subproblem...")
                self.local_cutoff += 40  # Update local_cutoff for this instance
                command = f"cube('{file_to_cube}', {self.m}, '{self.order}', {self.numMCTS}, self.queue, '{self.cutoff}', {self.local_cutoff}, {self.d})"
                self.queue.put(command)

        except Exception as e:
            print(f"Failed to run command due to: {str(e)}")

    def cube(self, file_to_cube, m, order, numMCTS, queue, cutoff='d', cutoffv=5, d=0, v=0):
        command = f"./simplification/simplify-by-conflicts.sh -s {file_to_cube} {order} 10000 | tee {file_to_cube}.simplog"
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

        if file_to_cube != self.file_name_solve:
            previous_ext = file_to_cube[:-1] + ".ext"
            command = f'cat {previous_ext} >> {file_to_cube}.ext'
            subprocess.run(command, shell=True)

        command = f"sed -E 's/.* 0 [-]*([0-9]*) 0$/\\1/' < {file_to_cube}.ext | awk '$0<={self.m}' | sort | uniq | wc -l"

        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        var_removed = int(result.stdout.strip())

        print (f'{var_removed} variables removed from the cube')

        subprocess.run(['rm', '-f', file_to_cube], check=True)
        os.rename(f"{file_to_cube}.simp", rename_file(file_to_cube))
        file_to_cube = rename_file(file_to_cube)

        if cutoff == 'd':
            if d >= cutoffv:
                if self.solveaftercube == 'True':
                    command = f"./solve-verify.sh {order} {file_to_cube}"
                    queue.put(command)
                return
        if cutoff == 'v':
            if var_removed >= cutoffv:
                if self.solveaftercube == 'True':
                    command = f"./solve-verify.sh {order} {file_to_cube}"
                    queue.put(command)
                return
        if int(numMCTS) == 0:
            subprocess.run(f"./gen_cubes/march_cu/march_cu {file_to_cube} -o {file_to_cube}.cubes -d 1 -m {m}", shell=True)
        else:
            subprocess.run(f"python -u alpha-zero-general/main.py {file_to_cube} -d 1 -m {m} -o {file_to_cube}.cubes -order {order} -prod -numMCTSSims {numMCTS}", shell=True)
        subprocess.run(f"./gen_cubes/apply.sh {file_to_cube} {file_to_cube}.cubes 1 > {file_to_cube}{0}", shell=True)
        subprocess.run(f"./gen_cubes/apply.sh {file_to_cube} {file_to_cube}.cubes 2 > {file_to_cube}{1}", shell=True)
        subprocess.run(['rm', '-f', file_to_cube], check=True)
        subprocess.run(['rm', '-f', file_to_cube + ".cubes"], check=True)
        d += 1
        command1 = f"cube('{file_to_cube}{0}', {m}, '{order}', {numMCTS}, queue, '{cutoff}', {cutoffv}, {d}, {var_removed})"
        command2 = f"cube('{file_to_cube}{1}', {m}, '{order}', {numMCTS}, queue, '{cutoff}', {cutoffv}, {d}, {var_removed})"
        queue.put(command1)
        queue.put(command2)

    @staticmethod
    def remove_related_files(new_file):
        files_to_remove = [
            new_file,
            f"{new_file}.perm",
            f"{new_file}.nonembed",
            f"{new_file}.drat",
        ]

        for file in files_to_remove:
            try:
                os.remove(file)
                print(f"Removed: {file}")
            except OSError as e:
                print(f"Error: {e.strerror}. File: {file}")

def worker(queue, command_processor):
    while True:
        args = queue.get()
        if args is None:
            queue.task_done()
            break
        if args.startswith("./solve-verify"):
            command_processor.run_command(args)
        else:
            print(args)  # Placeholder for run_cube_command
        queue.task_done()

def rename_file(filename):
    # Remove .simp from file name
    
    if filename.endswith('.simp'):
        filename = filename[:-5]
    
    return filename

def main(order, file_name_solve, numMCTS=2, cutoff='d', cutoffv=5, solveaftercube='True'):
    d=0 
    
    cutoffv = int(cutoffv)
    m = int(int(order)*(int(order)-1)/2)
    queue = multiprocessing.JoinableQueue()
    num_worker_processes = multiprocessing.cpu_count()

    # Create an instance of CommandProcessor
    command_processor = CommandProcessor(order, numMCTS, cutoff, cutoffv, d, m, solveaftercube, file_name_solve, queue)

    # Start worker processes
    processes = [multiprocessing.Process(target=worker, args=(queue, command_processor)) for _ in range(num_worker_processes)]
    for p in processes:
        p.start()

    # Example of putting a command in the queue
    command = f"./solve-verify.sh {order} example_file"
    queue.put(command)

    # Wait for all tasks to be completed
    queue.join()

    # Stop workers
    for _ in processes:
        queue.put(None)
    for p in processes:
        p.join()

if __name__ == "__main__":
    main(*sys.argv[1:])
