/* shortd.c : remove duplicates from a design file in d or greechie format */

#define USAGE \
 "shortd [-q] [-s] [-v] [-k] [-G] [-fxxx] [-Txxx] [infile [outfile]]"

#define HELPTEXT \
"Remove duplicates from a design file in d or greechie format\n\
\n\
   infile is the name of the input file in d or greechie format\n\
   outfile is the name of the output file in the same format\n\
\n\
   if outfile is omitted, it is taken to be the same as infile\n\
   if both infile and outfile are omitted, input will be taken\n\
           from stdin and written to stdout\n\
\n\
   Optional switches:\n\
\n\
   -k  output designs have the same labelling as the input\n\
       designs (canonical labelling only occurs internally)\n\
\n\
   -q  suppresses the statistical information normally\n\
       written to stderr at completion\n\
\n\
   -s  suppresses the canonical labelling, so that only\n\
       a sort is performed (i.e. assume already labelled)\n\
\n\
   -v  write to stderr a list of which input designs correspond to which\n\
       output designs.\n\
       The input and output designs are both numbered beginning at 1.\n\
       A line like\n\
          23 : 30 154 78\n\
       means that inputs 30, 154 and 78 were isomorphic, and produced output 23.\n\
\n\
   -G  use Greechie ascii format instead of d-format\n\
       isolated atoms are removed from the input\n\
\n\
   -fxxx  Specify a partition of the point set.  \"xxx\" is any\n\
       string of ASCII characters except nul.  This string is\n\
       considered extended to infinity on the right with the\n\
       character 'z'.  One character is associated with each point,\n\
       in the order given.  The labelling used obeys these rules:\n\
        (1) the new order of the points is such that the associated\n\
       characters are in ASCII ascending order\n\
        (2) if two designs are labelled using the same string xxx,\n\
       the output designs are identical iff there is an\n\
       associated-character-preserving isomorphism between them.\n\
       With -G, operates on the block set.\n\
\n\
   -Txxx  Specify a directory for the sort subprocess to use for\n\
       temporary files.  The default is the current directory.\n"

/*
    Author:  B. D. McKay, May-Sep 1993, May 2001, Apr 2010, Jun 2016, Sep 2022

**************************************************************************/

#include "gtools.h"
#include "naudesign.h"           /* which includes nauty.h and stdio.h */
#include <signal.h>

/* Old sort parameters, only use if necessary:
#define SORTCOMMAND  SORTPROG,SORTPROG,"-T",tempdir,"-u","+0","-1"
#define VSORTCOMMAND1  SORTPROG,SORTPROG,"-T",tempdir
#define VSORTCOMMAND2  SORTPROG,SORTPROG,"-T",tempdir,"+0","-1","+2"
*/

#define SORTCOMMAND  SORTPROG,SORTPROG,"-T",tempdir,"-u","-k","1,1"
#define VSORTCOMMAND1  SORTPROG,SORTPROG,"-T",tempdir
#define VSORTCOMMAND2  SORTPROG,SORTPROG,"-T",tempdir,"-k","1,1","-k","3"

static char *tempdir;

void writed(FILE *f, char *dstr);
boolean readd(FILE *f, design *des, int *np);
void canonise_des(design *g, int m, int n, design *h);
void fcanonise_des(design *g, int m, int n, design *h, char *fmt);
void fcanonisedstr(char *dstr, char *cdstr, char *fmt);
void canonisedstr(char *dstr, char *cdstr);
void fcanonisegrestr(char *dstr, char *cdstr, char *fmt);
void canonisegrestr(char *dstr, char *cdstr);

/**************************************************************************/

static int  
beginsort(FILE **sortin, FILE **sortout, boolean vswitch, boolean keep) 
 /* begin sort process and return its pid */
 /* and open streams for i/o to it        */
{
    int pid;
    int inpipe[2],outpipe[2];

    if (pipe(inpipe) < 0 || pipe(outpipe) < 0)
    {
        fprintf(stderr,">E shortd: can't create pipes to sort process\n");
        gt_abort(">E shortd");
    }

    if ((pid = fork()) < 0)
    {
        fprintf(stderr,">E shortd: can't fork\n");
        gt_abort(">E shortd");
    }

    if (pid > 0)            /* parent */
    {
        close(inpipe[0]);
        close(outpipe[1]);
        if ((*sortin = fdopen(inpipe[1],"w")) == NULL)
        {
            fprintf(stderr,">E shortd: can't open stream to sort process\n");
            gt_abort(">E shortd");
        }
        if ((*sortout = fdopen(outpipe[0],"r")) == NULL)
        {
            fprintf(stderr,">E shortd: can't open stream from sort process\n");
            gt_abort(">E shortd");
        }
    }
    else                   /* child */
    {
	SET_C_COLLATION;

        close(inpipe[1]);
        close(outpipe[0]);
        if (dup2(inpipe[0],0) < 0 || dup2(outpipe[1],1) < 0)
        {
            fprintf(stderr,">E shortd: dup2 failed\n");
            gt_abort(">E shortd");
        }

        if (vswitch)
            if (keep)
                execlp(VSORTCOMMAND2,(char*)NULL);
            else
                execlp(VSORTCOMMAND1,(char*)NULL);
        else
            execlp(SORTCOMMAND,(char*)NULL);
        fprintf(stderr,">E shortd: can't start sort process\n");
        gt_abort(">E shortd");
    }

    return pid;
}

