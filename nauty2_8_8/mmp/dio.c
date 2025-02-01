/* i/o routines for d format files */

#undef MAXN
#define MAXN WORDSIZE
#include "naudesign.h"

#include <errno.h>
#define ABORT(msg) {if (errno != 0) perror(msg); exit(2);}

static char xbit[] = {32,16,8,4,2,1};
#define BIAS ((char)63)

#undef MAXB
#define MAXB 4095

/****************************************************************************
*
*  Description of d-format
*
*  Let D = (d[0],d[1],...,d[b-1]) be a sequence of subsets of {0,1,...,n-1}.
*  A record consists of 3 + ceiling(n*b/6) bytes, plus one '\n'.  Apart
*  from the '\n', each byte contains the unsigned value 077 + x, where x
*  is a number in the range 0..077 (i.e. a 6-bit unsigned number).
*  In the following we will assume the bias 077 has been removed.
*
*  byte    0:  n                                (0 <= n <= 63)
*  bytes 1-2:  b = 64*byte1 + byte2             (0 <= b <= 4095)
*  bytes 3- :  Consider the bit stream u[0] u[1] ..., where
*              u[b*i+b-1-j] = 1 if and only if j is an element of d[i]
*              (0 <= i < n, 0 <= j < b), and u[t] = 0 if t >= n*b.
*              For 0 <= k < ceiling(n*b/6), byte 3+k (without the bias)
*              contains 32*u[6*k] + 16*u[6*k+1] + ... + u[6*k+5].
*
* This file assumes that n <= MAXN <= WORDSIZE and b <= MAXB <= 4095.
*
*****************************************************************************/

void
dparams(char *dstr, int *n, int *b)
/* get vertices and blocks in d-format string */
{
	*n = dstr[0] - BIAS;
	*b = ((int)(dstr[1] - BIAS) << 6) + (dstr[2] - BIAS);
}

/****************************************************************************/

void                    /* convert string in d format to design */
dton(char *dstr, design *des)
{
        int i,k,y,n;
        setword dj;
        int j,b;

        n = dstr[0] - BIAS;
        if (n > WORDSIZE)
        {
            fprintf(stderr,">E n too large for dton\n");
            exit(2);
        }

        b = ((int)(dstr[1] - BIAS) << 6) + (dstr[2] - BIAS);
        if (b > MAXB)
        {
            fprintf(stderr,">E b too large for dton\n");
            exit(2);
        }

        des[0] = b;

        dstr += 2;

        k = 5;
        for (j = 1; j <= b; ++j)
        {
            dj = 0;
            for (i = n; --i >= 0;)
            {
                if (++k == 6)
                {
                    k = 0;
                    y = *(++dstr) - BIAS;
                }
                if (y & xbit[k]) dj |= bit[i];
            }
            des[j] = dj;
        }
}

/**************************************************************************/

void ntod(design *des, int n, char *dstr)   /* convert design to d-string,   */
            /*  \n and \0 terminated */
{
        int i,j,k;
        int b;
        char y;

        b = des[0];
        if (n > WORDSIZE || b > MAXB)
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
            if (des[j] & bit[i]) y |= xbit[k];
        }
        if (n > 0 && b > 0) *(dstr++) = y + BIAS;
        *(dstr++) = '\n';
        *dstr = '\0';
}

/**************************************************************************/

boolean
readdstr(FILE *f, char *dstr)        /* read from d-format file into string */
                /* return TRUE for success, FALSE for eof */
             /* dstr[] must have at least MAXL+2 bytes */
{
        char *fgets();
        int i,n;
        int b,dlen;

        for (i = 0; i < 2+MAXL; ++i)
            dstr[i] = '\0';

        if (fgets(dstr,1+MAXL,f) == NULL)
        {
            if (feof(f))
                return FALSE;
            else
            {
                fprintf(stderr,">E readd: error in reading from input file\n");
                ABORT(">E readd");
            }
        }

        if (dstr[0] == '\0')
        {
            fprintf(stderr,">E readd: empty line read\n");
            ABORT(">E readd");
        }

        n = dstr[0] - BIAS;
        b = ((int)(dstr[1] - BIAS) << 6) + dstr[2] - BIAS;
        if (n > MAXN || b > MAXB)
        {
            fprintf(stderr,">E n or b too large for readd\n");
            ABORT(">E readd");
        }

        dlen = 3 + (n*b + 5)/6;
        if (dstr[dlen] != '\n')
        {
            fprintf(stderr,">E readd: line of bad length read\n");
            ABORT(">E readd");
        }

        for (i = 0; i < dlen; ++i)
            if (dstr[i] < BIAS || dstr[i] > BIAS + 63)
            {
                fprintf(stderr,">E readd: bad input character read\n");
                ABORT(">E readn");
            }

        return TRUE;
}

/**************************************************************************/

boolean
readd(FILE *f, design *des, int *np)
        /* read from d-format file into design format */
        /* return TRUE for success, FALSE for eof */
{
        char dstr[MAXL+3];

        if (!readdstr(f,dstr)) return FALSE;

        dton(dstr,des);
        *np = dstr[0] - BIAS;;

        return TRUE;
}

/*************************************************************************/

void
writed(FILE *f, char *dstr)
                /* write d format string to file */
{
        if (fputs(dstr,f) == EOF || ferror(f))
        {
            fprintf(stderr,">E writed : error on writing file\n");
            ABORT(">E writed");
        }
}

/*************************************************************************/

void
writend(FILE *f, design *des, int n)    /* write design to file in d format */
{
        char dstr[MAXL+3];

        ntod(des,n,dstr);
        writed(f,dstr);
}
