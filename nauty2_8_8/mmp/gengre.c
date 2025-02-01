/* gengre.c : generate connected Greechie diagrams */

#define USAGE \
 "gengre [-a#-#] [-b#] [-z#-#] [-l#] [-f] [-d|-u] [-q] [-s#/#] [outfile]"

#define HELPTEXT \
"Generate connected Greechie diagrams.\n\
    outfile  is the output file (missing or \'-\' means stdout)\n\
    -f : only output diagrams with no feet (and therefore no legs)\n\
    -a# : specify the number of atoms, or a range -a#-#\n\
    -b# : specify the number of blocks (compulsory)\n\
       Eg: -a-30 -b13  means 13 blocks, up to 30 atoms\n\
    -z#-# : specify the permitted size of blocks.  This can be given as\n\
       a single value like -z4 or a range like -z3-5.  If this\n\
       option is omitted entirely, -z3 is assumed.\n\
    -l# : specify the smallest cycle length permitted (3,4 or 5; default 5)\n\
    -B# : specify the number of big blocks, or a range -B#-#.  Big blocks\n\
       are defined to be blocks larger than the minimum allowed by -z.\n\
    -d : write in \'d\' format\n\
    -u : no output, just count\n\
    -q : suppress detailed counts\n\
    -s#/# : only present a fraction of the output.  The two numbers are\n\
       res/mod where 0 <= res <= mod-1.  The set of all diagrams is\n\
       divided into mod disjoint classes, and only class res is generated.\n"
/*
   Author:  Brendan McKay, Sep 2001.    bdm@cs.anu.edu.au

   Added -l switch : March 1, 2002.
   Fixed a stupid bug : July 5, 2002.
   Fixed another stupid bug: Sep 15, 2003.
   Update to work with nauty 2.6: June 20, 2016.

**************************************************************************/

/* MAXB is the maximum number of blocks.  MAXA is the maximum
   number of atoms.  MAXN is used for nauty-related things.
   It must be that MAXB <= MAXN = WORDSIZE. */

#undef MAXN
#define MAXN (2*WORDSIZE)
#include "gtools.h"
#include "naudesign.h"   /* which includes nauty.h and stdio.h */

#undef MAXN
#undef MAXB
#undef MAXA
#define MAXN WORDSIZE
#define MAXB WORDSIZE
#define MAXA 128

/*====================================================================*/

/* Define the default format (without -d or -u).  */

static char atomname[] = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ\
abcdefghijklmnopqrstuvwxyz!\"#$%&'()*-/:;<=>?@[\\]^_`{|}~";

/*====================================================================*/

#define GETCPUTIME 1          /* Whether to measure the cpu time or not */

#define ARG_OK 0
#define ARG_MISSING 1
#define ARG_TOOBIG 2
#define ARG_ILLEGAL 3
#undef NOLIMIT
#define NOLIMIT (MAXARG+1L)
#undef SWINT
#define SWINT(c,boool,val,id) if (sw==c) \
        {boool=TRUE;arg_int_g(&arg,&val,id);}
#define SWLONG(c,boool,val,id) if (sw==c) \
        {boool=TRUE;arg_long(&arg,&val,id);}
#undef SWRANGE
#define SWRANGE(c,sep,boool,val1,val2,id) if (sw==c) \
        {boool=TRUE;arg_range_g(&arg,sep,&val1,&val2,id);}

static FILE *outfile;
static long nout;

static int *bupper;
static void (*make_close)(design*);

/* bupper#[i] = upper bound on the number of 3-blocks that fit in i atoms
                with switch -l#.  The list is marked by a -1 at the end,
                after which point the program uses a recursion to extend
                the list if necessary. */
static int bupper3[MAXA+38] = {0,0,0,1,1, 2,4,7,8,12, 13,17,20,26,-1};
static int bupper4[MAXA+38] = {0,0,0,1,1, 2,2,3,4,6, 6,7,9,10,12,
                                15,15,17,18,21, 22,-1};
static int bupper5[MAXA+38] = {0,0,0,1,1, 2,2,3,3,4, 5,5,6,7,8,
                               10,10,11,12,13, 14,15,16,17,18,
                               20,20,21,23,24, 26,28,28,30,32, 35,36,36,-1};

static boolean fswitch;
static int mina,maxa,numb;
static int minblocksize,maxblocksize;
static int splitlevel,mod,res;
static int mincycle;
static long splitcases;
static int minbig,maxbig;
static void extend(design*,int,int,int*,int*,int);
static void (*outproc)();
static int isclose[MAXA][MAXA];
static long count[MAXA+1][MAXB+1];

DYNALLSTAT(int,xorbits,xorbits_sz);
DYNALLSTAT(set,xlist,xlist_sz);
static set *xlistp;
static set *xint[MAXB+1];
static size_t xint_sz[MAXB+1];
DYNALLSTAT(int,xperm,xperm_sz);

