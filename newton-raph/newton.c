#include <math.h>
#include <stdio.h>
#include <time.h>

//Newton-Raphson - Iterative root finding

double newton_sqrt(double S, int N) {
    double x = S / 2.0;  /* Initial guess */
    fprintf(stderr, " i x_i\n");
    for (int i = 0; i < N; i++) {
        x = 0.5 * (x + S / x);
        fprintf(stderr, "%2d %.15e\n", i, x);
    }
    return x;
}

int main(void) {
  /* Approximate sqrt with 25 iterations */
  const int N = 25;
  double S = 9.0;
  double pi = newton_sqrt(S, N);
  printf("%.15e\n", pi);
  return 0;
}
