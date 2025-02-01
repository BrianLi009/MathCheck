/* rangre.c : generate random Greechie diagrams */

#define USAGE \
 "rangre [-a#] [-b#] [-#:#-#] [-f] [-c] [-q] [-g#] [-n#] [outfile]"

#define HELPTEXT \
"Generate random Greechie diagrams.\n\
    outfile  is the output file (missing or \'-\' means stdout)\n\
    -f : only output diagrams with no feet (and therefore no legs)\n\
    -c : only output connected diagrams\n\
    -a# : specify the number of atoms (required)\n\
    -b# : specify the number of edges (required)\n\
         Example: -a16 -b13 .  At least one of -a or -b is required.\n\
    -n# : number of diagrams to output (default 1)\n\
    -# : permit edges of size #.  The number of them can also be given\n\
       exactly -#:# or as a range -#:#-#.  Eg. -3, -4:5, -4:3-8.  If this\n\
       option is omitted entirely, -3 is assumed.  Edge sizes not permitted\n\
       are forbidden.  NOT IMPLEMENTED  \n\
    -q : suppress informative message\n\
    -g# : set the seed of the random number generator.\n\
        The default -g0 uses the real-time clock.\n"
/*
    Author:  Brendan McKay, Feb 2001.    bdm@cs.anu.edu.au

**************************************************************************/

#define CHECK 1

/* MAXN is a bound on the number of atoms or blocks.  No limit.
   The number of atoms is also limited by atomname[].  */

#define MAXN 128

#include "gtools.h"   /* which includes stdio.h */

/*====================================================================*/

static char atomname[] = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ\
abcdefghijklmnopqrstuvwxyz!\"#$%&'()*-/:;<=>?@[\\]^_`{|}~";

/* Output is like
49B,38A,246,135,127.   (including the period)
The vertex numbers are taken from atomname[]. */

/*========================================================*/

#define GETCPUTIME 1          /* Whether to measure the cpu time or not */

#define ARG_OK 0
#define ARG_MISSING 1
#define ARG_TOOBIG 2
#define ARG_ILLEGAL 3
#define MAXARG 2000000000L
#undef NOLIMIT
#define NOLIMIT (MAXARG+1L)
#undef SWINT
#define SWINT(c,boool,val,id) if (sw==c) \
        {boool=TRUE;arg_int(&arg,&val,id);}
#undef SWRANGE
#define SWRANGE(c,sep,boool,val1,val2,id) if (sw==c) \
        {boool=TRUE;arg_range_g(&arg,sep,&val1,&val2,id);}

#define IF2BITS(ww) ww &= ww-1; if (ww && !(ww&(ww-1)))
#define IFLE2BITS(ww) ww &= ww-1; if (!(ww&(ww-1)))
#define IF1BITS(ww)  if (ww && !(ww&(ww-1)))
#define IFLE1BITS(ww)  if (!(ww&(ww-1)))

static int minblocks[MAXN+1];   /* min and max number of blocks */
static int maxblocks[MAXN+1];   /* of each size permitted */

extern int longvalue(char**,long*);

/************************************************************************/

#if 0
void
arg_int(char **ps, int *val, char *id)
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
#endif

/************************************************************************/

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

static int
ran_element(set *s, int n)
/* Choose a random element of s.  -1 if none exists */
{
	int i,j,k,m;

	i = KRAN(n); if (ISELEMENT(s,i)) return i;
	i = KRAN(n); if (ISELEMENT(s,i)) return i;
	i = KRAN(n); if (ISELEMENT(s,i)) return i;
	i = KRAN(n); if (ISELEMENT(s,i)) return i;
	i = KRAN(n); if (ISELEMENT(s,i)) return i;

	m = (n + WORDSIZE - 1) / WORDSIZE;

	i = -1;
	k = 0;
	for (j = -1; (j = nextelement(s,m,j)) >= 0; )
	{
	    ++k;
	    if (KRAN(k) == k-1) i = j;
	}

	return i;
}

/************************************************************************/

static void
gput(FILE *f, set g[][MAXM], int na, int nb)
/* write one diagram */
{
        set *gi;
	int m;
        int i,j;

	m = (na + WORDSIZE - 1) / WORDSIZE;

	for (i = 0, gi = g[0]; i < nb; ++i, gi += MAXM)
        {
	    if (i > 0) fputc(',',f);
            for (j = -1; (j = nextelement(gi,m,j)) >= 0;) fputc(atomname[j],f);
        }
        fputc('.',f);
        fputc('\n',f);
}

/************************************************************************/

