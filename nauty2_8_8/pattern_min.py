import subprocess
import itertools
import sys

def run_rcl(input_string):
    result = subprocess.run(['./RCL-binary', input_string], capture_output=True, text=True)
    return result.stdout.strip()

def generate_patterns(input_string):
    n = len(input_string)
    for num_x in range(n + 1):
        for positions in itertools.combinations(range(n), num_x):
            pattern = list(input_string)
            for pos in positions:
                pattern[pos] = 'x'
            yield ''.join(pattern)

def check_pattern(pattern):
    for combo in itertools.product('01', repeat=pattern.count('x')):
        test_string = pattern
        for bit in combo:
            test_string = test_string.replace('x', bit, 1)
        if run_rcl(test_string) != "0":
            return False
    return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 pattern.py <input_string>")
        print("Example: python3 pattern.py 110010")
        sys.exit(1)

    input_string = sys.argv[1]
    maximal_patterns = []

    for pattern in generate_patterns(input_string):
        if check_pattern(pattern):
            # Check if we can add another 'x' anywhere
            is_maximal = True
            for i in range(len(pattern)):
                if pattern[i] in '01':  # Only try positions that aren't already 'x'
                    new_pattern = list(pattern)
                    new_pattern[i] = 'x'
                    new_pattern = ''.join(new_pattern)
                    if check_pattern(new_pattern):
                        is_maximal = False
                        break
            if is_maximal:
                maximal_patterns.append(pattern)

    print(f"Input string: {input_string}")
    print(f"Maximal patterns found:")
    for pattern in maximal_patterns:
        print(f"  {pattern} (number of 'x': {pattern.count('x')})")

if __name__ == "__main__":
    main()
