import random
import sys
from collections import defaultdict
from pattern_all import generate_patterns_optimized, check_pattern, rcl_cache

def random_binary_string(length):
    # More efficient way to generate random binary strings
    return format(random.getrandbits(length), f'0{length}b')

def analyze_string(input_string):
    # Use the optimized pattern generator
    best_pattern = input_string
    max_x_count = 0
    
    # Use the optimized generator that starts from maximum x's
    for pattern in generate_patterns_optimized(input_string):
        if check_pattern(pattern):
            x_count = pattern.count('x')
            # Since we're going from max to min, we can return immediately
            return pattern, x_count
    
    return best_pattern, max_x_count

def get_string_length(order):
    """Calculate the length of the binary string needed for a graph of given order."""
    if order < 1:
        raise ValueError("Order must be positive")
    if order > 10:  # Practical limit to prevent memory issues
        raise ValueError("Order too large (max 10)")
    return order * (order - 1) // 2

def main():
    try:
        if len(sys.argv) != 2:
            print("Usage: python3 pattern_analysis.py <order>")
            sys.exit(1)
        
        order = int(sys.argv[1])
        length = get_string_length(order)
        
        # Track statistics
        stats = defaultdict(int)
        seen_strings = set()
        total_possible = 2**length
        
        print(f"Analyzing graphs of order {order} (string length: {length})")
        print(f"Total possible strings: {total_possible}")
        
        try:
            while len(seen_strings) < total_possible:
                # Progress indicator
                if len(seen_strings) % 100 == 0:
                    progress = (len(seen_strings) / total_possible) * 100
                    print(f"\rProgress: {progress:.1f}% ({len(seen_strings)}/{total_possible})", 
                          end='', file=sys.stderr)
                
                input_string = random_binary_string(length)
                if input_string in seen_strings:
                    continue
                
                seen_strings.add(input_string)
                
                try:
                    best_pattern, max_x_count = analyze_string(input_string)
                    stats[max_x_count] += 1
                    
                    print(f"\nInput string: {input_string}")
                    print(f"Best pattern: {best_pattern}")
                    print(f"Maximum number of 'x': {max_x_count}")
                except Exception as e:
                    print(f"\nError analyzing string {input_string}: {str(e)}")
                    continue
        
        except KeyboardInterrupt:
            print("\nAnalysis interrupted by user")
        
        finally:
            # Print statistics
            print("\n\nAnalysis Statistics:")
            print("-" * 40)
            for x_count in sorted(stats.keys()):
                count = stats[x_count]
                percentage = (count / len(seen_strings)) * 100
                print(f"Patterns with {x_count} x's: {count} ({percentage:.1f}%)")
            
            # Print cache statistics
            cache_hits = len(rcl_cache)
            print(f"\nCache statistics:")
            print(f"Total cached results: {cache_hits}")
            
    except ValueError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()