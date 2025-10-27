#include <stdio.h>
#include <math.h>

double quadratic_naive(double a, double b, double c) {
    double discriminant = sqrt(b*b - 4*a*c);
    double x1 = (-b + discriminant) / (2*a);
    // double x2 = (-b - discriminant) / (2*a);
    return x1;  // or x2
}

int main() {
    // Example with b >> sqrt(4*a*c)
    double a = 1.0;
    double b = 2000000.0;
    double c = 1.0;
    
    printf("%.15e\n", quadratic_naive(a, b, c));
    // printf("Stable: %.15f\n", quadratic_stable(a, b, c));
    
    return 0;
}