static int blockgen[MAXB][MAXB];   /* blockgen[0..numgens-1][*] are */
static int numgens;       		  /* generators for the block group */

#define STATS 0
#if STATS
long ncand[MAXB+1],naccept[MAXB+1];
#endif

#undef MAXL
#define MAXL  (7+(MAXB*MAXA + 5)/6)  /* max length of d-format line */

#define IF2BITS(ww) ww &= ww-1; if (ww && !(ww&(ww-1)))
#define IFLE2BITS(ww) ww &= ww-1; if (!(ww&(ww-1)))
#define IF1BITS(ww)  if (ww && !(ww&(ww-1)))
#define IFLE1BITS(ww)  if (!(ww&(ww-1)))

#define TMP

/*************************************************************************/

static void
checkorder(design *g)
{
	int i,alpha;

	alpha = g[0];

	for (i = 2; i <= alpha; ++i)
	    if (g[i] < g[i-1])
	    {
		fprintf(stderr,">E order error\n");
		exit(1);
	    }
}

/*************************************************************************/
static void
make_close3(design *g)
/* Make matrix of atoms at distance <= 1. */
{
	int alpha,i,j,k;
	setword gi;

	alpha = g[0];
	for (i = 0; i < alpha; ++i)
	for (j = 0; j < alpha; ++j)
	    isclose[i][j] = FALSE;

	for (i = 0; i < alpha; ++i)
	{
	    gi = g[i+1];
	    for (j = 0; j <= i; ++j)
		if (g[j+1] & gi) isclose[i][j] = isclose[j][i] = TRUE;
	}
}

/*************************************************************************/
static void
make_close4(design *g)
/* Make matrix of atoms at distance <= 2. */
{
        int alpha,i,j,k;
        int *plim[MAXA],nbhd[MAXA][MAXA];
        int *p,*pj,*pk,*pilim;
        setword gi;

        alpha = g[0];
        for (i = 0; i < alpha; ++i)
        for (j = 0; j < alpha; ++j)
            isclose[i][j] = FALSE;

        for (i = 0; i < alpha; ++i)
        {
            p = nbhd[i];
            gi = g[i+1];
            for (j = 0; j < alpha; ++j)
                if (g[j+1] & gi) *(p++) = j;
            plim[i] = p;
        }

	for (i = 0; i < alpha; ++i)
	{
	    pilim = plim[i];
	    p = nbhd[i];
	    for (pj = p; pj < pilim; ++pj)
	    for (pk = p; pk <= pj; ++pk)
		isclose[*pj][*pk] = isclose[*pk][*pj] = TRUE;
	}
}

/*************************************************************************/

static void
make_close5(design *g)
/* Make matrix of atoms at distance <= 3. */
{
	int alpha,i,j,k;
	int *plim[MAXA],*pjlim,nbhd[MAXA][MAXA];
	int dj,dk,*p,*pj,*pk,*pklim;
	setword gi;

	alpha = g[0];
	for (i = 0; i < alpha; ++i)
	for (j = 0; j < alpha; ++j)
	    isclose[i][j] = FALSE;

	for (i = 0; i < alpha; ++i)
	{
	    p = nbhd[i];
	    gi = g[i+1];
	    for (j = 0; j < alpha; ++j)
		if (g[j+1] & gi) *(p++) = j;
	    plim[i] = p;
	}
	
	for (j = 0; j < alpha; ++j)
	{
	    pjlim = plim[j];
	    for (p = nbhd[j]; ; ++p)
	    {
		k = *p;
		pklim = plim[k];
		for (pj = nbhd[j]; pj < pjlim; ++pj)
		for (pk = nbhd[k]; pk < pklim; ++pk)
		    isclose[*pj][*pk] = isclose[*pk][*pj] = TRUE;
		if (k == j) break;
	    }
	}
}

/************************************************************************/

static void
lsort(long *x, int n)
/* Sort x[0..n-1] */
{
        register int i,j,h;
        register long iw;

        j = n / 3;
        h = 1;
        do
            h = 3 * h + 1;
        while (h < j);

        do
        {
            for (i = h; i < n; ++i)
            {
                iw = x[i];
                for (j = i; x[j-h] > iw; )
                {
                    x[j] = x[j-h];
                    if ((j -= h) < h) break;
                }
                x[j] = iw;
            }
            h /= 3;
        }
        while (h > 0);
}

/*************************************************************************/

static void
sort_sw_p(setword *x, int *p, int n)
/* sort an array of n setwords, and a permutation in parallel.
   This is a stable sort, but not very fast. */
{
        int i,j;
        setword xi;
        int pi;

        for (i = 1; i < n; ++i)
        {
            xi = x[i];
            pi = p[i];
            for (j = i; x[j-1] > xi; )
            {
                x[j] = x[j-1];
                p[j] = p[j-1];
                if (--j <= 0) break;
            }
            x[j] = xi;
            p[j] = pi;
        }
}

