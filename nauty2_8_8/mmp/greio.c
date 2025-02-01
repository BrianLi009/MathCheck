/* i/o routines for greeche format files */

#include "gtools.h"
#include "naudesign.h"

// #include <errno.h>

static char atomname[] = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ\
abcdefghijklmnopqrstuvwxyz!\"#$%&'()*-/:;<=>?@[\\]^_`{|}~";
static int numatomnames;  /* number of names in atomname[] */

static boolean init = FALSE;
static int name2atom[256];

#define MAXATOMS 3200
#define MAXATOMWORDS SETWORDSNEEDED(MAXATOMS)
static set atommask[MAXATOMWORDS];
static int maxatomname;  /* highest atom name seen in input */

/************************************************************************/

static void
doinit(void)
{
    int i;

    for (i = 0; i < 256; ++i) name2atom[i] = -1;

    for (i = 0; atomname[i] != '\0'; ++i) name2atom[atomname[i]] = i;

    numatomnames = strlen(atomname);

    init = TRUE;
}

/************************************************************************/

void
greparams(char *dstr, int *na, int *nb)
/* count atoms and blocks in greechie string */
{
    int j,a,b,base;
    char *s;

    if (!init) doinit();

    EMPTYSET(atommask,MAXATOMWORDS);

    a = 0;
    b = 1;
    maxatomname = -1;

    for (s = dstr; *s != '.' && *s != '\n' && *s != '\0'; ++s)
    {
        if (*s == ',')
        {
            ++b;
        }
        else
        {
	    base = 0;
	    while (*s == '+') { base += numatomnames; ++s; }

            j = name2atom[*s];
            if (j < 0)
            {
                fprintf(stderr,">E greparams: unknown character 0X%2x\n",*s);
                exit(1);
            }

            j += base;
	    if (j >= MAXATOMS)
	    {
		fprintf(stderr,"Increase MAXATOMS in greio.c\n");
		exit(1);
	    }

	    if (!ISELEMENT(atommask,j))
	    {
		++a;
		ADDELEMENT(atommask,j);
		if (j > maxatomname) maxatomname = j;
	    }
        }
    }

    *na = a;
    *nb = b;
}

/************************************************************************/

void
greton(char *dstr, design *des, int *n)
/* convert string in greechie format to dual design */
{
    int i,j,b,nb,na,m,base;
    char *s;
    set *blk;
    DYNALLSTAT(int,newname,newname_sz);

    if (!init) doinit();
    greparams(dstr,&na,&nb);

    *n = nb;
    m = SETWORDSNEEDED(nb);
    des[0] = na;
    ++des;

    DYNALLOC1(int,newname,newname_sz,maxatomname+2,"greton");
    j = -1;
    for (i = 0; i < na; ++i)
    {
	j = nextelement(atommask,MAXATOMWORDS,j);
	newname[j] = i;
    }
    EMPTYSET(des,m*(size_t)na);

    b = 0;

    for (s = dstr; *s != '.' && *s != '\n' && *s != '\0'; ++s)
    {
        if (*s == ',')
            ++b;
        else
        {
	    base = 0;
	    while (*s == '+') { base += numatomnames; ++s; }
            j = newname[base+name2atom[*s]];
	    blk = des + j*(size_t)m;
	    ADDELEMENT(blk,b);
        }
    }
}

/************************************************************************/

graph*
gretograph_vb(char *dstr, int *pm, int *pna, int *pnb)
/* convert greechie string to nauty graph, vertices first */
{
    int v,b;
    int na,nb,m,n;
    char *s;
    graph *g;

    greparams(dstr,&na,&nb);
    n = na + nb;
    m = (n + WORDSIZE - 1)/WORDSIZE;
    *pm = m;
    *pna = na;
    *pnb = nb;

    if ((g = (graph*)ALLOCS(n,sizeof(graph)*m)) == NULL)
    {
        fprintf(stderr,"gretograph_vb: malloc failed\n");
        exit(1);
    }
    EMPTYSET(g,m*(size_t)n);

    b = na;

    for (s = dstr; *s != '.' && *s != '\n' && *s != '\0'; ++s)
    {
        if (*s == ',')
            ++b;
        else
        {
            v = name2atom[*s];
            ADDELEMENT(g+v*m,b);
            ADDELEMENT(g+b*m,v);
        }
    }

    return g;
}

