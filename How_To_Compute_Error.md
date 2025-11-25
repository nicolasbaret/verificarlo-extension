# Computing Error from Verificarlo Results

Verificarlo's VPREC and MCA backends do not output error directly. They produce raw computation results under simulated reduced precision (VPREC) or stochastic perturbations (MCA).

To obtain error metrics, you must write a separate script that:

1. Collects the output samples for each unique input - this is output in the .tab file that is created in the same directory as your c file you are running
2. Computes the mean of samples for each input (for MCA) or uses the result directly (for VPREC)
3. Compares against a high-precision reference value or known analytical solution
4. Calculates absolute error (`|computed - reference|`) and relative error (`|computed - reference| / |reference|`)

The reference value must be computed at significantly higher precision than the test precision to be meaningful (e.g., use 64-bit or arbitrary precision as reference when testing 32-bit computations).