/*************************************************************************/

static void
atomperm(design *g, int *bperm, int *aperm)
/* Find a stable atom permutation corresponding to a block permutation,
   or its inverse (it doesn't matter which).  MUST be stable. */
{
	design h[MAXA+1];
	int i,alpha;

	alpha = g[0];
	for (i = 0; i < alpha; ++i)
	{
	    aperm[i] = i;
	    permset(&g[i+1],&h[i],1,bperm);
	}

	sort_sw_p(h,aperm,alpha);    /* sort h, aperm in parallel, stable */
}

/************************************************************************/

static void
nullwrite(FILE *f, design *g, int n)
{
}

/************************************************************************/

void ntod(design *g, int beta, char *dstr)
/* convert dual design to d-string, \n and \0 terminated */
{
#define BIAS ((char)63)
	static char xbit[] = {32,16,8,4,2,1};
        int i,j,k,len;
        int alpha,base;
	setword x;

        alpha = g[0];

        *(dstr++) = alpha + BIAS;
        *(dstr++) = (beta >> 6) + BIAS;
        *(dstr++) = (beta & 077) + BIAS;

        len = (alpha*beta + 5) / 6;

	for (k = 0; k < len; ++k) dstr[k] = BIAS;
	dstr[len] = '\n';
	dstr[len+1] = '\0';

        for (i = alpha; --i >= 0;)
	{
	    x = g[i+1];

	    while (x)
	    {
		TAKEBIT(j,x);
		k = j*alpha + i;
		dstr[k/6] += xbit[k%6];
	    }
	}
}

/************************************************************************/

void
writend(FILE *f, design *g, int n)
/* write design to file in d format */
{
        char dstr[MAXL+3];

        ntod(g,n,dstr);
        if (fputs(dstr,f) == EOF || ferror(f))
        {
            fprintf(stderr,">E writed : error on writing file\n");
            gt_abort("writend");
        }
}

/************************************************************************/

static void
gput(FILE *f, design *g, int beta)
/* Write Greechie format. */
{
        setword x;
        int alpha,i,j;
	int v[MAXB][MAXA],*vi[MAXB],*vv;

        alpha = g[0];

	if (alpha > 90)
	{
	    fprintf(stderr,">E This format only supports alpha <= 90\n");
	    exit(1);
	}

	for (i = 0; i < beta; ++i) vi[i] = v[i];

	for (j = 0; j < alpha; ++j)
        {
            x = g[j+1];
            while (x)
            {
                TAKEBIT(i,x);
		*(vi[i]++) = alpha-j-1;
            }
        }

        for (i = 0; i < beta; ++i)
        {
	    for (vv = vi[i]; --vv >= v[i]; )
		fprintf(f,"%c",atomname[*vv]);
	    if (i < beta-1) fprintf(f,",");
	    else            fprintf(f,".\n");
        }
}

/************************************************************************/

static boolean
isconnected(design *g, int del)
/* Test if g minus block del is connected except for isolated atoms */
{
	int alpha,i,j;
	setword x,oldx;
	setword gdel;

	gdel = bit[del];
	
	alpha = g[0];
	for (j = 1; j <= alpha; ++j)
	    if (g[j] != gdel) break;

	if (j > alpha) return TRUE;

	x = g[j];
	do
	{
	    oldx = x;
	    for (i = j+1; i <= alpha; ++i)
		if (g[i] & x & ~gdel)
		{
		    x |= g[i];
		    if (i == j+1) ++j;
		}
	} while (oldx != x);

	x |= gdel;
	for (i = 1; i <= alpha; ++i)
	    if ((g[i] & ~x) != 0) return FALSE;

	return TRUE;
}

/************************************************************************/

static UPROC
storegens(int count, int *perm, int *orbits, int numorbits,
          int stabvertex, int n)
/* Store generators for possible later use. */
{
	int i;

	for (i = 0; i < n; ++i) blockgen[count-1][i] = perm[i];
}

/************************************************************************/

static void
got_one(design *g, int beta, int feet)
{
	int alpha;

	alpha = g[0];

	if (alpha <= maxa && alpha >= mina)
	{
	    outproc(outfile,g,beta);
	    ++count[alpha][beta];
	}
}

/************************************************************************/

static void
make_exts(int level, int *v, int *maxv, int nmaxv, set *sofar,
                                         int mininter, int maxinter, int m)
