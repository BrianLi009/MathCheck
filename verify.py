import os
import sys
def enumerate_files(folder_name, filename):
    file_list = []
    file_name = filename + "1"
    while os.path.exists(os.path.join(folder_name, file_name)):
        file_list.append(file_name)
        file_name = filename + str(int(file_name[len(filename):]) + 1)
    if not file_list:
        print(f"No files found with the name {filename} in the folder {folder_name}.")
    return file_list

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python verify.py folder_name filename")
        sys.exit(1)
    
    folder_name = sys.argv[1]
    filename = sys.argv[2]
    files = enumerate_files(folder_name, filename)
    print(files)
