/* greechie.c : generate connected Greechie-3-L diagrams */

#define USAGE "greechie [-v#:#] [-e#:#] [-f] [-d|-u] [-q] [-s#/#] [outfile]"

#define HELPTEXT \
"Generate connected Greechie-3-L diagrams.\n\
    outfile  is the output file (missing or \'-\' means stdout)\n\
    -f : only output diagrams with no feet (and therefore no legs)\n\
    -v# : specify the number of vertices, or a range -v#:#\n\
    -e# : specify the number of edges, or a range -e#:#\n\
       Eg: -v:10 -e13 -e10:12.  At least one of -v or -e is required.\n\
    -d : write in \'d\' format\n\
    -u : no output, just count\n\
    -q : suppress detailed counts\n\
    -s#/# : only present a fraction of the output.  The two numbers are\n\
        res/mod where 0 <= res <= mod-1.  The set of all diagrams is\n\
        divided into mod disjoint classes, and only class res is generated.\n"

/*
    Author:  Brendan McKay, Dec 1999.    bdm@cs.anu.edu.au
    Updated for nauty 2.6, June 2016.

**************************************************************************/

#undef MAXN
#define MAXN (WORDSIZE>32?63:WORDSIZE) 
    /* In this version, MAXN can be at most max(WORDSIZE,63). */

#include "gtools.h"   /* which includes stdio.h */
#include "naudesign.h"

#undef MAXB
#define MAXB 80   /* Not higher than in naudesign.h */

static setword *placeslist[MAXB+2] = {NULL};
static int *placeorbitslist[MAXB+2] = {NULL};

/*====================================================================*/

/* Define the default format (without -d or -u).  */

static char atomname[] = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ\
abcdefghijklmnopqrstuvwxyz!\"#$%&'()*-/:;<=>?@[\\]^_`{|}~";

/* These assignments will cause output like
49B,38A,246,135,127.   (including the period)
The vertex numbers are taken from atomname[]. */

#define BETWEEN_VERTICES ""
#define BETWEEN_BLOCKS   ","
#define AT_THE_END       ".\n"

/*These assignments will cause output like
+ 4,9,11; 3,8,10; 2,4,6; 1,3,5; 1,2,7;

#define BETWEEN_VERTICES ","
#define BETWEEN_BLOCKS   "; "
#define AT_THE_END       ";\n"
*/

/*========================================================*/

#define GIVECPUTIME 1  /* Whether to measure the cpu time or not */

#define ARG_OK 0
#define ARG_MISSING 1
#define ARG_TOOBIG 2
#define ARG_ILLEGAL 3
#undef NOLIMIT
#define NOLIMIT (MAXARG+1L)

#if 0
#define SWBOOLEAN(c,boool) if (sw==c) boool=TRUE;
#define SWINT(c,boool,val,id) if (sw==c) \
        {boool=TRUE;arg_int(&arg,&val,id);}
#define SWLONG(c,boool,val,id) if (sw==c) \
        {boool=TRUE;arg_long(&arg,&val,id);}
#endif
#undef SWRANGE
#define SWRANGE(c,sep,boool,val1,val2,id) if (sw==c) \
        {boool=TRUE;arg_range_g(&arg,sep,&val1,&val2,id);}

static FILE *outfile;
static long nout;

#define IF2BITS(ww) ww &= ww-1; if (ww && !(ww&(ww-1)))
#define IFLE2BITS(ww) ww &= ww-1; if (!(ww&(ww-1)))
#define IF1BITS(ww)  if (ww && !(ww&(ww-1)))
#define IFLE1BITS(ww)  if (!(ww&(ww-1)))

#define MAXNX (MAXN*(MAXN*MAXN+5)/6)
static setword *xset;
static int *xorbits;
static int nxset;

static boolean fswitch;
static int minv,maxv,minb,maxb;
static int splitlevel,mod,res;
static long splitcases;
static void extend(design*,int);
static void (*outproc)();
static long count[MAXN+1][MAXB+1];

#define STATS 0
static long ngen1,ngen2,ngen3,accept1,accept2,accept3;

/************************************************************************/

extern int longvalue(char**,long*);

void
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

static void
makeplaces(int b)
{
    if (placeslist[b] != NULL) return;

    placeslist[b] = (setword*)malloc(MAXNX*sizeof(setword));
    placeorbitslist[b] = (int*)malloc(MAXNX*sizeof(int));

    if (placeslist[b] == NULL || placeorbitslist[b] == NULL)
	gt_abort(">E Ran out of memory\n");
}