static boolean
isconnected(set g[][MAXM], int na, int nb)
/* Test if g is connected, not counting isloted vertices. */
{
	int ma,mb,j,k,navail;
	boolean progress;
	set avail[MAXM],covered[MAXM];
	set *gj;

	ma = (na + WORDSIZE - 1) / WORDSIZE;
	mb = (nb + WORDSIZE - 1) / WORDSIZE;
	EMPTYSET(avail,mb);
	for (j = 1; j < nb; ++j) ADDELEMENT(avail,j);

	for (k = 0; k < ma; ++k) covered[k] = g[0][k];

	progress = TRUE;
	for (navail = nb-1; navail > 0 && progress; )
	{
	    progress = FALSE;
	    for (j = -1; (j = nextelement(avail,mb,j)) >= 0;)
	    {
		gj = g[j];
		for (k = 0; k < ma; ++k) if (gj[k] & covered[k]) break;
		if (k < ma)
		{
		    DELELEMENT(avail,j);
		    for (k = 0; k < ma; ++k) covered[k] |= gj[k];
		    progress = TRUE;
		    --navail;
		}
	    }
	}

	return navail == 0;
}

/************************************************************************/

static int
setsize_g(set *x, int m)
{
	int i,s;
	setword w;

	s = 0;
	for (i = 0; i < m; ++i)
	    if ((w = x[i]) != 0) s += POPCOUNT(w);

	return s;
}

/************************************************************************/

static void
check(set g[][MAXM], int na, int nb, boolean nofeet, boolean conn)
/* Check a diagram is 3-L-Greechie */
{
	set *g1,*g2,*g3,*g4;
	set g12[MAXM],g123[MAXM],g1234[MAXM];
	set x1[MAXM],x2[MAXM];
	int b1,b2,b3,b4;
	int i,k,m;
	setword w;
#define ERROR(s) {fprintf(stderr,">E %s\n",s); exit(1);}

	m = (na + WORDSIZE - 1) / WORDSIZE;

	/* Check sizes */
	for (b1 = 0, g1 = g[0]; b1 < nb; ++b1, g1 += MAXM)
	    if (setsize_g(g1,m) != 3) ERROR("wrong block size");
	
	/* Check for isolates */
	EMPTYSET(x1,m);
	for (b1 = 0, g1 = g[0]; b1 < nb; ++b1, g1 += MAXM)
	    for (k = 0; k < m; ++k) x1[k] |= g1[k];

	for (i = 0; i < na; ++i)
	    if (!ISELEMENT(x1,i)) ERROR("isolate");

	/* Check unions */
	for (b1 = 0, g1 = g[0]; b1 < nb-1; ++b1, g1 += MAXM)
	for (b2 = b1+1, g2 = g[b1+1]; b2 < nb; ++b2, g2 += MAXM)
	{
	    for (k = 0; k < m; ++k) g12[k] = g1[k] | g2[k];
	    if (setsize_g(g12,m) < 5) ERROR("bad pair union");

	    for (b3 = b2+1, g3 = g[b2+1]; b3 < nb; ++b3, g3 += MAXM)
	    {
	        for (k = 0; k < m; ++k) g123[k] = g12[k] | g3[k];
	        if (setsize_g(g123,m) < 7) ERROR("bad triple union");

	        for (b4 = b3+1, g4 = g[b3+1]; b4 < nb; ++b4, g4 += MAXM)
	        {
	            for (k = 0; k < m; ++k) g1234[k] = g123[k] | g4[k];
	            if (setsize_g(g1234,m) < 9) ERROR("bad quad union");
		}
	    }
	}

	/* Check connectivity */
	if (conn)
	{
	    g1 = g[0];
	    g2 = g[nb-1];
	    for (k = 0; k < m; ++k)
	    {
		w = g1[k]; g1[k] = g2[k]; g2[k] = w;
	    }

	    if (!isconnected(g,na,nb)) ERROR("not connected");

	    for (k = 0; k < m; ++k)
	    {
		w = g1[k]; g1[k] = g2[k]; g2[k] = w;
	    }
	}

	/* Check for feet */
	if (nofeet)
	{
	    EMPTYSET(x1,m);
	    EMPTYSET(x2,m);
	    for (b1 = 0, g1 = g[0]; b1 < nb; ++b1, g1 += MAXM)
		for (k = 0; k < m; ++k)
		{
		    x2[k] |= g1[k] & x1[k];
		    x1[k] = (x1[k] | g1[k]) & ~x2[k];
		}

	    for (b1 = 0, g1 = g[0]; b1 < nb; ++b1, g1 += MAXM)
	    {
		i = 0;
		for (k = -1; (k = nextelement(g1,m,k)) >= 0; )
		    if (ISELEMENT(x2,k)) ++i;
		if (i == 1) ERROR("has feet");
	    }
	}
}

/************************************************************************/

