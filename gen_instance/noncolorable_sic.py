import itertools
import math

def noncolorable(n, edge_dict, tri_dict, cnf):
    cnf_file = open(cnf, 'a+')
    clause_count = 0
    
    # The two fixed colorings for the first 13 vertices
    fixed_colorings = [
        [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0],
        [0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0]
    ]
    
    # Calculate max allowed vertices with color 1 (less than 50%)
    max_ones = (n // 2) - 1 if n % 2 == 0 else n // 2
    
    # Process each fixed coloring
    for fixed_idx, fixed_coloring in enumerate(fixed_colorings):
        print(f"Processing fixed coloring {fixed_idx+1}: {fixed_coloring}")
        
        # Count ones in fixed coloring
        fixed_ones_count = sum(fixed_coloring)
        
        # Pre-compute fixed vertices with color 1
        fixed_ones = [i+1 for i, color in enumerate(fixed_coloring) if color == 1]
        
        # Calculate max remaining vertices that can have color 1
        max_remaining_ones = max_ones - fixed_ones_count
        
        # Generate all possible colorings for the remaining vertices
        remaining_vertices = list(range(14, n+1))
        remaining_count = len(remaining_vertices)
        
        # Only iterate up to the maximum allowed remaining ones
        for r in range(0, min(max_remaining_ones + 1, remaining_count + 1)):
            print(f"  Considering {r} additional vertices with color 1")
            
            for choice_remaining in itertools.combinations(remaining_vertices, r):
                # Create full coloring representation for printing
                full_coloring = [0] * n
                for i in range(13):
                    full_coloring[i] = fixed_coloring[i]
                for v in choice_remaining:
                    full_coloring[v-1] = 1
                
                print(f"    Coloring: {full_coloring}")
                
                # Combine fixed vertices with color 1 and current choice
                choice = fixed_ones.copy()
                choice.extend(choice_remaining)
                
                # Get vertices with color 0 (more efficient than checking each vertex)
                trig_vertices = [v for v in range(1, n+1) if v not in choice]
                
                # Generate constraints
                constraint_1_lst = []
                
                # Add edge constraints for vertices with color 1
                for e in itertools.combinations(choice, 2):
                    constraint_1_lst.append(str(edge_dict[e]))
                
                # Add triangle constraints for vertices with color 0
                if len(trig_vertices) > 2:
                    for triangle in itertools.combinations(trig_vertices, 3):
                        constraint_1_lst.append(str(tri_dict[triangle]))
                
                # Write constraint to file
                constraint_1 = ' '.join(constraint_1_lst)
                cnf_file.write(constraint_1 + " 0\n")
                clause_count += 1
    
    print(f"Total clauses generated: {clause_count}")
    return clause_count 