/**************************************************************************/

static void
tosort(FILE *f, char *cdstr, char *dstr, long index)   
   /* write one design to sort process */
            /* cdstr = canonical d-string */
           /* dstr = optional original d-string */
          /* index = optional index number */
{
    int i,j;
    char buff[2*MAXL+20];

    j = 0;
    for (i = 0; cdstr[i] != '\n';++i) buff[j++] = cdstr[i];

    if (dstr != NULL)
    {
        buff[j++] = ' ';
        for (i = 0; dstr[i] != '\n';++i) buff[j++] = dstr[i];
    }

    if (index > 0)
    {
        buff[j++] = '\t';
        sprintf(&buff[j],"%08ld",index);
        j += 8;
    }

    buff[j++] = '\n';
    buff[j] = '\0';

    fputs(buff,f);
    if (ferror(f))
    {
        fprintf(stderr,">E shortd: error writing to sort process\n");
        gt_abort(">E shortd");
    }
}

/**************************************************************************/

static boolean              /* read one design from sort process */
fromsort(FILE *f, char *cdstr, char *dstr, long *index)
{
    int i,j;
    char buff[2*MAXL+21];
    char *fgets();

    buff[2*MAXL+20] = '\n';
    if (fgets(buff,2*MAXL+20,f) == NULL)
    {
        if (feof(f))
            return FALSE;
        else
        {
            fprintf(stderr,">E shortd: error in reading from sort process\n");
            gt_abort(">E shortd");
        }
    }

    for (j = 0; buff[j] != ' ' && buff[j] != '\t' && buff[j] != '\n'; ++j)
        cdstr[j] = buff[j];

    cdstr[j] = '\n';
    cdstr[j+1] = '\0';

    if (buff[j] == ' ')
    {
        i = 0;
        for (++j;buff[j] != '\t' && buff[j] != '\n'; ++j)
            dstr[i++] = buff[j];
        dstr[i] = '\n';
        dstr[i+1] = '\0';
    }
    else
        dstr[0] = '\0';

    if (buff[j] == '\t')
    {
        if (sscanf(&buff[j+1],"%ld",index) != 1)
        {
            fprintf(stderr,">E shortd: index field corrupted\n");
            gt_abort(">E shortd");
        }
    }
    else
        *index = 0;

    return TRUE;
}

/**************************************************************************/

