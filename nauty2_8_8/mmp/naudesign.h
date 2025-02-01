/*  naudesign.h : header file for design version of nauty()  */
/*  Version 2.5; B. D. McKay, Apr 2010 */

#include "nauty.h"      /* which includes stdio.h */

typedef set design;
/* The internal representation used by nauty is an array of setwords,
   the first containing the number of blocks and the others containing
   the blocks in sorted order.  Sorted order is assumed for the input
   design also.  The number of points is passed in the parameter n. */

#ifdef __cplusplus
extern "C" {
#endif

extern void shell_des(design*,int,int);
extern boolean cheapautom_des(int*,int,boolean,int);
extern boolean isautom_des(graph*,int*,boolean,int,int);
extern void refine_des (graph*,int*,int*,int,int*,int*,set*,int*,int,int);
extern void refine1_des (graph*,int*,int*,int,int*,int*,set*,int*,int,int);
extern int testcanlab_des(graph*,graph*,int*,int*,int,int);
extern void updatecan_des(graph*,graph*,int*,int,int,int);
extern int targetcell_des(graph*,int*,int*,int,int,boolean,int,int,int);
extern void naudesign_check(int,int,int,int);
extern void naudesign_freedyn(void);

extern dispatchvec dispatch_design;

#ifdef __cplusplus
}
#endif

#define DEFAULTOPTIONS_DES(options) optionblk options \
    = {0,FALSE,FALSE,FALSE,TRUE,FALSE,CONSOLWIDTH,NULL,NULL,NULL, \
	NULL,NULL,NULL,NULL,0,0,1,0,&dispatch_design,FALSE,NULL}

#define DLINELEN(n,b) (3+((b)*1L*(n)+5)/6)   /* Length of d-format line */

#ifndef MAXB
#define MAXB 256  /* Only used in dio.c */
#endif
#undef MAXL
#define MAXL DLINELEN(MAXN,MAXB)    
#if MAXL < 50000
#undef MAXL
#define MAXL 50000
#endif