/************************************************************************/

graph*
gretograph_bv(char *dstr, int *pm, int *pna, int *pnb)
/* convert greechie string to nauty graph, blocks first */
{
    int v,b;
    int na,nb,m,n;
    char *s;
    graph *g;

    greparams(dstr,&na,&nb);
    n = na + nb;
    m = (n + WORDSIZE - 1)/WORDSIZE;
    *pm = m;
    *pna = na;
    *pnb = nb;

    if ((g = (graph*)ALLOCS(n,sizeof(graph)*m)) == NULL)
    {
        fprintf(stderr,"gretograph_bv: malloc failed\n");
        exit(1);
    }
    EMPTYSET(g,m*(size_t)n);

    b = 0;

    for (s = dstr; *s != '.' && *s != '\n' && *s != '\0'; ++s)
    {
        if (*s == ',')
            ++b;
        else
        {
            v = nb + name2atom[*s];
            ADDELEMENT(g+v*m,b);
            ADDELEMENT(g+b*m,v);
        }
    }

    return g;
}

/**************************************************************************/

void
ntogre(design *des, int b, char *dstr) 
/* convert dual design to greechie string, \n and \0 terminated */
{
    int i,j,k;
    int m,n;
    char *s;
    setword biti;
    set *des0,*desi,*desn;

    n = des[0];
    s = dstr;

    m = SETWORDSNEEDED(b);
    des0 = des+1;
    desn = des0 + n*(size_t)m;

    for (j = 0; j < b; ++j)
    {
	if (j > 0) *(s++) = ',';
        for (i = 0, desi = des0; i < n; ++i, desi += m)
	{
	    if (ISELEMENT(desi,j))
	    {
		k = i;
		while (k >= numatomnames)
		{
		    *(s++) = '+';
		    k -= numatomnames;
		}
		*(s++) = atomname[k];
	    }
	}
    }
    *(s++) = '.';
    *(s++) = '\n';
    *s = '\0';
}

/**************************************************************************/

char*
gre_getline(FILE *f)     /* read a line with error checking */
/* includes \n (if present) and \0.  Immediate EOF causes NULL return. */
{
    DYNALLSTAT(char,s,s_sz);
    int c;
    long i;

    DYNALLOC1(char,s,s_sz,5000,"gre_getline");

    FLOCKFILE(f);
    i = 0;
    while ((c = GETC(f)) != EOF && c != '\n')
    {
        if (i == s_sz-3)
            DYNREALLOC(char,s,s_sz,3*(s_sz/2)+10000,"gre_getline");
        s[i++] = c;
    }
    FUNLOCKFILE(f);

    if (i == 0 && c == EOF) return NULL;

    if (c == '\n') s[i++] = '\n';
    s[i] = '\0';
    return s;
}

/**************************************************************************/

boolean
readgrestr(FILE *f, char *dstr)  /* read from greechie format file into string */
                             /* return TRUE for success, FALSE for eof */
                             /* dstr[] must have at least MAXL+2 bytes */
{
    int i,n;
    int b,dlen;

    if (fgets(dstr,1+MAXL,f) == NULL)
    {
        if (feof(f))
            return FALSE;
        else
        {
            fprintf(stderr,
                    ">E readgrestr: error in reading from input file\n");
            gt_abort(">E readgrestr");
        }
    }

    if (dstr[0] == '\0')
    {
        fprintf(stderr,">E readgrestr: empty line read\n");
        gt_abort(">E readgrestr");
    }

    return TRUE;
}