/************************************************************************/

static setword
once(design *g)
/* Find the vertices used exactly once */
{
	setword x1,x2;
	int i,b;

	b = g[0];
	x1 = x2 = 0;
	for (i = 1; i <= b; ++i)
	{
	    x2 |= x1 & g[i];
	    x1 = (x1 | g[i]) & ~x2;
	}

	return x1;
}

/************************************************************************/

static void
nullwrite(FILE *f, design *g, int n)
{
}

/************************************************************************/

void ntod(design *g, int n, char *dstr)
/* convert design to d-string, \n and \0 terminated */
{
#define BIAS ((char)63)
	static char xbit[] = {32,16,8,4,2,1};
        register int i,j,k;
        int b;
        register char y;

        b = g[0];
        if (n > MAXN || b > MAXB)
        {
            fprintf(stderr,">E n or b too large for dtoy\n");
            exit(2);
        }

        *(dstr++) = n + BIAS;
        *(dstr++) = (b >> 6) + BIAS;
        *(dstr++) = (b & 077) + BIAS;

        y = 0;

        k = -1;
        for (j = 1; j <= b; ++j)
        for (i = n; --i >= 0;)
        {
            if (++k == 6)
            {
                *(dstr++) = y + BIAS;
                y = 0;
                k = 0;
            }
            if (g[j] & bit[i]) y |= xbit[k];
        }
        if (n > 0 && b > 0) *(dstr++) = y + BIAS;
        *(dstr++) = '\n';
        *dstr = '\0';
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
gput(FILE *f, design *g, int n)
{
        setword x;
        int b,i,j;

	if (BETWEEN_VERTICES[0] != '\0') fprintf(f,"+ ");

        b = g[0];
        for (j = 1; j <= b; ++j)
        {
            x = g[j];
            while (x)
            {
		TAKEBIT(i,x);
		if (BETWEEN_VERTICES[0] == '\0')
		    fprintf(f,"%c",atomname[i]);
		else
		{
		    fprintf(f,"%d",i+1);
		    if (x) fprintf(f,"%s",BETWEEN_VERTICES);
		}
            }
	    if (j < b && BETWEEN_BLOCKS != NULL)
		fprintf(f,"%s",BETWEEN_BLOCKS);
        }
        fprintf(f,"%s",AT_THE_END);
}

/************************************************************************/

static boolean
isconnected(design *g, int del)
/* Test if g minus block del is connected except for isolated vertices */
{
	int b,j;
	setword x,oldx;
	setword gdel;

	gdel = g[del];
	
	b = g[0]-1;
	if (b == 0) return TRUE;
	g[del] = g[b+1];

	x = g[1];
	do
	{
	    oldx = x;
	    for (j = 2; j <= b; ++j)
		if (g[j]&x) x |= g[j];
	} while (oldx != x);

	for (j = 2; j <= b; ++j)
	    if ((g[j]&x) == 0) break;

	g[del] = gdel;
	return j > b;
}

/************************************************************************/

static UPROC
setorbits(int count, int *perm, int *orbits, int numorbits,
          int stabvertex, int n)
/* Develop the orbits on a sorted list of sets (known closed under perm */
{
	register setword x,px;
	int i,j,lo,hi,mid;
	int xperm[MAXNX];

	for (i = 0; i < nxset; ++i)
	{
	    x = xset[i];
	    px = 0;
	    while (x)
	    {
		TAKEBIT(j,x);
		px |= bit[perm[j]];
	    }

	    lo = 0;
	    hi = nxset-1;
	    for (;;)
	    {
		mid = (lo + hi) / 2;
		if     (xset[mid] == px) break;
		else if (xset[mid] < px) lo = mid + 1;
		else                     hi = mid - 1;
	    }
	    xperm[i] = mid;
	}

	orbjoin(xorbits,xperm,nxset);
}

/************************************************************************/

static void
lsort(long *x, int k)
{
        register int i,j,h;
        register long iw;

        j = k / 3;
        h = 1;
        do
            h = 3 * h + 1;
        while (h < j);

        do
        {
            for (i = h; i < k; ++i)
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

/************************************************************************/

static boolean
acceptfoot(design *g, int n, design *h, char *fmt, int lastfoot)
/*  canonise g under format fmt; result in h
    Accept or reject according to foot position */
{
        int lab[MAXN],ptn[MAXN],orbits[MAXN];
        long x[MAXN];
        design gs[1+MAXB];
        int count[MAXN];
        register int i;
        int b,numcells,code;
        set active[MAXM];
        statsblk stats;
        static DEFAULTOPTIONS_DES(options);
        setword workspace[50];

        b = g[0];

        for (i = 0; i < n; ++i)
            x[i] = (fmt[i] << 16) | i;
        lsort(x,n);

        EMPTYSET(active,1);
        ADDELEMENT(active,0);
        numcells = 1;

        for (i = 0; i < n; ++i)
        {
            lab[i] = x[i] & 0xffff;
            if (i == n-1)
                ptn[i] = 0;
            else if ((x[i+1] >> 16) != (x[i] >> 16))
            {
                ++numcells;
                ADDELEMENT(active,i+1);
                ptn[i] = 0;
            }
            else
                ptn[i] = 1;
        }

        refine_des((graph*)g,lab,ptn,0,&numcells,count,active,&code,1,n);

        if (numcells == n)          /* discrete */
        {
	    if (lab[n-1] != lastfoot) return FALSE;
            for (i = 0; i < n; ++i)
                count[i] = lab[i];
            updatecan_des((graph*)g,(graph*)h,count,0,1,n);
	    return TRUE;
        }
        else
        {
            for (i = 0; i <= b; ++i) gs[i] = g[i];
            shell_des(&gs[1],1,b);

            options.getcanon = TRUE;
            options.defaultptn = FALSE;

            EMPTYSET(active,1);
            nauty((graph*)gs,lab,ptn,active,orbits,&options,&stats,
			workspace,50,1,n,(graph*)h);
	    return orbits[lab[n-1]] == orbits[lastfoot];
        }
}

/************************************************************************/

static boolean
acceptfootless(design *g, int n, design *h, char *fmt,
	       boolean gbtype, int gbdeg)
/*  canonise g under format fmt; result in h
    Accept or reject according to last block */
{
        int lab[MAXN],ptn[MAXN],orbits[MAXN];
        long xx[MAXN];
        design gs[1+MAXB];
        int count[MAXN];
        register int i,j;
        int b,numcells,code;
        set active[MAXM];
        statsblk stats;
	setword x,y;
        static DEFAULTOPTIONS_DES(options);
        setword workspace[200];
	setword newblock,x1;
	int blockorbits[MAXB];
	int v1,v2,v3,gideg;
	int k,degree[MAXN];

        b = g[0];
	newblock = g[b];

        for (i = 0; i < n; ++i)
            xx[i] = (fmt[i] << 16) | i;
        lsort(xx,n);

        EMPTYSET(active,1);
        ADDELEMENT(active,0);
        numcells = 1;

        for (i = 0; i < n; ++i)
        {
            lab[i] = xx[i] & 0xffff;
            if (i == n-1)
                ptn[i] = 0;
            else if ((xx[i+1] >> 16) != (xx[i] >> 16))
            {
                ++numcells;
                ADDELEMENT(active,i+1);
                ptn[i] = 0;
            }
            else
                ptn[i] = 1;
        }

        for (i = 0; i <= b; ++i)
             gs[i] = g[i];
        shell_des(&gs[1],1,b);

	nxset = b;
	xset = &gs[1];
	xorbits = blockorbits;
	for (i = 0; i < b; ++i)
	    blockorbits[i] = i;

        options.getcanon = TRUE;
        options.defaultptn = FALSE;
	options.userautomproc = setorbits;

        nauty((graph*)gs,lab,ptn,active,orbits,&options,&stats,
		workspace,200,1,n,(graph*)h);

	x1 = once(h);

	for (i = 0; i < n; ++i)
	    degree[i] = 0;

	for (j = 1; j <= b; ++j)
        {
            x = h[j] & ~x1;
            while (x)
            {
                TAKEBIT(k,x);
                ++degree[k];
            }
        }

	for (i = b; i >= 1; --i)
	    if (((h[i] & x1) != 0) == gbtype)
	    {
		x = h[i];
                TAKEBIT(v1,x); TAKEBIT(v2,x); v3 = FIRSTBIT(x);
                gideg = degree[v1] + degree[v2] + degree[v3];
		if (gideg == gbdeg && isconnected(h,i)) break;
	    }

	if (i == 0)
	{
	    fprintf(stderr,">E footless error 1\n");
	    exit(1);
	}

        /* h[i] is the major block. */

	x = h[i];
	y = 0;
	while (x)
	{
	    TAKEBIT(j,x);
	    y |= bit[lab[j]];
	}

	for (i = 1; i <= b; ++i)
	    if (gs[i] == y) break;

	if (i > b)
	{
            fprintf(stderr,">E footless error 2\n");
            exit(1);
        }

        for (j = 1; j <= b; ++j)
            if (gs[j] == g[b]) break;

        if (j > b)
        {
            fprintf(stderr,">E footless error 3\n");
            exit(1);
        }

	return blockorbits[i-1] == blockorbits[j-1];
}

/************************************************************************/

static void
got_one(design *g, int n, boolean hasfoot)
{
	int b;

	b = g[0];

	if (b <= maxb && n <= maxv && b >= minb && n >= minv)
	    if ((!hasfoot || !fswitch) && (b > splitlevel || res == 0))
	    {
	        outproc(outfile,g,n);
		++count[n][b];
	    }

	if (b < maxb) extend(g,n);
}

/************************************************************************/

static void
process(design *g, int n, setword x1)
{
        setword x;
        int i,j,k,b;
        char fmt[MAXN+1];
        design h[MAXB+1];
        int lastfoot;
        int degree[MAXN];  /* 0 instead of 1 */
        int ankle[MAXN],footdeg,maxfootdeg;
        int maxfoot[MAXN],nmaxfoot;
	boolean gbtype;
	int v1,v2,v3,gbeq,gbdeg,gideg;

        b = g[0];
	fmt[n] = '\0';

        for (i = 0; i < n; ++i)
        {
            fmt[i] = 'a';
            degree[i] = 0;
        }

        for (j = 1; j <= b; ++j)
        {
            x = g[j] & ~x1;
            while (x)
            {
                TAKEBIT(k,x);
                ++degree[k];
            }
        }

        lastfoot = -1;

	if (x1)
	{
            maxfootdeg = -1;
            for (j = 1; j <= b; ++j)
            {
                x = g[j] & x1;
                if (x)
                {
                    TAKEBIT(k,x);
                    fmt[k] = 'b';
                    if (x)
                    {
                        lastfoot = FIRSTBIT(x);
                        fmt[lastfoot] = 'c';
		        k = FIRSTBIT(g[j] & ~x1);
		        ankle[lastfoot] = k;
                        footdeg = degree[k];
                        if (footdeg == maxfootdeg)
                            maxfoot[nmaxfoot++] = lastfoot;
                        else if (footdeg > maxfootdeg)
                        {
                            nmaxfoot = 1;
                            maxfoot[0] = lastfoot;
                            maxfootdeg = footdeg;
                        }
                    }
                }
            }
	}

        if (lastfoot >= 0)
        {
#if STATS
	    ++ngen1;
#endif
            if (maxfoot[nmaxfoot-1] != lastfoot) return;
	    k = ankle[lastfoot];
	    for (i = nmaxfoot-1; --i >= 0;)
		if (ankle[maxfoot[i]] != k) break;
	    if (i < 0)
	    {
#if STATS
	            ++accept1;
#endif
        	got_one(g,n,TRUE);
		return;
	    }
            for (i = 0; i < nmaxfoot; ++i)
                fmt[maxfoot[i]] = 'd';
            if (!acceptfoot(g,n,h,fmt,lastfoot)) return;
#if STATS
	     ++accept1;
#endif
	    got_one(h,n,TRUE);
        }
	else
        {
	    gbtype = (g[b] & x1) != 0;
#if STATS
	    if (gbtype) ++ngen2;
	    else        ++ngen3;
#endif

	    if (gbtype)
	    {
		for (i = 1; i < b; ++i)
		    if ((g[i] & x1) == 0 && isconnected(g,i)) return;
	    }

	    x = g[b];
	    TAKEBIT(v1,x); TAKEBIT(v2,x); v3 = FIRSTBIT(x);
	    gbdeg = degree[v1] + degree[v2] + degree[v3];
	    gbeq = 1;

	    for (i = b; --i >= 1;)
		if (((g[i] & x1) != 0) == gbtype && isconnected(g,i))	    	
		{
		    x = g[i];
		    TAKEBIT(v1,x); TAKEBIT(v2,x); v3 = FIRSTBIT(x);
		    gideg = degree[v1] + degree[v2] + degree[v3];
		    if (gideg > gbdeg) return;
		    if (gideg == gbdeg) ++gbeq;
		}

	    if (gbeq == 1)
	    {
#if STATS
                if (gbtype) ++accept2;
                else        ++accept3;
#endif
                got_one(g,n,FALSE);
		return;
	    }

            if (!acceptfootless(g,n,h,fmt,gbtype,gbdeg)) return;
#if STATS
	    if (g[b] & x1) ++accept2;
	    else           ++accept3;
#endif
	    got_one(h,n,FALSE);
        }
}

/************************************************************************/

static void
extend(design *g, int n)
/* Extend by one edge */
{
        int i,j,k,b;
	graph close[MAXN];   /* distance <= 3 */
	setword x,y;
	setword x1,x2;
	setword foot[MAXB];
	int t,nfeet;
	design gs[MAXB+1];
	DEFAULTOPTIONS_DES(options);
	statsblk stats;
	int lab[MAXN],ptn[MAXN],orbits[MAXN];
	setword workspace[6*MAXM];
	setword *places;
	int *placeorbits;
	int nplaces;

	b = g[0];

	if (b == splitlevel)
	{
#ifdef SPLITTEST
	    ++splitcases;
	    return;
#else
	    if (res-- != 0) return;
	    res = mod - 1;
#endif
	}

	makeplaces(b);
	places = placeslist[b];
	placeorbits = placeorbitslist[b];

	for (i = 0; i < n; ++i)
	{
	    y = bit[i];

	    x = y;
	    for (j = 1; j <= b; ++j)
		if (g[j]&x) y |= g[j];

	    x = y;
	    for (j = 1; j <= b; ++j)
		if (g[j]&x) y |= g[j];

	    x = y;
	    for (j = 1; j <= b; ++j)
		if (g[j]&x) y |= g[j];

	    close[i] = y;
	}

	x1 = x2 = 0;
	for (j = 1; j <= b; ++j)
	{
	    x2 |= g[j] & x1;
	    x1 = (x1 | g[j]) & ~x2;
	}

	nfeet = 0;
	for (j = 1; j <= b; ++j)
	{
	    x = y = g[j] & x1;
	    IF2BITS(y) foot[nfeet++] = x;
	}

	nplaces = 0;

	if ((!fswitch || b < maxb-1) && maxv >= n+2)
	    for (i = 0; i < n; ++i)
	        places[nplaces++] = bit[i];

	if (nfeet <= 2 && maxv >= n+1)
	{
	    for (i = 0; i < n-1; ++i)
	    for (j = i+1; j < n; ++j)
	    {
	        if (close[i] & bit[j]) continue;

	        x = bit[i] | bit[j];
		for (t = 0; t < nfeet; ++t)
		    if ((x & foot[t]) == 0) break;
		if (t == nfeet) places[nplaces++] = x;
	    }
	}

	if (nfeet <= 3 && maxv >= n)
	{
	    for (i = 0; i < n-2; ++i)
            for (j = i+1; j < n-1; ++j)
            {
                if (close[i] & bit[j]) continue;
	        for (k = j+1; k < n; ++k)
	        {
		    if (close[k] & (bit[i]|bit[j])) continue;

                    x = bit[i] | bit[j] | bit[k];
		    for (t = 0; t < nfeet; ++t)
                        if ((x & foot[t]) == 0) break;
                    if (t == nfeet) places[nplaces++] = x;
	        }
            }
	}

	if (nplaces == 0) return;

	shell_des(places,1,nplaces);
	for (i = 0; i < nplaces; ++i)
	    placeorbits[i] = i;
	xset = places;
	nxset = nplaces;
 	xorbits = placeorbits;

	options.getcanon = FALSE;
	options.userautomproc = setorbits;

        for (i = 0; i <= b; ++i)
            gs[i] = g[i];
        shell_des(&gs[1],1,b);

	nauty((graph*)gs,lab,ptn,NULL,orbits,&options,&stats,
	      workspace,6*MAXM,1,n,NULL);

	g[0] = b+1;
	for (i = 0; i < nplaces; ++i)
	    if (placeorbits[i] == i)
	    {
	        x = places[i];
	        k = POPCOUNT(x);
	        if (k < 3) x |= bit[n];
	        if (k < 2) x |= bit[n+1];
	        g[b+1] = x;
	        process(g,n+3-k,(x^x1^x2)&~x2);
	    }
	g[0] = b;
}

/************************************************************************/
/************************************************************************/

int
main(int argc, char *argv[])
{
        char *arg,sw,*outfilename;
        boolean badargs;
        int i,j,argnum;
        design g[MAXB+1];
        double time0,time1,cputime;
	boolean qswitch,sswitch,dswitch,uswitch;
	boolean eswitch,bswitch,aswitch,vswitch;
	boolean truncwarning;

	HELP;

	fprintf(stderr,">A");
	for (i = 0; i < argc; ++i)
	    fprintf(stderr," %s",argv[i]);
	fprintf(stderr,"\n");

        nauty_check(WORDSIZE,1,MAXN,NAUTYVERSIONID);
        nautil_check(WORDSIZE,1,MAXN,NAUTYVERSIONID);
	naudesign_check(WORDSIZE,1,MAXN,NAUTYVERSIONID);

	qswitch = sswitch = dswitch = fswitch = FALSE;
	uswitch = eswitch = bswitch = aswitch = vswitch = FALSE;
        outfilename = NULL;
	minb = minv = 0;
	maxb = maxv = NOLIMIT;

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
                    else SWRANGE('s',"/",sswitch,res,mod,"greechie -s")
                    else SWRANGE('a',":-",aswitch,minv,maxv,"listg -a")
                    else SWRANGE('v',":-",vswitch,minv,maxv,"listg -v")
                    else SWRANGE('e',":-",eswitch,minb,maxb,"listg -e")
                    else SWRANGE('b',":-",bswitch,minb,maxb,"listg -b")
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

	if ((aswitch && vswitch) || (bswitch && eswitch) || (uswitch && dswitch))
	{
	    fprintf(stderr,">E -a/-v, -b/-e, and -u/-d are incompatible\n");
	    exit(1);
	}

	vswitch = (vswitch || aswitch);
	bswitch = (bswitch || eswitch);

	if (!vswitch && !bswitch)
	{
            fprintf(stderr,">E at least one of -v and -e is required\n");
            exit(1);
        }

        if (badargs)
        {
            fprintf(stderr,">E Usage: %s\n",USAGE);
            exit(1);
        }

	if (minb == -NOLIMIT) minb = 0;
	if (minv == -NOLIMIT) minv = 0;

	if (maxv <= 0 || maxb <= 0)
	{
            fprintf(stderr,">E n and b limits must be >= 0\n");
            exit(1);
	}

	if (maxb < NOLIMIT/2)
	{
	    j = 2*maxb + (!fswitch);
	    if (j < maxv) maxv = j;
	}

	if (maxv > MAXN)
	{
	    fprintf(stderr,">E Can't handle more than MAXN vertices\n");
	    fprintf(stderr,">E Continuing with -v%d assumed\n",MAXN);
	    maxv = MAXN;
	}

	if (maxb > MAXB)
	{
	    truncwarning = TRUE;
	    maxb = MAXB;
	}
	else
	    truncwarning = FALSE;

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
	    if (maxb >= 15) splitlevel = 12;
	    else            splitlevel = maxb-3;
	    if (splitlevel > maxv-12) splitlevel = maxv-12;
	    if (splitlevel < 1) splitlevel = 0;	
	}
	else 
	    splitlevel = 0;

#ifdef SPLITTEST
	splitcases = 0;
	fprintf(stderr,"Splitting level = %d blocks\n",splitlevel);
	uswitch = TRUE;
#endif

        for (i = 0; i <= MAXN; ++i)
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
                  ">E greechie: can't open %s for writing\n",outfilename);
            gt_abort("greechie");
        }

	if (dswitch)      outproc = writend;
	else if (uswitch) outproc = nullwrite;
	else              outproc = gput;

#if GIVECPUTIME
        time0 = CPUTIME;
#endif

	g[0] = 1;
	g[1] = bit[0] | bit[1] | bit[2];
	got_one(g,3,TRUE);

#if GIVECPUTIME
        time1 = CPUTIME;
	cputime = time1 - time0;
#endif

	nout = 0;
	for (i = 0; i <= MAXN; ++i)
        for (j = 0; j <= MAXB; ++j)
	{
	    if (j == MAXB && count[i][j] != 0 && truncwarning)
	    {
		fprintf(stderr,">E WARNING: maybe MAXB is insufficient\n");
		truncwarning = FALSE;
	    }
	    nout += count[i][j];
	}

	if (!qswitch)
	{
	    for (i = 0; i <= MAXN; ++i)
            for (j = 0; j <= MAXB; ++j)
	        if (count[i][j] != 0)
		    fprintf(stderr,
			"%9ld %sdiagrams with %2d vertices and %2d edges\n",
		           count[i][j],(fswitch?"foot-free ":""),i,j);
	}

#if STATS
	fprintf(stderr,"accepted %ld/%ld, %ld/%ld, %ld/%ld\n",
			accept1,ngen1,accept2,ngen2,accept3,ngen3);
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
