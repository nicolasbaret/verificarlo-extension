#include <fenv.h>
#include <math.h>
#include <stdint.h>
#define TRUE 1
#define FALSE 0

double ex0(double x) {
	double r = 4.0;
	double K = 1.11;
	return (r * x) / (1.0 + (x / K));
}