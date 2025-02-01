#include "geng_interface.h"
#include "gtools.h"
#include "nauty.h"

// Declare external functions and variables from geng.c
extern void genextend(graph*, int, int*, int, boolean, int, int);
extern void (*outproc)(FILE*, graph*, int);
extern FILE *outfile;
extern int connec;
extern boolean bipartite, trianglefree, squarefree, pentagonfree;
extern boolean k4free, splitgraph, chordal, perfect, clawfree;
extern boolean savemem, canonise;
extern int maxdeg, mindeg, maxn, mine, maxe;
extern nauty_counter ecount[1+MAXN*(MAXN-1)/2];
extern int splitlevel, min_splitlevel;
extern int mod, res;
extern int multiplicity;

void geng_extend(graph *g, int n, int *deg, int ne, boolean rigid, int xlb, int xub)
{
    // Initialize global variables
    connec = 0;
    bipartite = trianglefree = squarefree = pentagonfree = FALSE;
    k4free = splitgraph = chordal = perfect = clawfree = FALSE;
    savemem = canonise = FALSE;
    maxdeg = MAXN - 1;
    mindeg = 0;
    maxn = n + 1;
    mine = ne;
    maxe = (maxn * (maxn - 1)) / 2;
    outproc = NULL;
    outfile = stdout;
    splitlevel = -1;
    min_splitlevel = 6;
    mod = 1;
    res = 0;
    multiplicity = 1;

    // Initialize ecount
    for (int i = 0; i <= maxe; i++) ecount[i] = 0;

    // Call genextend
    genextend(g, n, deg, ne, rigid, xlb, xub);
}