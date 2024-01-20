import subprocess
import time

def test_script():
    with subprocess.Popen(['python3', 'parallel-solve.py'], 
                          stdout=subprocess.PIPE, 
                          text=True) as proc:
        
        while True:
            output = proc.stdout.readline()
            if not output:
                break
            print(output.strip())

if __name__ == "__main__":
    test_script()
