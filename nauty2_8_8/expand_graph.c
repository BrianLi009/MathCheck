// Include the nauty library header
#include "nauty.h"
// Include the gtools library header
#include "gtools.h"
// Include the nautinv library header
#include "nautinv.h"

// Function to read input graph from stdin
void read_input_graph(graph **g, int *m, int *n) {
    // Set input file to stdin
    FILE *infile = stdin;  // Read from standard input
    // Declare a boolean variable to store if the graph is directed
    boolean digraph;
    // Read the graph from input file
    if ((*g = readgg(infile, NULL, 0, m, n, &digraph)) == NULL) {
        // Print error message if reading fails
        fprintf(stderr, "Error reading input graph\n");
        // Exit the program with error code 1
        exit(1);
    }
}

// Function to print graph in graph6 format
void print_graph_g6(FILE *f, graph *g, int m, int n) {
    // Write the graph in graph6 format to the specified file
    writeg6(f, g, m, n);
}

// Main function
int main(int argc, char *argv[])
{
    // Declare dynamic allocation for graph g
    DYNALLSTAT(graph,g,g_sz);
    // Declare dynamic allocation for graph newg
    DYNALLSTAT(graph,newg,newg_sz);
    // Declare variables for graph properties
    int n, m, i, j;
    
    // Set initial word size
    m = WORDSIZE;
    // Dynamically allocate memory for graph g
    DYNALLOC2(graph,g,g_sz,m,1,"malloc");
    // Read input graph
    read_input_graph(&g, &m, &n);
    
    // Calculate number of words needed for n+1 vertices
    m = SETWORDSNEEDED(n+1);
    
    // Check nauty version compatibility
    nauty_check(WORDSIZE,m,n+1,NAUTYVERSIONID);
    
    // Reallocate memory for graph g
    DYNREALLOC(graph,g,g_sz,m*(n+1),"realloc");
    // Allocate memory for new graph newg
    DYNALLOC2(graph,newg,newg_sz,m,n+1,"malloc");
    
    // Initialize counter for number of expansions
    int num_expansions = 0;
    
    // Generate all possible expansions
    for (int edge_mask = 0; edge_mask < (1 << n); edge_mask++) {
        // Initialize newg as an empty graph
        EMPTYGRAPH(newg,m,n+1);
        
        // Copy original graph to newg
        for (j = 0; j < n; j++) {
            memcpy(GRAPHROW(newg,j,m), GRAPHROW(g,j,m), m*sizeof(setword));
        }
        
        // Add new vertex and edges based on the edge_mask
        for (j = 0; j < n; j++) {
            if (edge_mask & (1 << j)) {
                // Add edge between new vertex and vertex j
                ADDONEEDGE(newg,j,n,m);
            }
        }
        
        // Increment expansion counter
        num_expansions++;
        
        // Output the expansion in graph6 format
        print_graph_g6(stdout, newg, m, n+1);
    }
    
    // Free dynamically allocated memory for g
    DYNFREE(g,g_sz);
    // Free dynamically allocated memory for newg
    DYNFREE(newg,newg_sz);
    
    // Return 0 to indicate successful execution
    return 0;
}