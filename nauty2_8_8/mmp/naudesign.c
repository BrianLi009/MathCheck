/*****************************************************************************
*                                                                            *
*  Design-specific source file for version 2.5 of nauty.                     *
*                                                                            *
*   Copyright (1984-2010) Brendan McKay.  All rights reserved.               *
*   Subject to waivers and disclaimers in nauty.h.                           *
*                                                                            *
*   CHANGE HISTORY                                                           *
*       26-May-93 : - original changes to standard version 1.7 file          *
*        4-Sep-93 : - changed refine1 incompatibly with earlier version      *
*       16-Nov-00 : - use dispatch vectors and update for version 2.0.       *
*        1-Aug-01 : - code for arbitrary m.  shell_des got extra arg         *
*       17-Nov-03 : changed INFINITY to NAUTY_INFINITY                       *
*       25-Apr-05 : added bestcell_des                                       *
*       10-Sep-08 : added targetcell_des, made bestcell_des local            *
*       10-Nov-09 : removed type permutation                                 *
*        5-May-10 : completed removal of m limits                            *
*                                                                            *
*****************************************************************************/

#define ONE_WORD_SETS
#include "nauty.h"
#include "naudesign.h"

    /* macros for hash-codes: */
#define MASH(l,i) ((((l) ^ 065435) + (i)) & 077777)
    /* : expression whose long value depends only on long l and int/long i.
         Anything goes, preferably non-commutative. */

#define CLEANUP(l) ((int)((l) % NAUTY_INFINITY))
    /* : expression whose value depends on long l and is less than
         NAUTY_INFINITY when converted to int then short.  Anything goes. */

#if  MAXM==1
#define M 1
#else
#define M m
#endif

dispatchvec dispatch_design =
  {isautom_des,testcanlab_des,updatecan_des,refine_des,refine1_des,
   cheapautom_des,targetcell_des,naudesign_freedyn,naudesign_check,NULL,NULL};

#if !MAXN
DYNALLSTAT(int,workperm,workperm_sz);
DYNALLSTAT(int,workvec,workvec_sz);
DYNALLSTAT(set,workset,workset_sz);
#else
static int workperm[MAXN];
static int workvec[MAXN];
static set workset[MAXN];
#endif
DYNALLSTAT(design,workdes,workdes_sz);  /* Can't be done statically */

#define ACCUM(x,y)   x = (((x) + (y)) & 077777)

static int fuzz1[] = {037541,061532,005257,026416};
static int fuzz2[] = {006532,070236,035523,062437};

#define FUZZ1(x) ((x) ^ fuzz1[(x)&3])
#define FUZZ2(x) ((x) ^ fuzz2[(x)&3])

/*****************************************************************************
*                                                                            *
*  shell_des(x,m,b) sorts the k-block design x[0..b-1] using shellsort       *
*                                                                            *
*****************************************************************************/

void
shell_des(design *x, int m, int b)
{
    int i,j,k,h;
    design iw1,*xjh,*xj;

    j = b / 3;
    h = 1;
    do
        h = 3 * h + 1;
    while (h < j);

#if MAXM==1
    do
    {
        for (i = h; i < b; ++i)
        {
            iw1 = x[i];
            for (j = i; x[j-h] > iw1; )
            {
                x[j] = x[j-h];
                if ((j -= h) < h) break;
            }
            x[j] = iw1;
        }
        h /= 3;
    }
    while (h > 0);
#else
#if !MAXN
    DYNALLOC1(set,workset,workset_sz,M,"shell_des");
#endif

    do
    {
        for (i = h; i < b; ++i)
        {
            xj = x + m*i;
            for (k = 0; k < m; ++k) workset[k] = xj[k];
            for (j = i; ; )
            {
                xjh = xj - m*h;
                for (k = 0; k < m; ++k)
                if (xjh[k] != workset[k]) break;
                if (k == m || xjh[k] < workset[k]) break;
                for (k = 0; k < m; ++k) xj[k] = xjh[k];
                xj = xjh;
                if ((j -= h) < h) break;
            }
            if (j != i)
                for (k = 0; k < m; ++k) xj[k] = workset[k];
        }
        h /= 3;
    }
    while (h > 0);
#endif
}

/*****************************************************************************
*                                                                            *
*  sortindirect(x,n,z) - sort x[0..n-1] according to z[x[i]] values          *
*                                                                            *
*****************************************************************************/

