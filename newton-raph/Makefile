# Default noise MCA mode: mca at 53 precision
VFC_BACKENDS=libinterflop_mca.so -m mca  --precision-binary64=53

archimedes: newton.c
	verificarlo --ddebug -O0 -g newton.c -o newton -lm

dd: newton
	rm -rf dd.line/
	VFC_BACKENDS="${VFC_BACKENDS}" vfc_ddebug ddRun ddCmp

dderrors: dd.line/rddmin-cmp/dd.line.exclude
	bash -c "vim -q <(./vfc_dderrors.py newton $<)"

clean:
	rm -rf newton dd.line *.ll *.o