/* Make extension intersections.  Recursive.  Result should be sorted. 
   v[] is a list of indexes into maxv[]  */
{
	size_t nx,newsize;
	int i,imin,j,vl;

	if (level >= mininter && level <= maxinter)
	{
	    nx = xlistp - xlist;
	    if (nx + m > xlist_sz)
	    {
		newsize = (5*xlist_sz)/4 + 1000;
		DYNREALLOC(set,xlist,xlist_sz,newsize,"realloc()");
		xlistp = xlist + nx;
	    }
	    for (i = 0; i < m; ++i) xlistp[i] = sofar[i];
	    xlistp += m;
	}

	if (level >= maxinter) return;

	imin = (level == 0 ? 0 : v[level-1]+1);
	for (i = nmaxv; --i >= imin; )
	{
	    vl = maxv[i];
	    for (j = 0; j < level; ++j)
		if (isclose[vl][maxv[v[j]]]) break;
	    if (j == level)
	    {
		v[level] = i;
		ADDELEMENT(sofar,maxv[i]);
		make_exts(level+1,v,maxv,nmaxv,sofar,mininter,maxinter,m);
		DELELEMENT(sofar,maxv[i]);
	    }
	}
}

/************************************************************************/

static boolean
accept(design *g, int beta, int feet, int *ankle, int *size)
/* See if the last block is accepted.  If so, find the block group. */
{
	int lab[MAXB],ptn[MAXB],orbits[MAXB];
        long wt0,wt,x[MAXB];
        design h[MAXA+1];
        int count[MAXB];
        int i,alpha,numcells,code;
        set active[MAXM];
        statsblk stats;
        static DEFAULTOPTIONS_DES(options);
        setword workspace[50],w,parity;
	int numeq;

	numeq = 0;
	if (ankle[beta-1] >= 0)               /* case of foot */
	{
	    w = g[ankle[beta-1]+1];
	    wt0 = 0x4000L | (size[beta-1] << 8) | POPCOUNT(w);

	    for (i = beta-1; --i >= 0;)
	    {
		if (ankle[i] >= 0)
		{
		    w = g[ankle[i]+1];
		    wt = 0x4000L | (size[i] << 8) | POPCOUNT(w);
		    if (wt > wt0) return FALSE;
		    if (wt == wt0) ++numeq;
		}
		else
		    wt = size[i] << 8;
		x[i] = (wt << 8) | i;
	    }
	    x[beta-1] = (wt0 << 8) | (beta-1);
	}
	else                                /* no feet at all */
	{
	    if (feet) return FALSE;
	    alpha = g[0]; 

	    parity = 0;
	    for (i = 1; i <= alpha; ++i)
	    {
		w = g[i];
		IFLE1BITS(w) parity ^= w;
	    }

	    wt0 = (size[beta-1] << 8) | ((bit[beta-1] & parity) == 0);
	    for (i = beta-1; --i >= 0;)
	    {
		wt = (size[i] << 8) | ((bit[i] & parity) == 0);
		if (wt >= wt0 && isconnected(g,i))
		{
		    if (wt > wt0) return FALSE;
		    if (wt == wt0) ++numeq;
		    wt |= 0x10000;
		}
		x[i] = (wt << 8) | i;
	    }
	    x[beta-1] = 0x1000000 | (wt0 << 8) | (beta-1);
	}

	if (beta == numb && numeq == 0) return TRUE;

	lsort(x,beta);

	EMPTYSET(active,1);
        ADDELEMENT(active,0);
        numcells = 1;

        for (i = 0; i < beta; ++i)
        {
            lab[i] = x[i] & 0xff;
            if (i == beta-1)
                ptn[i] = 0;
            else if ((x[i+1] >> 8) != (x[i] >> 8))
            {
                ++numcells;
                ADDELEMENT(active,i+1);
                ptn[i] = 0;
            }
            else
                ptn[i] = 1;
        }

        refine_des((graph*)g,lab,ptn,0,&numcells,count,active,&code,1,beta);

	if (ptn[beta-2] == 0)   /* last cell is singelton */
	{
	    if (lab[beta-1] != beta-1) return FALSE;
	    if (beta == numb) return TRUE;
	}

        if (numcells == beta)          /* discrete */
        {
	    numgens = 0;
            return TRUE;
        }

	if (lab[beta-1] != beta-1)
	{
	    for (i = beta-2; ptn[i] > 0 && lab[i] != beta-1; --i) {}
	    if (ptn[i] == 0) return FALSE;
	}

        options.getcanon = TRUE;
        options.defaultptn = FALSE;
	options.userautomproc = (beta == numb ? NULL : storegens);

        EMPTYSET(active,1);
        nauty((graph*)g,lab,ptn,active,orbits,&options,&stats,
                        workspace,50,1,beta,(graph*)h);
	numgens = stats.numgenerators;

        return  orbits[lab[beta-1]] == orbits[beta-1];
}

/************************************************************************/