static void
sortindirect(int *x, int n, int *z)
{
    int i,j,h,xi;
    int iw;

    j = n / 3;
    h = 1;
    do
        h = 3 * h + 1;
    while (h < j);

    do
    {
        for (i = h; i < n; ++i)
        {
            xi = x[i];
            iw = z[xi];
            for (j = i; z[x[j-h]] > iw; )
            {
                x[j] = x[j-h];
                if ((j -= h) < h) break;
            }
            x[j] = xi;
        }
        h /= 3;
    }
    while (h > 0);
}

/*****************************************************************************
*                                                                            *
*  isautom_des(g,perm,digraph,m,n) = TRUE iff perm is an automorphism of g   *
*  (i.e., g^perm = g).  digraph is ignored.                                  *
*                                                                            *
*  GLOBALS ACCESSED: bit<r>,nextelement()                                    *
*                                                                            *
*****************************************************************************/

boolean
isautom_des(graph *g, int *perm, boolean digraph, int m, int n)
{
    int i,b;
    design *des,*des0,*des1,*dmid,*db;
    int i0,i1,imid,mult,pmult;

    des = (design*)g;
    b = des[0];
    des0 = des + 1;
    des1 = des0 + M*b;

    if (b == 0) return TRUE;

#if !MAXN
    DYNALLOC1(set,workset,workset_sz,M,"isautom_des");
#endif
    
    for (des = des0; des < des1; )
    {
        permset(des,workset,M,perm);

        i0 = 0;
        i1 = b-1;
        while (i0 <= i1)
        {
            imid = (i0 + i1) / 2;
            dmid = des0 + imid*M;
            for (i = 0; i < M; ++i)
                if (workset[i] != dmid[i]) break;
            if (i == M) break;
            if (workset[i] < dmid[i]) i1 = imid - 1;
            else                      i0 = imid + 1;
        }

        if (i0 > i1) return FALSE;

#ifndef SIMPLEDES
        mult = 1;
        for (db = des+M; db < des1; db += M)
        {
            for (i = 0; i < M; ++i)
                if (db[i] != des[i]) break;
            if (i < M) break;
            ++mult;
        }
        des = db;

        pmult = 1;
        for (db = dmid+M; db < des1; db += M)
        {
            for (i = 0; i < M; ++i)
                if (db[i] != dmid[i]) break;
            if (i < M) break;
            ++pmult;
        }
        for (db = dmid-M; db >= des0; db -= M)
        {
            for (i = 0; i < M; ++i)
                if (db[i] != dmid[i]) break;
            if (i < M) break;
            ++pmult;
        }
 
        if (mult != pmult) return FALSE;
#else
        des += M;
#endif
    }

    return TRUE;
}

/*****************************************************************************
*                                                                            *
*  testcanlab_des(g,canong,lab,samerows,m,n) compares g^lab to canong,       *
*  using an ordering which is immaterial since it's only used here.  The     *
*  value returned is -1,0,1 if g^lab <,=,> canong.  *samerows is set to      *
*  the number of rows (0..n) of canong which are the same as those of g^lab. *
*                                                                            *
*  GLOBALS ACCESSED: permset(),workperm<rw>,workdes<rw>                      *
*                                                                            *
*****************************************************************************/

int
testcanlab_des(graph *g, graph *canong, int *lab, int *samerows, int m, int n)
{
    int i,j;
    design *des,*cdes,*d1,*d2;
    int b;

    des = (design*)g;
    cdes = (design*)canong;
    b = des[0];

    DYNALLOC1(design,workdes,workdes_sz,1+b*(size_t)M,"testcanlab_des");
#if !MAXN
    DYNALLOC1(int,workperm,workperm_sz,n,"testcanlab_des");
#endif

    *samerows = 0;

    for (i = 0; i < n; ++i) workperm[lab[i]] = i;
    for (i = 0; i < b; ++i) permset(&des[1+i*M],&workdes[1+i*M],M,workperm);

    shell_des(workdes+1,M,b);

    for (i = 0; i < b; ++i)
    {
        d1 = &workdes[1+i*(size_t)M];
        d2 = &cdes[1+i*(size_t)M];
        for (j = 0; j < M; ++j)
            if      (d1[j] > d2[j]) return 1;
            else if (d1[j] < d2[j]) return -1;
    }

    *samerows = n;
    return 0;
}

