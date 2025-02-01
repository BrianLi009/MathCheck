#define WORDSIZE 64
#define MAXNV  64
#include "gtools.h"
static      DEFAULTOPTIONS_GRAPH(options);
static      statsblk(stats);
static      setword workspace[50];

#define USAGE \
"N-canrec2 [-ugs] input-file [output-file]"

#define HELPTEXT \
" :) later I'll tell you"


static void (*outproc)(FILE*, graph*, int);
#ifdef OUTPROC
extern void OUTPROC(FILE*, graph*, int);
#endif


void Getcan_Rec(graph g[MAXNV] , int n, int can[]);
int extend(graph g[MAXNV], int n);  // Add this line


static FILE     *msgfile;             /* file for input graphs */
static char     *infilename;
static FILE     *outfile;             /* file for output graphs */
static char     *outfilename;
boolean         graph6;                         /* presence of -g */
boolean         sparse6;                        /* presence of -s */
boolean         nooutput;                       /* presence of -u */

int maxn;
int count =0;
void chapg(graph[MAXNV], int);

/************************************************************************/

void
writeg6x(FILE *f, graph *g, int n)
/* write graph g with n vertices to file f in graph6 format */
{
    writeg6(f, g, 1, n);
}
/************************************************************************/

void
writes6x(FILE *f, graph *g, int n)
/* write graph g with n vertices to file f in graph6 format */
{
    writes6(f, g, 1, n);
}
/***********************************************************************/

static void
nullwrite(FILE *f, graph *g, int n)
/* don't write graph g to file f */
{
}
/***********************************************************************/

#ifdef OUTPROC1

static void write12(FILE *f, graph *g, int n)
/* pass to OUTPROC1 */
{
    OUTPROC1(f, g, n);
}

#endif
/*****************************************************************************/

/*****************************************************************************/
int main(int argc, char *argv[])
{
    int             can[MAXNV];   int codetype;
    graph           g[MAXNV],cang2[MAXNV];
    graph           *gg, *cang;
    int             n;
    int             m = 1;
    int             i, j;
    
    int         inv_can[MAXNV];
    int         argnum, sw;
    boolean     badargs, got_inf, got_outf;
    char        *arg;
    char        msg[201];
    double      t2, t1;

    
    
    HELP;
   // gtools_check(WORDSIZE,1,MAXN,NAUTYVERSIONID);  /// 1 or MAXN ???
    if( MAXN > WORDSIZE )
    {
        fprintf(stderr,"N-heir_gen: incompatible MAXN or WORDSIZE\n");
        exit(1);
    }
    
    sscanf(argv[1],"%d ",&maxn);
    printf("\nmaxn = %d\n",maxn);
    
    t1 = CPUTIME;
    
    g[0] = 0;
    n = 1;
    extend(g, n);
    
    t2 = CPUTIME;

    printf("\n The total number is: %d  , time = %f\n", count, (t2-t1));
    
    exit(0);
}





/***************************************************************/
/***************************************************************/
/***************************************************************/
int extend(graph g[MAXNV] , int n)
{
    setword     x;
    int         i, j, k;
    int             can[MAXNV];
    graph           cang2[MAXNV];
   // graph           *cang;
    int         inv_can[MAXNV];
    boolean     acc;
//printf("\n ************************************************ new acc graph %d %d \n", 1<<n, n);
    for(i=0; i < (1<<n); i++)  // i =0; i< n*2: i++
    {  //printf("\njjjjjjjjjjjjjjjj new child n=%d i=%d\n", n,i);
        x = i;
        g[n] = 0;
        while(x)
        {
            j = FIRSTBIT(x);
            x ^= bit[j];
            j = (WORDSIZE - 1) - j;   
            g[j] |= bit[n];
            g[n] |= bit[j];
        } //printf("\n ***********\n");
        Getcan_Rec(g, n+1, can); //printf("\n *********** 3\n");
        for ( j = 0; j < n+1; j++ )
        {
            // printf( "old %d is now %d\n", can[i], i);
            inv_can[can[j]] = j;
        }
        for ( k = 0; k < n+1; k++ )
        {
            // printf("\nnew %d:", i);
            x = g[can[k]];
            cang2[k] = 0;
            while(x)
            {
                j = FIRSTBIT(x);
                x ^= bit[j];
                j = inv_can[j];
                cang2[k] |= bit[j];
                //  printf(" %d,", j);
            }
        }
        
       // chapg(g, n+1);
      //  chapg(cang2, n+1);
        acc = TRUE;
        for ( j = 0; (j < n+1) && acc; j++ )
            if( g[j] != cang2[j] )   {acc = FALSE;}// printf("\n\n\nRej %d %d \n",g[j], cang2[j]); }
        if (acc &&  n+1 == maxn ) { count++; if( !(count % 10000) ) printf("\ncount = %d\n", count);}
        if(  acc   &&   n+1 < maxn  )
        {
            //printf("\n\n\naccept\n");
           // chapg(g, n+1);
            extend(g , n+1);
        }
        x = i;
        while(x)
        {
            j = FIRSTBIT(x);
            x ^= bit[j];
            j = (WORDSIZE - 1) - j;
            g[j] ^= bit[n];
        }
        
    }
    return 1;
}

/***************************************************************/

void chapg(graph g[MAXNV], int n)
{
    int i,ff,k;  setword x;
    
    for(i = 0; i < n; i++)
    {
        printf("\n %d :",i);
        x = g[i];
        while(x)
        {
            ff = FIRSTBIT(x);
            x ^= bit[ff];
            printf("%d  ",ff);
        }
    }
    printf("\nchapg done \n");
}

/***************************************************************/
/***************************************************************/
/***************************************************************/
void Getcan_Rec(graph g[MAXNV] , int n, int can[])
{
    int         lab1[MAXNV], lab2[MAXNV], inv_lab1[MAXNV], ptn[MAXNV], orbits[MAXNV];
    int         i, j, k;
    setword     st;
    graph       g2[MAXNV];
    int         m=1;
    
    
   // printf( "%d \n", count--);
    if ( n == 1 )   can[n-1] = n-1;
    else
    {
        options.writeautoms = FALSE;
        options.writemarkers = FALSE;
        options.getcanon = TRUE;
        options.defaultptn = TRUE;
        
        ran_init(1);
        nauty(g, lab1, ptn, NULL, orbits, &options, &stats, workspace, 50, m, n, g2);
        
        
        for( i=0; i< n; i++ )
            inv_lab1[lab1[i]] = i;
        for(i=0; i<= n-2; i++ )
        {
            j = lab1[i];
            st = g[j];
            g2[i] = 0;
            while(st)
            {
                k = FIRSTBIT(st);
                st ^= bit[k];
                k = inv_lab1[k];
                if( k != n-1 )
                    g2[i] |= bit[k];
            }
        }
        Getcan_Rec(g2, n-1, lab2);
        for(i=0; i <= n-2; i++)
            can[i] = lab1[ lab2 [i] ];
        can[n-1] = lab1[n-1];
    }
}
