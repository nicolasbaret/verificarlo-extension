// verhulst_range.c - Version that tests full range
#include <stdio.h>
#include <vfc_probes.h>

#define REAL double

REAL verhulst(REAL x) {
    REAL r = 4.0; 
    REAL K = 1.1; 
    return (r * x) / (1.0 + (x / K));
}

int main() {
    vfc_probes probes = vfc_init_probes();
    
    // Test range from -1.0 to 1.0
    for (double x = -1.0; x <= 1.0; x += 0.1) {
        REAL result = verhulst(x);
        
        char probe_name[64];
        snprintf(probe_name, sizeof(probe_name), "x_%.1f", x);
        
        // Just monitor - no threshold checking
        vfc_probe(&probes, "verhulst_range", probe_name, result);
        
        printf("%.2f %.16e\n", x, result);
    }
    
    vfc_dump_probes(&probes);
    return 0;
}