/*****************************************************************************
*                                                                            *
*  updatecan_des(g,canong,lab,samerows,m,n) sets canong = g^lab,             *
*  ignoring the value of samerows.                                           *
*                                                                            *
*  GLOBALS ACCESSED: permset(),workperm<rw>                                  *
*                                                                            *
*****************************************************************************/

void
updatecan_des(graph *g, graph *canong, int *lab, int samerows, int m, int n)
{
    int i,b;
    design *des,*cdes;

    des = (design*)g;
    cdes = (design*)canong;
    b = des[0];
    cdes[0] = b;

#if !MAXN
    DYNALLOC1(int,workperm,workperm_sz,n,"testcanlab_des");
#endif  

    for (i = 0; i < n; ++i) workperm[lab[i]] = i;
    for (i = 0; i < b; ++i)
        permset(&des[1+i*(size_t)M],&cdes[1+i*(size_t)M],M,workperm);

    shell_des(cdes+1,M,b);
}

/*****************************************************************************
*                                                                            *
*  refine_des(g,lab,ptn,level,numcells,count,active,code,m,n) performs a     *
*  refinement operation on the partition at the specified level of the       *
*  partition nest (lab,ptn).  *numcells is assumed to contain the number of  *
*  cells on input, and is updated.  The initial set of active cells (alpha   *
*  in the paper) is specified in the set active.  Precisely, x is in active  *
*  iff the cell starting at index x in lab is active.                        *
*  The resulting partition is equitable if active is correct (see the paper  *
*  and the Guide).                                                           *
*  *code is set to a value which depends on the fine detail of the           *
*  algorithm, but which is independent of the labelling of the design.       *
*  count is used for work space.                                             *
*                                                                            *
*****************************************************************************/

void
refine_des(graph *g, int *lab, int *ptn, int level, int *numcells,
           int *count, set *active, int *code, int m, int n)
{
    int cell1,cell2,iw,pw;
    boolean same;
    long longcode;
    int b,k,iact;
    int i,j,bcode;
    design *des,*d;

#if !MAXN
    DYNALLOC1(int,workperm,workperm_sz,n,"refine_des");
    DYNALLOC1(int,workvec,workvec_sz,n,"refine_des");
    DYNALLOC1(set,workset,workset_sz,m,"refine_des");
#endif

// printf("level=%2d: ",level);
// for (i=0;i<n;++i) {printf("%2d",lab[i]); if (ptn[i]<=level) printf("|"); else printf(" ");}
// printf("\n");

    longcode = *numcells;
    des = (design*)g;
    b = des[0];
    ++des;

    j = FUZZ1(0);
    for (i = 0; i < n; ++i)
    {
        count[i] = 0;
        workvec[lab[i]] = j;
        if (ptn[i] <= level) j = FUZZ1(i+1);
    }

    iact = -1;
    while (*numcells < n && ((iact = nextelement(active,m,iact)) >= 0
                         || (iact = nextelement(active,m,-1)) >= 0))
    {
        DELELEMENT(active,iact);
        longcode = MASH(longcode,iact);

        EMPTYSET(workset,m);
        i = iact;
        do
        {
            ADDELEMENT(workset,lab[i]);
            ++i;
        } while (ptn[i-1] > level);

        for (d = des+b*m; (d -= m) >= des;)
        {
            for (i = 0; i < m; ++i)
                if ((d[i] & workset[i]) != 0) break;
            if (i == m) continue;

            k = 0;
            bcode = 0;
            for (i = -1; (i = nextelement(d,m,i)) >= 0; )
            {
                bcode = ACCUM(bcode,workvec[i]);
                workperm[k++] = i;
            }
            bcode = FUZZ2(bcode) ^ k;
            for (i = 0; i < k; ++i)
                count[workperm[i]] = ACCUM(count[workperm[i]],bcode);
        }

        for (cell1 = 0; cell1 < n; cell1 = cell2 + 1)
        {
            pw = count[lab[cell1]];
            same = TRUE;
            for (cell2 = cell1; ptn[cell2] > level; ++cell2)
                if (count[lab[cell2+1]] != pw) same = FALSE;
            if (same) continue;

            if (cell2 <= cell1 + 10)
                for (i = cell1 + 1; i <= cell2; ++i)
                {
                    iw = lab[i];
                    pw = count[iw];
                    for (j = i; count[lab[j-1]] > pw; )
                    {
                        lab[j] = lab[j-1];
                        if (--j <= cell1) break;
                    }
                    lab[j] = iw;
                }
            else
                sortindirect(lab+cell1,cell2-cell1+1,count);

            j = FUZZ1(cell1);
            for (i = cell1 + 1; i <= cell2; ++i)
            {
                if (count[lab[i]] != count[lab[i-1]])
                {
                    ptn[i-1] = level;
                    ++*numcells;
                    ADDELEMENT(active,i);
                    longcode = MASH(longcode,i+count[lab[i]]);
                    j = FUZZ1(i);
                }
                workvec[lab[i]] = j;
            }
        }
    }

    longcode = MASH(longcode,*numcells);
    *code = CLEANUP(longcode);

// printf("          ");
// for (i=0;i<n;++i) {printf("%2d",lab[i]); if (ptn[i]<=level) printf("|"); else printf(" ");}
// printf("\n");
}