static void
extend(design *g, int beta, int feet, int *ankle, int *size, int numbig)
/* g is accepted and the block group is known if beta < numb.
   ankle[i] = -1 if block i is not a foot, and is the ankle otherwise.
   ankle is 0-origin. numbig is the number of big blocks, feasible. */
{
	int i,j,k,m,mininter,maxinter,alpha;
	int v[MAXA],ank,newankle[MAXB],newfeet;
	int nmaxv,maxv[MAXA],nplaces;
	int aperm[MAXA];
	int ix,extra,minextra,maxextra;
	design gx[MAXA+1];
	setword betabit,x;
	int lo,mid,hi,sz;
	set ximage[(MAXA+WORDSIZE-1)/WORDSIZE];
	set *xmid,*xintp;
	int minbs,maxbs;

	if (beta == numb)
	{
	    if (!fswitch || feet == 0) got_one(g,beta,feet);
	    return;
	}

	if (beta == splitlevel)
	{
#ifdef SPLITTEST
	    ++splitcases;
	    return;
#else
	    if (res-- != 0) return;
	    res = mod - 1;
#endif
	}

	alpha = g[0];

	m = (alpha + WORDSIZE - 1) / WORDSIZE;

	minbs = minblocksize;
	maxbs = maxblocksize;

	if (numbig == maxbig) maxbs = minblocksize;
	if (numbig+numb-beta == minbig) minbs = minblocksize+1;

	mininter = alpha + minbs - maxa;
	if (mininter < 1) mininter = 1;
	if (fswitch && beta == numb-1)
	{
	    if (mininter == 1) mininter = 2;
	    if (feet > mininter) mininter = feet;
	    if (feet >= 2 && mincycle >= 4)
	    {
		EMPTYSET(ximage,m);
		for (i = 0; i < beta; ++i)
		{
		    j = ankle[i];
		    if (j >= 0)
		    {
			if (ISELEMENT(ximage,j)) return;
			ADDELEMENT(ximage,j);
		    }
		}
	    }	
	}

	maxinter = (maxbs > alpha ? alpha : maxbs);

	if (maxinter < mininter) return;

	if (mininter > minbs) minbs = mininter;

	make_close(g);

	nmaxv = 0;
	for (i = 1; i < alpha; ++i)
	    if (g[i] != g[i+1]) maxv[nmaxv++] = i-1;
	maxv[nmaxv++] = alpha-1;

	xlistp = xlist;
	EMPTYSET(ximage,m);
	make_exts(0,v,maxv,nmaxv,ximage,mininter,maxinter,m);
	nplaces = (xlistp - xlist) / m;

	if (nplaces == 0) return;

	if (numgens == 0)
	{
	    DYNALLOC1(set,xint[beta],xint_sz[beta],m*nplaces,"malloc A");
	    for (i = m*nplaces; --i >= 0; ) xint[beta][i] = xlist[i];
	}
	else
	{
	    DYNALLOC1(int,xperm,xperm_sz,nplaces,"malloc");
	    DYNALLOC1(int,xorbits,xorbits_sz,nplaces,"malloc");
	    for (i = 0; i < nplaces; ++i) xorbits[i] = i;

	    for (i = 0; i < numgens; ++i)
	    {
		atomperm(g,blockgen[i],aperm);
		for (j = 0, xlistp = xlist; j < nplaces; ++j, xlistp += m)
		{
		    permset(xlistp,ximage,m,aperm);
		    lo = 0;
                    hi = nplaces-1;
            	    for (;;)
            	    {
                	mid = (lo + hi) / 2;
			xmid = xlist + m * mid;
			for (k = 0; k < m; ++k)
			    if (ximage[k] != xmid[k]) break;
			if (k == m) break;
			else if (xmid[k] < ximage[k]) lo = mid + 1;
			else                          hi = mid - 1;
            	    }
            	    xperm[j] = mid;
		}
		orbjoin(xorbits,xperm,nplaces);
	    }

	    k = 0;
	    for (i = 0; i < nplaces; ++i) if (xorbits[i] == i) ++k;
	    DYNALLOC1(set,xint[beta],xint_sz[beta],m*k,"malloc");

	    xintp = xint[beta];
	    for (j = 0, xlistp = xlist; j < nplaces; ++j, xlistp += m)
		if (xorbits[j] == j)
		    for (i = 0; i < m; ++i) *(xintp++) = xlistp[i];
	    nplaces = k;
	}

	betabit = bit[beta];
/*	for (ix = 0, xintp = xint[beta]; ix < nplaces; ++ix, xintp += m) */
	for (ix = nplaces, xintp = xint[beta]+m*(size_t)(nplaces-1);
						--ix >= 0; xintp -= m)
	{
	    sz = 0;
	    for (i = 0; i < m; ++i) sz += POPCOUNT(xintp[i]);

	    if (minbs > sz) minextra = minbs - sz;
	    else            minextra = 0;

	    if (maxbs-sz < maxa-alpha) maxextra = maxbs - sz;
	    else                       maxextra = maxa - alpha;

	    for (i = 1; i <= minextra; ++i) gx[i] = betabit;
	    for (i = 1; i <= alpha; ++i) gx[minextra+i] = g[i];

	    for (i = 0; i < beta; ++i) newankle[i] = ankle[i];

	    for (j = -1; (j = nextelement(xintp,m,j)) >= 0; )
	    {
		gx[minextra+j+1] |= betabit;
		ank = j;
		x = g[j+1];
		while (x)
		{
		    TAKEBIT(i,x);
		    if (newankle[i] != j) newankle[i] = -1;
		}
	    }
	    gx[0] = alpha + minextra;

	    if (sz == 1) newankle[beta] = ank;
	    else         newankle[beta] = -1;

	    newfeet = 0;
	    for (i = 0; i <= beta; ++i)
		if (newankle[i] >= 0)
		{
		    newankle[i] += minextra;
		    ++newfeet;
		}

	    size[beta] = sz + minextra;

	    for (extra = minextra; ; ++extra)
	    {
#if STATS
		++ncand[beta+1];
#endif
		if (accept(gx,beta+1,newfeet,newankle,size))
		{
#if STATS
		    ++naccept[beta+1];
#endif
		    extend(gx,beta+1,newfeet,newankle,size,
					numbig+(size[beta]>minblocksize));
		}
		if (extra == maxextra) break;

		for (i = 0; i <= beta; ++i)
		    if (newankle[i] >= 0) ++newankle[i];
		for (i = gx[0]; i >= 1; --i) gx[i+1] = gx[i];
		gx[1] = betabit;
		++gx[0];
		++size[beta];
	    }
	}
}

