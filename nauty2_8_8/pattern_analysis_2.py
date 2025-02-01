import random
import sys
import subprocess
from pattern_all import generate_patterns, check_pattern

def random_binary_string(length):
    return ''.join(random.choice('01') for _ in range(length))

def analyze_string(input_string):
    max_x_count = 0
    best_pattern = input_string

    for pattern in generate_patterns(input_string):
        if check_pattern(pattern):
            x_count = pattern.count('x')
            if x_count > max_x_count:
                max_x_count = x_count
                best_pattern = pattern
    
    return best_pattern, max_x_count

def get_string_length(order):
    """Calculate the length of the binary string needed for a graph of given order."""
    return order * (order - 1) // 2

def run_rcl(binary_string):
    """Run RCL binary and return the orbit information, canonical string, and if it's canonical."""
    try:
        # Run RCL-binary first to check if canonical
        result = subprocess.run(['./RCL-binary', binary_string], 
                              capture_output=True, text=True)
        # RCL-binary outputs 1 for canonical graphs, so stdout will be "1\n"
        is_canonical = result.stdout.strip() == "1"

        if not is_canonical:
            return None, None, False

        # If canonical, run RCL to get orbit information
        result = subprocess.run(['./RCL', binary_string], 
                              capture_output=True, text=True)
        
        # Parse orbit information and canonical string from output
        orbits = []
        canonical_string = None
        for line in result.stdout.split('\n'):
            if line.startswith('Orbits:'):
                continue
            if ':' in line and line[0].isdigit():
                vertex, orbit = line.split(':')
                orbits.append(int(orbit))
            if line.startswith('Output string:'):
                canonical_string = line.split()[-1]
            if line.startswith('Permutation'):
                break
                
        return orbits, canonical_string, True
    except subprocess.CalledProcessError as e:
        print(f"Error running RCL: {e}")
        return None, None, False

def check_orbit_ordering(orbits):
    """Check if orbits are in non-decreasing order."""
    return all(orbits[i] <= orbits[i+1] for i in range(len(orbits)-1))

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 pattern_analysis.py <order>")
        sys.exit(1)
    
    order = int(sys.argv[1])
    length = get_string_length(order)
    seen_strings = set()
    total_canonical = 0
    total_violations = 0
    
    print(f"\nAnalyzing graphs of order {order} (string length: {length})")
    print("=" * 50)
    
    while True:
        input_string = random_binary_string(length)
        if input_string in seen_strings:
            continue
            
        seen_strings.add(input_string)
        
        # Run RCL and check orbit ordering
        orbits, canonical_string, is_canonical = run_rcl(input_string)
        
        if is_canonical:
            total_canonical += 1
            orbit_str = ''.join(str(x) for x in orbits)
            is_ordered = check_orbit_ordering(orbits)
            
            if not is_ordered:
                total_violations += 1
                print(f"\nWARNING: Orbit violation found! (#{total_violations})")
            
            print(f"\nGraph #{len(seen_strings)}:")
            print(f"Input string:      {input_string}")
            print(f"Canonical string:  {canonical_string}")
            print(f"Orbits:           {orbit_str}")
            print(f"Orbit ordered:     {'✓' if is_ordered else '✗'}")
            print("-" * 50)
        
        # Print progress periodically
        if len(seen_strings) % 1000 == 0:
            print(f"\nProgress: {len(seen_strings)}/{2**length} strings checked")
            print(f"Canonical graphs found: {total_canonical}")
            print(f"Orbit violations found: {total_violations}")
            print("-" * 50)
        
        # Stop when we've seen all possible strings
        if len(seen_strings) == 2**length:
            break
    
    # Print final statistics
    print("\nFinal Statistics:")
    print(f"Total strings checked: {len(seen_strings)}")
    print(f"Total canonical graphs: {total_canonical}")
    print(f"Total orbit violations: {total_violations}")
    print("=" * 50)

if __name__ == "__main__":
    main()