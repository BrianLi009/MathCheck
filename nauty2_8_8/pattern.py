import subprocess
import itertools
import sys

def generate_strings(pattern):
    # Count the number of 'x' in the pattern
    x_count = pattern.count('x')
    
    # Generate all possible combinations for the x positions
    for combo in itertools.product('01', repeat=x_count):
        # Create a list from the pattern
        s = list(pattern)
        # Replace 'x' with values from the combo
        x_index = 0
        for i in range(len(s)):
            if s[i] == 'x':
                s[i] = combo[x_index]
                x_index += 1
        # Join the list back into a string
        yield ''.join(s)

def run_rcl(input_string):
    result = subprocess.run(['./RCL-binary', input_string], capture_output=True, text=True)
    return result.stdout

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 pattern.py <pattern>")
        print("Example: python3 pattern.py x1xx0x")
        sys.exit(1)

    pattern = sys.argv[1]
    for s in generate_strings(pattern):
        output = run_rcl(s).strip()  # Strip whitespace from the output
        if output == "1":
            print(f"Input string: {s}")
            print(output)
            print("-" * 50)

if __name__ == "__main__":
    main()
