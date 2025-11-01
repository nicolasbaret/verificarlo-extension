# Default noise MCA mode: mca at 53 precision
VFC_BACKENDS=libinterflop_mca.so -m mca  --precision-binary64=53

quadratic: quadratic.c
	verificarlo --ddebug -O0 -g quadratic.c -o quadratic -lm

dd: quadratic
	rm -rf dd.line/
	VFC_BACKENDS="${VFC_BACKENDS}" vfc_ddebug ddRun ddCmp

dderrors: dd.line/rddmin-cmp/dd.line.exclude
	bash -c "vim -q <(./vfc_dderrors.py quadratic $<)"

clean:
	rm -rf quadratic dd.line *.ll *.o
