import subprocess
import itertools
import sys
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

# Cache for RCL results to avoid repeated subprocess calls
rcl_cache = {}

def run_rcl(input_string):
    if input_string in rcl_cache:
        return rcl_cache[input_string]
    result = subprocess.run(['./RCL-binary', input_string], capture_output=True, text=True)
    rcl_cache[input_string] = result.stdout.strip()
    return rcl_cache[input_string]

def check_pattern_chunk(args):
    pattern, start, end = args
    x_positions = [i for i, char in enumerate(pattern) if char == 'x']
    x_count = len(x_positions)
    
    # Generate combinations more efficiently using binary counting
    for i in range(start, min(end, 2**x_count)):
        test_string = list(pattern)
        for j in range(x_count):
            test_string[x_positions[j]] = '1' if (i & (1 << j)) else '0'
        if run_rcl(''.join(test_string)) != "0":
            return False
    return True

def check_pattern(pattern):
    x_count = pattern.count('x')
    if x_count > 20:  # Skip patterns with too many x's (would take too long)
        return False
    
    if x_count == 0:
        return run_rcl(pattern) == "0"

    # Calculate total combinations
    total_combinations = 2**x_count
    
    # Use multiprocessing for patterns with many combinations
    if total_combinations > 1024:
        num_processes = multiprocessing.cpu_count()
        chunk_size = (total_combinations + num_processes - 1) // num_processes
        chunks = [(pattern, i, min(i + chunk_size, total_combinations)) 
                 for i in range(0, total_combinations, chunk_size)]
        
        with ProcessPoolExecutor(max_workers=num_processes) as executor:
            results = executor.map(check_pattern_chunk, chunks)
            return all(results)
    
    return check_pattern_chunk((pattern, 0, total_combinations))

def generate_patterns_optimized(input_string):
    n = len(input_string)
    # Start from larger numbers of x's first (more likely to find solution)
    for num_x in range(n, -1, -1):
        for positions in itertools.combinations(range(n), num_x):
            pattern = list(input_string)
            for pos in positions:
                pattern[pos] = 'x'
            yield ''.join(pattern)

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 pattern_all.py <input_string>")
        print("Example: python3 pattern_all.py 110010")
        sys.exit(1)

    input_string = sys.argv[1]
    
    # Early validation
    if not all(c in '01' for c in input_string):
        print("Error: Input string must contain only 0's and 1's")
        sys.exit(1)

    # Track all patterns with maximum x's
    max_x_count = 0
    best_patterns = []

    for pattern in generate_patterns_optimized(input_string):
        if check_pattern(pattern):
            x_count = pattern.count('x')
            if x_count > max_x_count:
                max_x_count = x_count
                best_patterns = [pattern]
            elif x_count == max_x_count:
                best_patterns.append(pattern)

    # Print all found patterns
    for pattern in best_patterns:
        print(f"Input string: {input_string}")
        print(f"Pattern: {pattern}")
        print(f"Number of x's: {pattern.count('x')}")

if __name__ == "__main__":
    main()
