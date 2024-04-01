import os
import sys
def enumerate_files(folder_name, filename, depth=1):
    base_name = f'{folder_name}/{filename}0'
    for subfix in generate_strings(depth):
        new_file_name = f'{base_name}{subfix}.cnf.simplog'
        with open(new_file_name, 'r') as file:
            content = file.read()
            if "exit 20" in content:
                print(f"'exit 20' found in {new_file_name}")
            else:
                if depth > 1:
                    for i in range(1, depth+1):
                        new_file_name = f'{base_name}{subfix}{i}.cnf.simplog'
                        with open(new_file_name, 'r') as file:
                            content = file.read()
                            if "exit 20" in content:
                                print(f"'exit 20' found in {new_file_name}")
                            else:
                                enumerate_files(folder_name, filename, depth+1)

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
