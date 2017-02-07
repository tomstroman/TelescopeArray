/* precess.c
 * Thomas Stroman, University of Utah, 2017-02-06
 * syntax for compiling:
gcc -c precess.c
gcc -o precess.run precess.o -static -lnova -lm
 * Given J2000 equatorial coordinates, find the coordinates 
 * based on the equinox of an arbitrary date (much like what Stellarium
 * reports) for use with star.c ray-tracing code.
 */

#include <stdlib.h>
#include <stdio.h>
#include <math.h>

#include <libnova/transform.h>
#include <libnova/julian_day.h>
#include <libnova/utility.h>

int main(int argc, char *argv[]) {
  if (argc != 13) {
    fprintf(stderr, "Usage:\n\n");
    fprintf(stderr, "%s YYYY MM DD hh mm ss.s raH raM raS.S [-]decD decM decS.S\n", argv[0]);
    fprintf(stderr, "     where time is UTC and equatorial coordinates are J2000.0\n");
    return -1;
  }
  struct ln_date date; // UTC date of observation start
  struct lnh_equ_posn cj2k; // J2000.0 coordinates of star
  struct ln_equ_posn object, precessed_object;
  struct lnh_equ_posn cnow; // coordinates in current epoch
  int signed_deg;
  double JD;
  double from_JD = 2451545.0;
  date.years = atoi(argv[1]);
  date.months = atoi(argv[2]);
  date.days = atoi(argv[3]);
  date.hours = atoi(argv[4]);
  date.minutes = atoi(argv[5]);
  date.seconds = atof(argv[6]);
  
  cj2k.ra.hours = atoi(argv[7]);
  cj2k.ra.minutes = atoi(argv[8]);
  cj2k.ra.seconds = atof(argv[9]);
  
  signed_deg = atoi(argv[10]);
  cj2k.dec.neg = (signed_deg < 0);
  cj2k.dec.degrees = abs(signed_deg);
  cj2k.dec.minutes = atoi(argv[11]);
  cj2k.dec.seconds = atof(argv[12]);
  
  
  JD = ln_get_julian_day(&date);
  ln_hequ_to_equ(&cj2k, &object);
//   printf("Julian date: %f\n", JD);
//   printf("ra %f, dec %f\n", object.ra, object.dec);
  ln_get_equ_prec2(&object, from_JD, JD, &precessed_object);
//   printf("ra %f, dec %f\n", precessed_object.ra, precessed_object.dec);
  ln_equ_to_hequ(&precessed_object, &cnow);
  printf("%d %d %f %d %d %f\n", cnow.ra.hours, cnow.ra.minutes, cnow.ra.seconds,
                                cnow.dec.degrees * (cnow.dec.neg?-1:1), cnow.dec.minutes, cnow.dec.seconds);
  return 0;
}