static boolean
make_rangre(set g[][MAXM], int na, int nb, boolean nofeet, boolean conn)
/* Make and write one random diagram */
{
	set far[MAXN][MAXM],allv[MAXM];
	set x[MAXM],y[MAXM];
	set *gj;
#define FAR(i,j) ISELEMENT((set*)far[i],j)
	int m,i,j,k,ne,ii;
	int v1,v2,v3;
	boolean gotit;
	int tries;
	int deg[MAXN];

	m = (na + WORDSIZE - 1) / WORDSIZE;

	EMPTYSET(allv,m);
	for (i = 0; i < na; ++i) ADDELEMENT(allv,i);

	for (ne = 0; ne < nb; )
	{
	    for (i = 0; i < na; ++i)
	    {
		EMPTYSET(y,m);
		ADDELEMENT(y,i);
		
		for (j = 0, gj = g[0]; j < ne; ++j, gj += MAXM)
		{
		    if (ISELEMENT(gj,i))
			for (k = 0; k < m; ++k) y[k] |= gj[k];
		}

		for (k = 0; k < m ; ++k) x[k] = y[k];
		
		for (j = 0, gj = g[0]; j < ne; ++j, gj += MAXM)
		{
		    for (k = 0; k < m; ++k) if (gj[k] & x[k]) break;
		    if (k < m) for (k = 0; k < m; ++k) y[k] |= gj[k];
		}

		for (k = 0; k < m ; ++k) x[k] = y[k];

		for (j = 0, gj = g[0]; j < ne; ++j, gj += MAXM)
		{
		    for (k = 0; k < m; ++k) if (gj[k] & x[k]) break;
		    if (k < m) for (k = 0; k < m; ++k) y[k] |= gj[k];
		}

		for (k = 0; k < m ; ++k) far[i][k] = allv[k] ^ y[k];
	    }

	    tries = 0;
	    gotit = FALSE;
	    do
	    {
		++tries;

		v1 = KRAN(na);
		if ((v2 = ran_element(far[v1],na)) < 0) continue;

		for (k = 0; k < m; ++k) x[k] = far[v1][k] & far[v2][k];

		if ((v3 = ran_element(x,na)) < 0) continue;

		gotit = TRUE;

		gj = g[ne];
		for (k = 0; k < m; ++k) gj[k] = 0;
		ADDELEMENT(gj,v1);
		ADDELEMENT(gj,v2);
		ADDELEMENT(gj,v3);
		++ne;
	    } while (!gotit && tries < 100);

	    if (!gotit)
	    {
		i = KRAN(ne);
		for (k = 0; k < m; ++k) g[i][k] = g[ne-1][k];
		--ne;
	    }
	}

	for (i = 0; i < na; ++i) deg[i] = 0;

	for (j = 0, gj = g[0]; j < nb; ++j, gj += MAXM)
	    for (k = -1; (k = nextelement(gj,m,k)) >= 0;) ++deg[k];

	for (i = 0; i < na; ++i)
	    if (deg[i] == 0)
	    {
		tries = 0;
		gotit = FALSE;
		do
		{
		    ++tries;
		    j = KRAN(nb);
		    if ((k = ran_element(g[j],na)) < 0 || deg[k] <= 1)
			continue;
		    gotit = TRUE;
		    DELELEMENT(g[j],k);
		    ADDELEMENT(g[j],i);
		    deg[i] = 1;
		    --deg[k];
		} while (!gotit && tries < 100);
	    }

	if (!gotit) return FALSE;

	if (nofeet)
	{
	    for (ii = 0, i = KRAN(nb); ii < nb; ++ii, i = (i == nb-1 ? 0 : i+1))
	    {
	        v2 = -1;
		for (k = -1; (k = nextelement(g[i],m,k)) >= 0; )
		    if (deg[k] == 1)  v1 = k;
		    else if (v2 >= 0) break;
		    else              v2 = k;

		if (k < 0 && v2 >= 0)
		{
		    /* this is a foot */	

		    EMPTYSET(y,m);
		
		    for (j = 0, gj = g[0]; j < nb; ++j, gj += MAXM)
		    {
		        if (ISELEMENT(gj,v2))
		            for (k = 0; k < m; ++k) y[k] |= gj[k];
		    }

		    for (k = 0; k < m ; ++k) x[k] = y[k];

		    for (j = 0, gj = g[0]; j < nb; ++j, gj += MAXM)
		    {
		        for (k = 0; k < m; ++k) if (gj[k] & x[k]) break;
		        if (k < m) for (k = 0; k < m; ++k) y[k] |= gj[k];
		    }

		    for (k = 0; k < m ; ++k) x[k] = allv[k] ^ y[k];
		    /* now x[] is far from v1 */

		    tries = 0;
		    gotit = FALSE;
		    do
		    {
			++tries;

			do {j = KRAN(nb);} while (j == i);

			v3 = ran_element(g[j],na);
			if (deg[v3] <= 2) continue;

			for (k = -1; (k = nextelement(g[j],m,k)) >= 0; )
			    if (k != v3 && !ISELEMENT(x,k)) break;
			if (k >= 0) continue;

			gotit = TRUE;
			DELELEMENT(g[j],v3);
			ADDELEMENT(g[j],v1);
			--deg[v3];
			++deg[v1];
		    } while (!gotit && tries < 100);

		    if (!gotit) return FALSE;
		}
	    }
	}

	if (conn && !isconnected(g,na,nb)) return FALSE;

	return TRUE;
}

