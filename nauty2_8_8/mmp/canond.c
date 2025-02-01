/* canond.c :  nautyd interface routines for designs
               plus a few utilities

    Author:  B. D. McKay, May 1993 and May 2001.

**************************************************************************/

#include "naudesign.h"   /* which includes nauty.h and stdio.h */

void canonise_des(design *g, int m, int n, design *h);
void fcanonise_des(design *g, int m, int n, design *h, char *fmt);
void fcanonisedstr(char *dstr, char *cdstr, char *fmt);
void canonisedstr(char *dstr, char *cdstr);
void fcanonisegrestr(char *dstr, char *cdstr, char *fmt);
void canonisegrestr(char *dstr, char *cdstr);

/* dio.c */
extern void dparams(char *dstr, int *n, int *b);
extern void dton(char *dstr, design *des);
extern void ntod(design *des, int n, char *dstr);

/* greio.c */
extern void greparams(char *dstr, int *na, int *nb);
extern void greton(char *dstr, design *des, int *n);
extern void ntogre(design *des, int b, char *dstr);

/**************************************************************************/

static void
ulsort(unsigned long *x, int k)
{
    int i,j,h;
    unsigned long iw;

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

/**************************************************************************/

void
canonise_des(design *g, int m, int n, design *h) 
 /*  canonise g; result in h */
{
    fcanonise_des(g,m,n,h,NULL);
}

/**************************************************************************/

void
fcanonise_des(design *g, int m, int n, design *h, char *fmt)
    /*  canonise g under format fmt; result in h */
{
    DYNALLSTAT(int,lab,lab_sz);
    DYNALLSTAT(int,ptn,ptn_sz);
    DYNALLSTAT(int,orbits,orbits_sz);
    DYNALLSTAT(int,count,count_sz);
    DYNALLSTAT(unsigned long,x,x_sz);
    DYNALLSTAT(design,gs,gs_sz);
    DYNALLSTAT(set,active,active_sz);
    DYNALLSTAT(setword,workspace,workspace_sz);
    int i;
    long li;
    int b,numcells,code;
    statsblk stats;
    static DEFAULTOPTIONS_DES(options);

    DYNALLOC1(int,lab,lab_sz,n,"fcanonise_des"); 
    DYNALLOC1(int,ptn,ptn_sz,n,"fcanonise_des"); 
    DYNALLOC1(set,active,active_sz,m,"fcanonise_des"); 
    DYNALLOC1(int,count,count_sz,n,"fcanonise_des"); 

    b = g[0];

    if (fmt == NULL || fmt[0] == '\0')
    {
	for (i = 0; i < n; ++i)
	{
	    lab[i] = i;
	    ptn[i] = 1;
	}
	ptn[n-1] = 0;
	numcells = 1;
	EMPTYSET(active,m);
	ADDELEMENT(active,0);
    }
    else
    {
	DYNALLOC1(unsigned long,x,x_sz,n,"fcanonise_des");

        for (i = 0; i < n && fmt[i] != '\0'; ++i)
	    x[i] = (fmt[i] << 24) | i;
	for (; i < n; ++i)
	    x[i] = ('z' << 24) | i;

        ulsort(x,n);

        EMPTYSET(active,m);
        ADDELEMENT(active,0);
        numcells = 1;

        for (i = 0; i < n; ++i)
        {
            lab[i] = x[i] & 0xffffff;
            if (i == n-1)
                ptn[i] = 0;
            else if ((x[i+1] >> 24) != (x[i] >> 24))
            {
                ++numcells;
                ADDELEMENT(active,i+1);
                ptn[i] = 0;
            }
            else
                ptn[i] = 1;
        }
    }

    if (m == 1)
        refine1_des(g,lab,ptn,0,&numcells,count,active,&code,m,n);
    else
        refine_des(g,lab,ptn,0,&numcells,count,active,&code,m,n);

    if (numcells == n)          /* discrete */
        updatecan_des(g,h,lab,0,m,n);
    else
    {
	DYNALLOC1(design,gs,gs_sz,1+m*(size_t)b,"fcanonise_des");
	DYNALLOC1(int,orbits,orbits_sz,n,"fcanonise_des");

        for (li = 0; li <= m*(size_t)b; ++li) gs[li] = g[li];
        shell_des(&gs[1],m,b);

        options.getcanon = TRUE;
        options.defaultptn = FALSE;
        options.tc_level = 0;

        EMPTYSET(active,m);
	DYNALLOC1(setword,workspace,workspace_sz,10*m,"fcanonise_des");
        nauty(gs,lab,ptn,active,orbits,&options,&stats,workspace,10*m,m,n,h);
    }
}

/**************************************************************************/

void
canonise2(design *g, int n, design *h)     /*  canonise g; result in h */
       /* case of half design with complementary property */
{
    int lab[WORDSIZE],ptn[WORDSIZE],orbits[WORDSIZE];
    design gs[1+MAXB],hs[1+MAXB];
    int count[WORDSIZE];
    int i,j;
    int b,numcells,code;
    set active[1];
    statsblk stats;
    static DEFAULTOPTIONS_DES(options);
    setword all,workspace[50];

    if (n > WORDSIZE || g[0] > MAXB)
    {
	fprintf(stderr,">E canonise2: n or b is too big (fix the code!)\n");
	exit(1);
    }
    all = 0;
    for (i = 0; i < n; ++i) all |= bit[i];

    b = g[0];
    gs[0] = b+b;
    for (i = 1; i <= b; ++i)
    {
        gs[i] = g[i];
        gs[i+b] = all ^ g[i];
    }
    shell_des(&gs[1],1,b+b);

    for (i = 0; i < n; ++i)
    {
        lab[i] = i;
        ptn[i] = 1;
    }
    ptn[n-1] = 0;
    numcells = 1;
    EMPTYSET(active,1);

    ADDELEMENT(active,0);

    refine_des(gs,lab,ptn,0,&numcells,count,active,&code,1,n);

    if (numcells == n)          /* discrete */
    {
        for (i = 0; i < n; ++i)
            count[i] = lab[i];
        updatecan_des(gs,hs,count,0,1,n);
    }
    else
    {
        options.getcanon = TRUE;
        options.defaultptn = FALSE;
        options.tc_level = 0;

        EMPTYSET(active,1);
        nauty(gs,lab,ptn,active,orbits,&options,&stats,
               workspace,50,1,n,hs);
    }

    h[0] = b;
    j = 1;
    for (i = 1; i <= b+b; ++i)
        if ((hs[i] & bit[0]) == 0) h[j++] = hs[i];
}

/**************************************************************************/

void
canonisedstr(char *dstr, char *cdstr)
{
    fcanonisedstr(dstr,cdstr,NULL);
}

/**************************************************************************/

void
fcanonisedstr(char *dstr, char *cdstr, char *fmt)
{
    int m,n,b;
    DYNALLSTAT(design,g,g_sz);
    DYNALLSTAT(design,h,h_sz);

    dparams(dstr,&n,&b);
    m = SETWORDSNEEDED(n);

    DYNALLOC1(design,g,g_sz,1+m*(size_t)n,"fcanonisedstr");
    DYNALLOC1(design,h,h_sz,1+m*(size_t)n,"fcanonisedstr");

    dton(dstr,g);

    fcanonise_des(g,m,n,h,fmt);
    ntod(h,n,cdstr);
}

/**************************************************************************/

void
canonisegrestr(char *dstr, char *cdstr)
{
    fcanonisegrestr(dstr,cdstr,NULL);
}

/**************************************************************************/

void
fcanonisegrestr(char *dstr, char *cdstr, char *fmt)
{
    int m,n,b;
    DYNALLSTAT(design,g,g_sz);
    DYNALLSTAT(design,h,h_sz);

    greparams(dstr,&n,&b);
    m = SETWORDSNEEDED(b);

    DYNALLOC1(design,g,g_sz,1+m*(size_t)n,"fcanonisedstr");
    DYNALLOC1(design,h,h_sz,1+m*(size_t)n,"fcanonisedstr");

    greton(dstr,g,&n);  /* Note: makes dual design */

    fcanonise_des(g,m,n,h,fmt);
    ntogre(h,n,cdstr);
}

/**************************************************************************/

boolean
checkdes(design *des, int n, int k, int r, int lambda)
             /* check design: m=1 assumed k is upper bound only */
{
    int i,j,t,b,l;
    setword w;

    b = des[0];
    for (t = 1; t <= b; ++t)
        if (POPCOUNT(des[t]) > k)
        {
            fprintf(stderr,
               ">E check: k error; des[%d]=0x%llx; k=%d\n",
	          t,(unsigned long long)des[t],k);
            return FALSE;
        }

    for (i = 0; i < n; ++i)
    {
        l = 0;
        w = bit[i];
        for (t = 1; t <= b; ++t)
            if (w & des[t]) ++l;
        if (l != r)
        {
            fprintf(stderr,">E check: r error\n");
            return FALSE;
        }
    }

    for (i = 0; i < n-1; ++i)
    for (j = i+1; j < n; ++j)
    {
        l = 0;
        w = bit[i] | bit[j];
        for (t = 1; t <= b; ++t)
            if ((w & des[t]) == w) ++l;
        if (l != lambda)
        {
            fprintf(stderr,">E check: lambda error\n");
            return FALSE;
        }
    }

    return TRUE;
}
