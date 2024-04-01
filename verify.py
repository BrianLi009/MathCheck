import os
import sys
def enumerate_files(folder_name, filename):
    filename_1 = f'{folder_name}/{filename}1.cnf.simplog'
    filename_2 = f'{folder_name}/{filename}2.cnf.simplog'
    file1 = False
    file2 = False
    with open(filename_1, 'r') as file:
        content = file.read()
        if "exit 20" in content:
            print(f"'exit 20' found in {filename_1}")
            file1 = True
        else:
            if enumerate_files(folder_name, f'{filename}1'):
                print (f'{folder_name}/{filename}1.cnf.simp.log needs to be UNSAT')
    with open(filename_2, 'r') as file:
        content = file.read()
        if "exit 20" in content:
            print(f"'exit 20' found in {filename_1}")
            file2 = True
        else:
            if enumerate_files(folder_name, f'{filename}2'):
                print (f'{folder_name}/{filename}2.cnf.simp.log needs to be UNSAT')
    return file1 and file2

def generate_strings(n):
    if n == 0:
        return []
    if n == 1:
        return ["1", "2"]
    
    # Generate strings of length n-1 recursively
    prev_strings = generate_strings(n-1)
    # Extend each string with either "1" or "2"
    new_strings = [s + "1" for s in prev_strings] + [s + "2" for s in prev_strings]
    
    return new_strings

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python verify.py folder_name filename")
        sys.exit(1)
    
    folder_name = sys.argv[1]
    filename = sys.argv[2]
    files = enumerate_files(folder_name, filename)
    print(files)