/*****************************************************************************
*                                                                            *
*  refine1_des(g,lab,ptn,level,numcells,count,active,code,m,n) is a version  *
*  of refine_des that works only for m=1.  It gives the same results but     *
*  is hopefully faster.                                                      *
*                                                                            *
*****************************************************************************/

void
refine1_des(graph *g, int *lab, int *ptn, int level, int *numcells,
           int *count, set *active, int *code, int m, int n)
{
    int cell1,cell2,iw,pw;
    boolean same;
    long longcode;
    int b,k;
    setword act,acell;
    setword block;
    int i,j,iact,bcode;
    design *des,*d;

#if !MAXN
    DYNALLOC1(int,workperm,workperm_sz,n,"refine_des");
    DYNALLOC1(int,workvec,workvec_sz,n,"refine_des");
#endif

    longcode = *numcells;
    des = (design*)g;
    b = des[0];
    ++des;
    act = *active;


    j = FUZZ1(0);
    for (i = 0; i < n; ++i)
    {
        count[i] = 0;
        workvec[lab[i]] = j;
        if (ptn[i] <= level) j = FUZZ1(i+1);
    }

    iact = -1;
    while (*numcells < n && ((iact = nextelement(&act,1,iact)) >= 0
                         || (iact = nextelement(&act,1,-1)) >= 0))
    {
        DELELEMENT(&act,iact);
        longcode = MASH(longcode,iact);

        i = iact;

//    while (act != 0 && *numcells < n)
//    {
//        i = FIRSTBIT(act);
//        act &= ~BITT[i];
//        longcode = MASH(longcode,i);

        acell = BITT[lab[i]];
        while (ptn[i] > level) acell |= BITT[lab[++i]];

        for (d = des+b; --d >= des;)
        {
            block = *d;
            if ((block & acell) == 0) continue;
            k = 0;
            bcode = 0;
            while (block)
            {
                i = FIRSTBIT(block);
                block ^= BITT[i];
                bcode = ACCUM(bcode,workvec[i]);
                workperm[k++] = i;
            }
            bcode = FUZZ2(bcode) ^ k;
            for (i = 0; i < k; ++i)
                count[workperm[i]] = ACCUM(count[workperm[i]],bcode);
        }

        for (cell1 = 0; cell1 < n; cell1 = cell2 + 1)
        {
            pw = count[lab[cell1]];
            same = TRUE;
            for (cell2 = cell1; ptn[cell2] > level; ++cell2)
                if (count[lab[cell2+1]] != pw) same = FALSE;
            if (same) continue;

            if (cell2 <= cell1 + 10)
                for (i = cell1 + 1; i <= cell2; ++i)
                {
                    iw = lab[i];
                    pw = count[iw];
                    for (j = i; count[lab[j-1]] > pw; )
                    {
                        lab[j] = lab[j-1];
                        if (--j <= cell1) break;
                    }
                    lab[j] = iw;
                }
            else
                sortindirect(lab+cell1,cell2-cell1+1,count);

            j = FUZZ1(cell1);
            for (i = cell1 + 1; i <= cell2; ++i)
            {
                if (count[lab[i]] != count[lab[i-1]])
                {
                    ptn[i-1] = level;
                    ++*numcells;
                    act |= BITT[i];
                    longcode = MASH(longcode,i+count[lab[i]]);
                    j = FUZZ1(i);
                }
                workvec[lab[i]] = j;
            }
        }
    }

    longcode = MASH(longcode,*numcells);
    *code = CLEANUP(longcode);
}

