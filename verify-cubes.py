import sys

def get_substrings(numbers):
    # Generate all possible substrings of the number sequence, including the full sequence
    substrings = [numbers[:i+1] for i in range(len(numbers))]
    return substrings

def find_matching_negations(lines):
    # Process each line to get numbers only (ignore first char and last 0)
    processed_lines = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:  # Skip empty lines
            continue
            
        # Split line and convert to integers, ignoring first char and last 0
        numbers = [int(x) for x in line.split()[1:-1]]  # This now includes all numbers except the final 0
        processed_lines.append((numbers, i + 1))
    
    matches = []
    # Check each line
    for numbers, line_num in processed_lines:
        # Get all substrings for current line
        subs = get_substrings(numbers)
        
        # For each substring
        for sub in subs:
            # Create the target substring by negating the last number
            target = list(sub[:-1]) + [-sub[-1]]
            
            # Look for matching substrings in other lines
            for other_numbers, other_line_num in processed_lines:
                if line_num != other_line_num:  # Don't compare with self
                    other_subs = get_substrings(other_numbers)
                    if target in other_subs:
                        matches.append((
                            ' '.join(map(str, sub)),
                            ' '.join(map(str, target)),
                            line_num,
                            other_line_num,
                            sub[-1]  # Store the last number for verification
                        ))
    
    return matches

# Check if filename is provided
if len(sys.argv) != 2:
    print("Usage: python verify-cubes.py <input_file>")
    sys.exit(1)

# Read the file using command line argument
try:
    with open(sys.argv[1], 'r') as f:
        lines = f.readlines()
except FileNotFoundError:
    print(f"Error: File '{sys.argv[1]}' not found")
    sys.exit(1)

# Find matches
matches = find_matching_negations(lines)

# Print results
for original, negated, line1, line2, last_num in matches:
    print(f"Match found:")
    print(f"  Original ({line1}): {original}")
    print(f"  Negated  ({line2}): {negated}")
    print()

# Check completeness
def check_completeness(matches, lines):
    if not matches:
        return False, "No matching negations found"
    
    # Store all sequences and their substrings
    all_sequences = set()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            numbers = [int(x) for x in line.split()[1:-1]]
            if numbers:
                # Add all substrings of this sequence
                for i in range(len(numbers)):
                    all_sequences.add(tuple(numbers[:i+1]))
        except (ValueError, IndexError):
            continue
    
    # Check if each sequence has a matching negated sequence
    for sequence in all_sequences:
        # Create negated sequence (negate the last number)
        negated = tuple(list(sequence[:-1]) + [-sequence[-1]])
        if negated not in all_sequences:
            return False, f"Sequence ending with {sequence[-1]} has no matching negation"
    
    return True, "All sequences have matching negations"

# Check and print completeness status
is_complete, reason = check_completeness(matches, lines)
print("Completeness check:")
if is_complete:
    print("✓ Cubes are complete -", reason)
else:
    print("✗ Cubes are incomplete -", reason)
