// extend-atmos-date.c
// Thomas Stroman, University of Utah, 2015-06-11
/* Compilation instructions that fit within a "head" command:
gcc -c extend-atmos-date.c -I$TADSTINC
gcc -o extend-atmos-date.run extend-atmos-date.o -L$TADSTLIB -ldst2k
*/
// This single-use code is intended to modify the range of valid dates in a
// particular calibration file, so that it can be used beyond the original
// end date by date-sensitive simulation and reconstruction code.

int main() {
}
  


