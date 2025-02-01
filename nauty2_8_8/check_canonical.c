#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "nauty.h"
#include "nausparse.h"
#include "gtools.h"

// Function to convert a graph to its adjacency matrix string representation
void graph_to_adj_matrix_string(graph *g, int n, char *adj_matrix_str) {
    int i, j;
    char *p = adj_matrix_str;
    for (i = 0; i < n; ++i) {
        for (j = 0; j < n; ++j) {
            *p++ = ISELEMENT(GRAPHROW(g, i, n), j) ? '1' : '0';
        }
    }
    *p = '\0';
}

// Function to check if the input graph is canonical
int is_canonical(graph *g, int m, int n, char *witness) {
    static DEFAULTOPTIONS_GRAPH(options);
    statsblk stats;
    setword workspace[160 * MAXM];
    graph canon_g[MAXN * MAXM];
    int lab[MAXN], ptn[MAXN], orbits[MAXN];
    char adj_matrix_str[MAXN * MAXN + 1];
    char min_adj_matrix_str[MAXN * MAXN + 1];

    // Get the adjacency matrix string of the input graph
    graph_to_adj_matrix_string(g, n, adj_matrix_str);

    // Initialize the minimum adjacency matrix string with the input graph's string
    strcpy(min_adj_matrix_str, adj_matrix_str);

    // Generate the canonical form of the graph
    options.getcanon = TRUE;
    nauty(g, lab, ptn, NULL, orbits, &options, &stats, workspace, 160 * MAXM, m, n, canon_g);

    // Get the adjacency matrix string of the canonical form
    graph_to_adj_matrix_string(canon_g, n, adj_matrix_str);

    // Compare the input graph's adjacency matrix string with the canonical form
    if (strcmp(adj_matrix_str, min_adj_matrix_str) == 0) {
        return 1; // The input graph is canonical
    } else {
        strcpy(witness, adj_matrix_str);
        return 0; // The input graph is not canonical
    }
}

int main() {
    graph g[MAXN * MAXM];
    int m, n;
    char witness[MAXN * MAXN + 1];

    // Read the input graph in graph6 format
    if (readg(stdin, g, 0, &m, &n) == NULL) {
        fprintf(stderr, "Error reading input graph\n");
        return EXIT_FAILURE;
    }

    // Check if the graph is canonical
    if (is_canonical(g, m, n, witness)) {
        printf("true\n");
    } else {
        printf("false\n");
        printf("Witness: %s\n", witness);
    }

    return EXIT_SUCCESS;
}