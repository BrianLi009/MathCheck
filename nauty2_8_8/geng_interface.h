// geng_interface.h

#ifndef GENG_INTERFACE_H
#define GENG_INTERFACE_H

#include "nauty.h"
#include "gtools.h"

#ifndef MAXN
#define MAXN 64  // Or whatever your maximum number of vertices is
#endif

// Function prototype for the interface
void geng_extend(graph *g, int n, int *deg, int ne, boolean rigid, int xlb, int xub);

#endif // GENG_INTERFACE_H