/************************************************************************/

static void
start(void)
/* Put in first two blocks and handle the one-block case. */
{
	design g[MAXA+1];
	int i,sz,sz0,sz1,size[MAXB],ankle[MAXB];
	int numbig;

	if (numb == 1)
	{
	    for (sz = minblocksize; sz <= maxblocksize; ++sz)
	    {
		g[0] = sz;
		for (i = 1; i <= sz; ++i) g[i] = bit[0];
		ankle[0] = -1;
		size[0] = sz;
		got_one(g,1,0);
	    }
	    return;
	}

	DYNALLOC1(set,xlist,xlist_sz,16,"malloc()");

	for (sz0 = minblocksize; sz0 <= maxblocksize; ++sz0)
	for (sz1 = sz0; sz1 <= maxblocksize && sz1 <= maxa - sz0 + 1; ++sz1)
	{
	    sz = sz0 + sz1 - 1;
	    g[0] = sz;
	    size[0] = sz0;
	    size[1] = sz1;
	    for (i = 1; i < sz1; ++i) g[i] = bit[1];
	    for (i = sz1; i < sz; ++i) g[i] = bit[0];
	    g[sz] = bit[0] | bit[1];
	    if (sz0 == sz1)
	    {
		numgens = 1;
		blockgen[0][0] = 1;
		blockgen[0][1] = 0;
	    }
	    else
	        numgens = 0;

	    ankle[0] = ankle[1] = sz-1;
	    numbig = (sz0>minblocksize) + (sz1>minblocksize);
	    if (numbig+numb-2 >= minbig && numbig <= maxbig)
	        extend(g,2,2,ankle,size,numbig);
	}
}

/************************************************************************/

static void
decode_limits(void)
/* Figure out all the switches describing the parameters. */
{
	int i,j;

	if (mincycle == 3) { bupper = bupper3; make_close = make_close3; }
	if (mincycle == 4) { bupper = bupper4; make_close = make_close4; }
	if (mincycle == 5) { bupper = bupper5; make_close = make_close5; }

	for (i = 0; bupper[i] >= 0; ++i) {}

	for ( ; i <= MAXA+1; ++i)
	    bupper[i] = (bupper[i-1] * i) / (i - 3);

	if (mina < 0) mina = 0;
	if (maxa > MAXA) maxa = MAXA;

	while (bupper[mina] < numb && mina <= maxa) ++mina;

	if (maxa < mina)
	{
	    fprintf(stderr,"No such diagrams exist\n");
	    exit(1);
	}

	if (minblocksize == 0) minblocksize = 3;
	if (maxblocksize == 0 || maxblocksize > maxa) maxblocksize = maxa;
	if (minblocksize < 3 || maxblocksize < minblocksize)
	{
	    fprintf(stderr,">E illegal -z switch\n");
	    exit(1);
	}

	if (maxbig == 0 && minbig > 0) maxbig = numb;
	if (minblocksize == maxblocksize) maxbig = 0;
	if (maxbig > numb) maxbig = numb;
	if (minbig > maxbig)
	{
	    fprintf(stderr,">E impossible -B values\n");
	    exit(1);
	}
}

