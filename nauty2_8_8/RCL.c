#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "nauty.h"

#define WORDSIZE 64
#define MAXNV 64

static DEFAULTOPTIONS_GRAPH(options);
static statsblk stats;
static setword workspace[50];

void stringToGraph(const char* input, graph* g, int n, int m) {
    int index = 0;
    for (int j = 1; j < n; j++) {
        for (int i = 0; i < j; i++) {
            if (input[index++] == '1') {
                ADDONEEDGE(g, i, j, m);
                ADDONEEDGE(g, j, i, m);  // Ensure symmetry
            }
        }
    }
}

void graphToString(graph* g, int n, int m, char* output) {
    int index = 0;
    for (int j = 1; j < n; j++) {
        for (int i = 0; i < j; i++) {
            output[index++] = ISELEMENT(GRAPHROW(g,i,m), j) ? '1' : '0';
        }
    }
    output[index] = '\0';
}

void Getcan_Rec(graph g[MAXNV], int n, int can[])
{
    int lab1[MAXNV], lab2[MAXNV], inv_lab1[MAXNV], ptn[MAXNV], orbits[MAXNV];
    int i, j, k;
    setword st;
    graph g2[MAXNV];
    int m = 1;

    if (n == 1) {
        can[n-1] = n-1;
    } else {
        options.writeautoms = FALSE;
        options.writemarkers = FALSE;
        options.getcanon = TRUE;
        options.defaultptn = TRUE;

        nauty(g, lab1, ptn, NULL, orbits, &options, &stats, workspace, 50, m, n, g2);

        for (i = 0; i < n; i++)
            inv_lab1[lab1[i]] = i;
        for (i = 0; i <= n-2; i++) {
            j = lab1[i];
            st = g[j];
            g2[i] = 0;
            while (st) {
                k = FIRSTBIT(st);
                st ^= bit[k];
                k = inv_lab1[k];
                if (k != n-1)
                    g2[i] |= bit[k];
            }
        }
        Getcan_Rec(g2, n-1, lab2);
        for (i = 0; i <= n-2; i++)
            can[i] = lab1[lab2[i]];
        can[n-1] = lab1[n-1];
    }
}

void printAdjacencyMatrix(graph* g, int n, int m) {
    printf("Adjacency Matrix:\n");
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            if (i == j) {
                printf("0 ");
            } else {
                printf("%d ", ISELEMENT(GRAPHROW(g,i,m), j) ? 1 : 0);
            }
        }
        printf("\n");
    }
    printf("\n");
}

void computeAndPrintOrbits(graph* g, int n, int m) {
    int lab[MAXNV], ptn[MAXNV], orbits[MAXNV];
    DEFAULTOPTIONS_GRAPH(orbit_options);
    statsblk orbit_stats;
    setword orbit_workspace[50];

    orbit_options.getcanon = FALSE;
    orbit_options.defaultptn = TRUE;

    nauty(g, lab, ptn, NULL, orbits, &orbit_options, &orbit_stats, orbit_workspace, 50, m, n, NULL);

    printf("Orbits:\n");
    for (int i = 0; i < n; i++) {
        printf("%d: %d\n", i, orbits[i]);
    }
    printf("\n");
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <input_string>\n", argv[0]);
        return 1;
    }

    const char* input = argv[1];
    int n = (int)(sqrt(2 * strlen(input) + 0.25) + 0.5);
    int m = SETWORDSNEEDED(n);
    
    graph g[MAXNV];
    for (int i = 0; i < n; i++) {
        EMPTYSET(GRAPHROW(g, i, m), m);
    }
    stringToGraph(input, g, n, m);

    printf("Input Graph:\n");
    printAdjacencyMatrix(g, n, m);

    // Compute and print orbits
    computeAndPrintOrbits(g, n, m);

    int can[MAXNV];
    graph cang[MAXNV];
    
    Getcan_Rec(g, n, can);

    // Print the permutation
    printf("Permutation (input -> canonical):\n");
    for (int i = 0; i < n; i++) {
        printf("%d -> %d\n", can[i], i);
    }
    printf("\n");

    // Correctly construct the canonical graph
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < m; j++) {
            cang[i*m + j] = 0;
        }
        for (int j = 0; j < n; j++) {
            if (ISELEMENT(GRAPHROW(g, can[i], m), can[j])) {
                ADDONEEDGE(cang, i, j, m);
            }
        }
    }

    printf("Canonical Graph:\n");
    printAdjacencyMatrix(cang, n, m);

    char* output = (char*)malloc((n*(n-1)/2 + 1) * sizeof(char));
    graphToString(cang, n, m, output);
    printf("Output string: %s\n", output);

    free(output);

    return 0;
}