/*****************************************************************************
*                                                                            *
*  cheapautom_des(ptn,level,digraph,n) returns TRUE if the partition at the  *
*  specified level in the partition nest (lab,ptn) {lab is not needed here}  *
*  satisfies a simple sufficient condition for its cells to be the orbits of *
*  some subgroup of the automorphism group.  Otherwise it returns FALSE.     *
*  It always returns FALSE if digraph!=FALSE.                                *
*                                                                            *
*  nauty assumes that this function will always return TRUE for any          *
*  partition finer than one for which it returns TRUE.                       *
*                                                                            *
*****************************************************************************/

boolean
cheapautom_des(int *ptn, int level, boolean digraph, int n)
{
    return FALSE;
}

/*****************************************************************************
*                                                                            *
*  naudesign_check() checks that this file is compiled compatibly with the   *
*  given parameters.   If not, call exit(1).                                 *
*                                                                            *
*****************************************************************************/

void
naudesign_check(int wordsize, int m, int n, int version)
{
    if (wordsize != WORDSIZE)
    {
        fprintf(ERRFILE,"Error: WORDSIZE mismatch in naudesign.c\n");
        exit(1);
    }

#if MAXN
    if (m > MAXM)
    {
        fprintf(ERRFILE,"Error: MAXM inadequate in naudesign.c\n");
        exit(1);
    }

    if (n > MAXN)
    {
        fprintf(ERRFILE,"Error: MAXN inadequate in naudesign.c\n");
        exit(1);
    }
#endif

    if (version < NAUTYREQUIRED)
    {
        fprintf(ERRFILE,"Error: nautdesign.c version mismatch\n");
        exit(1);
    }
}

/*****************************************************************************
*                                                                            *
*  naudesign_freedyn() - free the dynamic memory in this module              *
*                                                                            *
*****************************************************************************/

void
naudesign_freedyn(void)
{
#if !MAXN
    DYNFREE(workperm,workperm_sz);
    DYNFREE(workvec,workvec_sz);
    DYNFREE(workset,workset_sz);
#endif
    DYNFREE(workdes,workdes_sz);
}

/*****************************************************************************
*                                                                            *
*  bestcell_des(g,lab,ptn,level,tc_level,m,n) returns the index in           *
*  lab of the start of the "best non-singleton cell" for fixing.             *
*  If there is no non-singleton cell it returns n.                           *
*  This implementation finds the first smallest nontrivial cell,             *
*  which is not really good but something to work with.                      *
*                                                                            *
******************************************************************************/

static int
bestcell_des(graph *g, int *lab, int *ptn, int level, int tc_level,
         int m, int n)
{
    int i,j,k;
    int smallsize,size;

    smallsize = n+1;
    i = 0;
    while (i < n)
    {
        if (ptn[i] > level)
        {
            j = i;
            while (ptn[i] > level) ++i;
            size = i-j+1;
            if (size < smallsize)
            {
                smallsize = size;
                k = j;
            }
        }
        ++i;
    }

    if (smallsize <= n) return k;
    else                return n;
}

/*****************************************************************************
*                                                                            *
*  targetcell(g,lab,ptn,level,tc_level,digraph,hint,m,n) returns the index   *
*  in lab of the next cell to split.                                         *
*  hint is a suggestion for the answer, which is obeyed if it is valid.      *
*  Otherwise we use bestcell() up to tc_level and the first non-trivial      *
*  cell after that.                                                          *
*                                                                            *
*****************************************************************************/

int
targetcell_des(graph *g, int *lab, int *ptn, int level, int tc_level,
           boolean digraph, int hint, int m, int n)
{
    int i;

    if (hint >= 0 && ptn[hint] > level &&
                         (hint == 0 || ptn[hint-1] <= level))
        return hint;
    else if (level <= tc_level)
        return bestcell_des(g,lab,ptn,level,tc_level,m,n);
    else
    {
        for (i = 0; i < n && ptn[i] <= level; ++i) {}
        return (i == n ? 0 : i);
    }
}