/*************************************************************************/

#if 0
// Now defined in gtools.c
static int
longvalue(char **ps, long *l)
{
        boolean neg,pos;
        long sofar,last;
        char *s;

        s = *ps;
        pos = neg = FALSE;
        if (*s == '-')
        {
            neg = TRUE;
            ++s;
        }
        else if (*s == '+')
        {
            pos = TRUE;
            ++s;
        }

        if (*s < '0' || *s > '9')
        {
            *ps = s;
            return (pos || neg) ? ARG_ILLEGAL : ARG_MISSING;
        }

        sofar = 0;

        for (; *s >= '0' && *s <= '9'; ++s)
        {
            last = sofar;
            sofar = sofar * 10 + (*s - '0');
            if (sofar < last || sofar > MAXARG)
            {
                *ps = s;
                return ARG_TOOBIG;
            }
        }
        *ps = s;
        *l = neg ? -sofar : sofar;
        return ARG_OK;
}
#endif

/*************************************************************************/

static void
arg_int_g(char **ps, int *val, char *id)
{
        int code;
        long longval;

        code = longvalue(ps,&longval);
        *val = longval;
        if (code == ARG_MISSING || code == ARG_ILLEGAL)
        {
            fprintf(stderr,">E %s: missing argument value\n",id);
            gt_abort(NULL);
        }
        else if (code == ARG_TOOBIG || *val != longval)
        {
            fprintf(stderr,">E %s: argument value too large\n",id);
            gt_abort(NULL);
        }
}

/************************************************************************/

static void
arg_range_g(char **ps, char *sep, int *val1, int *val2, char *id)
{
        int code,i;
        char *s;
	long longval1,longval2;

        s = *ps;
        code = longvalue(&s,&longval1);
        if (code != ARG_MISSING)
        {
            if (code == ARG_ILLEGAL)
            {
                fprintf(stderr,">E %s: bad range\n",id);
                gt_abort(NULL);
            }
            else if (code == ARG_TOOBIG)
            {
                fprintf(stderr,">E %s: value too big\n",id);
                gt_abort(NULL);
            }
        }
        else if (*s == '\0' || strchr(sep,*s) == NULL)
        {
            fprintf(stderr,">E %s: missing value\n",id);
            gt_abort(NULL);
        }
        else
            longval1 = -NOLIMIT;

        if (*s != '\0' && strchr(sep,*s) != NULL)
        {
            ++s;
            code = longvalue(&s,&longval2);
            if (code == ARG_MISSING)
                longval2 = NOLIMIT;
            else if (code == ARG_TOOBIG)
            {
                fprintf(stderr,">E %s: value too big\n",id);
                gt_abort(NULL);
            }
            else if (code == ARG_ILLEGAL)
            {
                fprintf(stderr,">E %s: illegal range\n",id);
                gt_abort(NULL);
            }
        }
        else
            longval2 = longval1;

        *ps = s;
	*val1 = longval1;
	*val2 = longval2;
	if (*val1 != longval1 || *val2 != longval2)
	{
	    fprintf(stderr,">E %s: value too big for int\n",id);
	    gt_abort(NULL);
	}
}

/************************************************************************/
/************************************************************************/