/************************************************************************/
/************************************************************************/

int
main(int argc, char *argv[])
{
        char *arg,sw,*outfilename;
	FILE *outfile;
        boolean badargs;
        int i,j,argnum;
        double time0,time1,cputime;
	boolean qswitch,fswitch,cswitch;
	boolean bswitch,aswitch,gswitch,nswitch;
	int minblk,maxblk,blksz;
	int natoms,nblocks,nout;
	int seed;
	set g[MAXN][MAXM];

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

	qswitch = fswitch = cswitch = FALSE;
	nswitch = bswitch = aswitch = gswitch = FALSE;
        outfilename = NULL;

        argnum = 0;
        badargs = FALSE;

	for (j = 0; j <= MAXN; ++j)
	    minblocks[j] = maxblocks[j] = 0;

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
                    else SWBOOLEAN('c',cswitch)
                    else SWBOOLEAN('q',qswitch)
                    else SWINT('a',aswitch,natoms,"rangre -a")
                    else SWINT('b',bswitch,nblocks,"rangre -b")
                    else SWINT('n',nswitch,nout,"rangre -n")
                    else SWINT('g',gswitch,seed,"rangre -g")
		    else if (sw >= '0' && sw <= '9')
		    {
			--arg;
			arg_int(&arg,&blksz,"rangre -#");
			if (*arg != ':')
			{
			    minblk = 0;
			    maxblk = NOLIMIT;
			}
			else
			{
			    arg_range_g(&arg,"-",&minblk,&maxblk,"rangre -#");
			    if (minblk == -NOLIMIT) minblk = 0;
			}
			if (blksz < 2 || blksz > MAXN) badargs = TRUE;
			else
			{
			    minblocks[blksz] = minblk;
			    maxblocks[blksz] = maxblk;
			}
			fprintf(stderr,">E -%d is unimplemented\n",sw);
			badargs = TRUE;
		    }
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

	if (!aswitch || !bswitch)
	{
	    fprintf(stderr,">E -a and -b are compulsory\n");
	    exit(1);
	}

	if (natoms > MAXN || nblocks > MAXN)
	{
	    fprintf(stderr,
		    ">E at most %d atoms or blocks; increase MAXN\n",MAXN);
	    exit(1);
	}

	if (natoms > strlen(atomname))
	{
	    fprintf(stderr,">E number of atoms exceeds output limit\n");
	    exit(1);
	}

	/* decode_limits(); */

	if ((!cswitch && natoms > 3*nblocks) ||
	    (cswitch && ((fswitch && natoms > 2*nblocks) ||
			(!fswitch && natoms > 2*nblocks+1))))
	{
	    fprintf(stderr,">E -a and -b values are impossible\n");
	    exit(1);
	}

	if (gswitch && seed != 0) ran_init((long)seed);
	else                      ran_init((long)time(NULL));

	if (!nswitch) nout = 1;

     /* open output file */

        if (outfilename == NULL)
        {
            outfilename = "stdout";
            outfile = stdout;
        }
        else if ((outfile = fopen(outfilename,"w")) == NULL)
        {
            fprintf(stderr,
                  ">E rangre: can't open %s for writing\n",outfilename);
            gt_abort("rangre");
        }

#if GETCPUTIME
        time0 = CPUTIME;
#endif

	for (i = 0; i < nout; ++i)
	{
	   while (!make_rangre(g,natoms,nblocks,fswitch,cswitch)) {}
#if CHECK
	   check(g,natoms,nblocks,fswitch,cswitch);
#endif
	   gput(outfile,g,natoms,nblocks);
	}

#if GETCPUTIME
        time1 = CPUTIME;
	cputime = time1 = time0;
#else
	cputime = 0.0;
#endif
	
	if (!qswitch)
	{
            fprintf(stderr,">Z %6d diagrams written to %s in %4.2f seconds\n",
                            nout,outfilename,cputime);
	}

        return 0;
}
