/* Verificarlo Tutorial: Verhulst Population Growth Model */

#include <assert.h>
#include <float.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Define real type and format string */
#ifdef DOUBLE
#define REAL double
#define FMT "%.16e %.16e"
#else
#define REAL float
#define FMT "%.7e %.7e"
#endif

REAL verhulst(REAL x);

/* Usage function to explain program arguments */
void usage() {
    fprintf(stderr, "Usage: ./verhulst <x>\n");
    fprintf(stderr, "x: initial population value\n");
    exit(EXIT_FAILURE);
}

REAL verhulst(REAL x) {
    REAL r = 4.0; 
    REAL K = 1.1; 
    REAL numer = r * x; 
    REAL denom = 1.0 + (x / K); 
    REAL result = numer / denom;
    return result;
}

/* Main function */
int main(int argc, char **argv) {
    if (argc != 2) {
        usage();
    }
    
    REAL x = atof(argv[1]);
    REAL result = verhulst(x);
    
    printf(FMT "\n", x, result);
    
    return EXIT_SUCCESS;
}