int
main(int argc, char *argv[])
{
    char *infilename,*outfilename;
    FILE *infile,*outfile;
    FILE *sortin,*sortout;
    int status;
    char dstr[MAXL+2],cdstr[MAXL+2],prevstr[MAXL+2];
    char *fmt;
    boolean greechie,quiet,sortonly,vswitch,keep,format;
    long numread,numwritten;
    int i,j,namesgot,line;
    int sortpid;
    char *arg;
    boolean (*readproc)();
    boolean readdstr(),readgrestr();

    HELP;
 
    fprintf(stderr,">A");
    for (i = 0; i < argc; ++i)
        fprintf(stderr," %s",argv[i]);
    fprintf(stderr,"\n");

    nauty_check(WORDSIZE,1,MAXN,NAUTYVERSIONID);
    nautil_check(WORDSIZE,1,MAXN,NAUTYVERSIONID);
    naudesign_check(WORDSIZE,1,MAXN,NAUTYVERSIONID);

    infilename = outfilename = NULL;
    format = quiet = sortonly = vswitch = keep = FALSE;
    greechie = FALSE;
    tempdir = ".";

     /* parse argument list */

    namesgot = 0;
    for (i = 1; i < argc; ++i)
    {
        arg = argv[i];
        if (arg[0] == '-' && arg[1] != '\0')
        {
            if (arg[1] == 's')
                sortonly = TRUE;
            else if (arg[1] == 'q')
                quiet = TRUE;
            else if (arg[1] == 'v')
                vswitch = TRUE;
            else if (arg[1] == 'k')
                keep = TRUE;
            else if (arg[1] == 'G')
                greechie = TRUE;
            else if (arg[1] == 'f')
            {
                format = TRUE;
                fmt = arg+2;
            }
            else if (arg[1] == 'T')
                tempdir = arg+2;
            else
            {
                fprintf(stderr,USAGE);
                exit(2);
            }
        }
        else
        {
            if (namesgot == 0)
            {
                namesgot = 1;
                infilename = arg;
            }
            else if (namesgot == 1)
            {
                namesgot = 2;
                outfilename = arg;
            }
            else
            {
                fprintf(stderr,USAGE);
                exit(2);
            }
        }
    }

    if (namesgot == 1) outfilename = infilename;

     /* open input file */

    if (infilename == NULL || infilename[0] == '-')
    {
        infile = stdin;
        infilename = "stdin";
    }
    else if ((infile = fopen(infilename,"r")) == NULL)
    {
        fprintf(stderr,">E shortd: can't open %s for reading\n",infilename);
        gt_abort(">E shortd");
    }

    if (greechie) readproc = readgrestr;
    else          readproc = readdstr;

    signal(SIGPIPE,SIG_IGN);        /* process pipe errors ourselves */

     /* begin sort in a subprocess */

    sortpid = beginsort(&sortin,&sortout,vswitch,keep);

     /* feed input designs, possibly relabelled, to sort process */

    numread = 0;
    while ((*readproc)(infile,dstr))
    {
        ++numread;
        if (sortonly) strcpy(cdstr,dstr);
        else if (greechie)
        {
            if (format) fcanonisegrestr(dstr,cdstr,fmt);
            else        canonisegrestr(dstr,cdstr);
        }
        else
        {
            if (format) fcanonisedstr(dstr,cdstr,fmt);
            else        canonisedstr(dstr,cdstr);
        }

        tosort(sortin,cdstr,keep ? dstr : NULL,vswitch ? numread : 0);
    }
    fclose(sortin);
    fclose(infile);

     /* open output file */

    if (outfilename == NULL || outfilename[0] == '-')
    {
        outfile = stdout;
        outfilename = "stdout";
    }
    else
    {
        if ((outfile = fopen(outfilename,"w")) == NULL)
        {
            fprintf(stderr,
                ">E shortd: can't open %s for writing\n",outfilename);
            gt_abort(">E shortd");
        }
    }

    if (!quiet)
        fprintf(stderr,
                "%6ld designs read from %s\n",numread,infilename);

     /* collect output from sort process and write to output file */

    numwritten = 0;
    if (vswitch)
    {
        while (fromsort(sortout,cdstr,dstr,&numread))
        {
            if (numwritten == 0 || strcmp(cdstr,prevstr) != 0)
            {
                ++numwritten;
                writed(outfile,keep ? dstr : cdstr);
                fprintf(stderr,"\n");
                fprintf(stderr,"%3ld : %3ld",numwritten,numread);
                line = 1;
            }
            else
            {
                if (line == 15)
                {
                    line = 0;
                    fprintf(stderr,"\n     ");
                }
                fprintf(stderr," %3ld",numread);
                ++line;
            }
            strcpy(prevstr,cdstr);
        }
        fprintf(stderr,"\n\n");
    }
    else
    {
        while (fromsort(sortout,cdstr,dstr,&numread))
        {
            ++numwritten;
            writed(outfile,keep ? dstr : cdstr);
        }
    }

    fclose(sortout);
    fclose(outfile);

    if (!quiet)
        fprintf(stderr,
                "%6ld designs written to %s\n",numwritten,outfilename);

     /* check that the subprocess exitted properly */

    while (wait(&status) != sortpid) {}
    
#ifdef WIFSIGNALED
    if (WIFSIGNALED(status) && WTERMSIG(status) != 0)
#else
    if (WTERMSIG(status) != 0)
#endif
    {
        fprintf(stderr,">E shortg: sort process killed (signal %d)\n",
                      WTERMSIG(status)); 
        gt_abort(">E shortd");
    }   
    else if (WEXITSTATUS(status) != 0)
    {
        fprintf(stderr,
                ">E shortg: sort process exited abnormally (code %d)\n",
                WEXITSTATUS(status));
        gt_abort(">E shortd");
    }

    exit(0);
}