int
main(int argc, char *argv[])
{
        char *arg,sw,*outfilename;
        boolean badargs;
        int i,j,argnum;
        double time0,time1,cputime;
	boolean qswitch,sswitch,dswitch,uswitch;
	boolean eswitch,bswitch,aswitch,vswitch;
	boolean Bswitch,zswitch,lswitch;

        if (argc > 1 && (strcmp(argv[1],"-help") == 0
		       || strcmp(argv[1],"--help") == 0))
        {
            printf("\nUsage: %s\n\n%s",USAGE,HELPTEXT);
            return 0;
        }

	fprintf(stderr,">A");
	for (i = 0; i < argc; ++i)
	    fprintf(stderr," %s",argv[i]);
	fprintf(stderr,"\n");

        nauty_check(WORDSIZE,1,MAXN,NAUTYVERSIONID);
        nautil_check(WORDSIZE,(MAXA+WORDSIZE-1)/WORDSIZE,MAXA,NAUTYVERSIONID);
	naudesign_check(WORDSIZE,1,MAXN,NAUTYVERSIONID);

	qswitch = sswitch = dswitch = fswitch = FALSE;
	uswitch = eswitch = bswitch = aswitch = vswitch = FALSE;
	lswitch = zswitch = Bswitch = FALSE;
        outfilename = NULL;
	minbig = mina = 0;
	maxbig = maxa = NOLIMIT;

        argnum = 0;
        badargs = FALSE;

        for (j = 1; !badargs && j < argc; ++j)
        {
            arg = argv[j];
            if (arg[0] == '-' && arg[1] != '\0')
            {
                ++arg;
                while (*arg != '\0')
                {
                    sw = *arg++;
                         SWBOOLEAN('f',fswitch)
                    else SWBOOLEAN('q',qswitch)
                    else SWBOOLEAN('d',dswitch)
                    else SWBOOLEAN('u',uswitch)
                    else SWRANGE('s',"/",sswitch,res,mod,"gengre -s")
                    else SWRANGE('a',":-",aswitch,mina,maxa,"gengre -a")
                    else SWRANGE('v',":-",vswitch,mina,maxa,"gengre -v")
                    else SWRANGE('z',":-",zswitch,
				 minblocksize,maxblocksize,"gengre -z")
                    else SWRANGE('B',":-",Bswitch,
				 minbig,maxbig,"gengre -B")
                    else SWINT('e',eswitch,numb,"gengre -e")
                    else SWINT('b',bswitch,numb,"gengre -b")
                    else SWINT('l',lswitch,mincycle,"gengre -l")
                    else badargs = TRUE;
                }
            }
            else
            {
                ++argnum;
                if (argnum == 1) outfilename = arg;
                else             badargs = TRUE;
            }
        }

        if (badargs)
        {
            fprintf(stderr,">E Usage: %s\n",USAGE);
            exit(1);
        }

	if ((aswitch && vswitch) || (bswitch && eswitch) || (uswitch && dswitch))
	{
	    fprintf(stderr,">E -a/-v, -b/-e, and -u/-d are incompatible\n");
	    exit(1);
	}

	if (!bswitch)
	{
	    fprintf(stderr,">E the -b switch is compulsory\n");
	    exit(1);
	}

	if (numb > MAXB)
	{
	    fprintf(stderr,">E this edition can only manage %d blocks\n",MAXB);
	    exit(1);
	}

	if (!lswitch) mincycle = 5;
	if (mincycle < 3 || mincycle > 5)
	{
            fprintf(stderr,">E the value of -l can only be 3, 4 or 5\n");
            exit(1);
        }

	if (!zswitch) minblocksize = maxblocksize = 3;
	decode_limits();

#ifdef SPLITTEST
	sswitch = TRUE; res = 0; mod = 1;
#endif
	if (sswitch)
	{
	    if (res < 0 || res >= mod)
	    {
	        fprintf(stderr,">E must have 0 <= res < mod for -s values\n");
		exit(1);
	    }
	    if (numb >= 15) splitlevel = 12;
	    else            splitlevel = numb-3;
	    if (splitlevel > maxa-12) splitlevel = maxa-12;
	    if (splitlevel < 1) splitlevel = 0;	
	}
	else 
	    splitlevel = 0;

#ifdef SPLITTEST
	splitcases = 0;
	fprintf(stderr,"Splitting level = %d blocks\n",splitlevel);
	uswitch = TRUE;
#endif

        for (i = 0; i <= MAXA; ++i)
	for (j = 0; j <= MAXB; ++j)
	    count[i][j] = 0;

     /* open output file */

        if (outfilename == NULL)
        {
            outfilename = "stdout";
            outfile = stdout;
        }
        else if ((outfile = fopen(outfilename,"w")) == NULL)
        {
            fprintf(stderr,
                  ">E gengre: can't open %s for writing\n",outfilename);
            gt_abort("gengre");
        }

	if (dswitch)      outproc = writend;
	else if (uswitch) outproc = nullwrite;
	else              outproc = gput;


#if GETCPUTIME
        time0 = CPUTIME;
#endif

	start();

#if GETCPUTIME
        time1 = CPUTIME;
	cputime = time1 - time0;
#else
	cputime = 0.0;
#endif
	
	nout = 0;
	for (i = 0; i <= MAXA; ++i)
        for (j = 0; j <= MAXB; ++j)
	    nout += count[i][j];

	if (!qswitch)
	{
	    for (i = 0; i <= MAXA; ++i)
            for (j = 0; j <= MAXB; ++j)
	        if (count[i][j] != 0)
		    fprintf(stderr,
			"%9ld %sdiagrams with %2d atoms and %2d blocks\n",
		           count[i][j],(fswitch?"foot-free ":""),i,j);
	}

#if STATS
	for (i = 0; i <= numb; ++i)
	    if (ncand[i])
		fprintf(stderr,">C %9ld accepted out of %9ld on level %d\n",
			       naccept[i],ncand[i],i);
#endif

	if (outproc == nullwrite)
	    fprintf(stderr,">Z %6ld diagrams generated in %4.2f seconds\n",
                            nout,cputime);
	else
            fprintf(stderr,">Z %6ld diagrams written to %s in %4.2f seconds\n",
                            nout,outfilename,cputime);
#ifdef SPLITTEST
	fprintf(stderr,"%ld splitting cases\n",splitcases);
#endif

        return 0;
}
