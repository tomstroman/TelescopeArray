/* localpoint.c
 * Thomas Stroman, University of Utah 2017-05-26
 * Compilation instructions:
 * 0. Set up TRUMP (Telescope Array proprietary software)
 * 1. add localpoint.c to $TRUMP/bin
 * 2. Make the following modifications to $TRUMP/Makefile
 *      a. append "localpoint.c" to BINSRC definition
 *      b. insert these two lines among the other ".PHONY" entries:
.PHONY: localpoint
localpoint: bin/localpoint.run
 * 3. compile with "make localpoint"
 */
#include <ctype.h>
#include <sys/types.h>
#include <sys/times.h>

#include "trump.h"



// global variables:
// TRUMP-specific simulation control structure
RuntimeParameters *par;
RayTrace *ray;

double segDeflectAzDeg[18];
double segDeflectAltDeg[18];
double segSpot[18];

// function prototypes
void PrintUsage(char *name);
void ParseCommandLine(int argc, char *argv[]);
void ModifySegments(FDSiteGeometry *g, int mir);
void runRayTrace(RuntimeParameters *par, FDSiteGeometry *fdsg, TGeom *tgeom, RayTrace *ray, FILE *out);



// inputs: a geometry DST filename, a mirror number, point source location,
//      mirror segment deviations, output filename
// output: a list of x,y positions of rays striking the camera plane

int main(int argc, char *argv[]) {
  // required initial setup of control structure
  par = newInstanceOf(RuntimeParameters);
  initializeParameters(par);

  ray = newInstanceOf(RayTrace);
  ParseCommandLine(argc, argv);
  
  // prepare output destination
  FILE *out;
  if (strcmp(par->outfn, "NULL") != 0)
    out = fopen(par->outfn, "w");
  else
    out = stdout;  
  
//   int i, k, mir; 
//   double banana_error, seg_rcurve;

  // Load original site geometry
  FDSiteGeometry *fdsg = newInstanceOf(FDSiteGeometry);
  loadFDSiteGeometry(par->geometryFile, fdsg);
  par->siteid = fdsg->siteid;
  
  // Modify geometry according to command-line arguments
  ModifySegments(fdsg, ray->cam);
  
  // Initialize variables necessary for ray-tracing
  UCalibration *calib = newInstanceOf(UCalibration);
  calib->nmir = fdsg->nmir;
  calib->tc = newInstanceOf(TACalibration);
  TACalibration *tacalib = calib->tc;
  tacalib->nmir = calib->nmir;
  getTADefaultCalibration(par, tacalib);
  
  // Initialize random-number generator
#ifdef _OPENMP
  int rs;
  for (rs=0; rs<omp_get_max_threads(); rs++)
    ranq2setup(rs, par->seed+rs);
#else
  ranq2setup(par->seed);
#endif  
  
  // Initialize ray-trace
  TGeom *tgeom = newInstanceOf(TGeom);
  initRayTrace(fdsg, tgeom, calib); 
 
  
  // PERFORM THE RAY-TRACE
  runRayTrace(par, fdsg, tgeom, ray, out);

  // close the output file
  if (strcmp(par->outfn, "NULL") != 0)
    fclose(out);

  return 0;
}




// {
//   if (par->nevt >= 0) {
//     mir = par->nevt;
//     fprintf(stderr, "Selected site %d mirror %d.\n", par->siteid, mir);
//     fprintf(stderr, "Zenith: %5.2f deg; Azimuth: %6.2f deg CCWE or %6.2f deg CWN\n", 
//             fdsg->mir_the[mir]*R2D, fdsg->mir_phi[mir]*R2D, fmod(450.0-fdsg->mir_phi[mir]*R2D,360.0));
//     fprintf(stderr, "Original SSPs:");
//     for (i=0; i<fdsg->nseg[mir]; i++) {
//       fprintf(stderr, " %.3f", fdsg->seg_spot[mir][i]);
//     }
//     fprintf(stderr,"\n");
//     
//     if (par->flag_mirref) {
//       banana_error = par->phiimplo;
//       if (banana_error > 1.0) {
//         banana_error = (fdsg->ring3[mir]==2)?0.098:0.0;
//         if (mir==4 && par->siteid==BLACK_ROCK_SITEID) {
//           banana_error = 0;
//         }
//       }
//       seg_rcurve = par->phiimphi;
//       if (seg_rcurve < 0) {
//         seg_rcurve = 6.058;
//       }
//             
//       RefocusSegments(fdsg, mir, banana_error, seg_rcurve);
//     }
//   } 
  
  // Load default calibration, necessary for ray trace initialization  
  
  
  


/*
  if (par->trigid) {
    tgeom->n_glass = tgeom->n_air; // no Snell shift if Paraglas open
    tgeom->thick_incam -= 0.0047625; // thickness of 3/16" posterboard
//     tgeom->thick_incam -= 0.05;
    tgeom->thick_filter = 0; // want image on surface of board
    tgeom->n_filter = tgeom->n_air; // just for peace of mind.

    
  }
  
  if (par->nsbackground >= 0) { // override the spot-size parameter!
    for (i=0; i<fdsg->nmir; i++) {
      for (k=0; k<fdsg->nseg[i]; k++)
        tgeom->spot[i][k] = par->nsbackground * (0.01 / 0.195);
//       tgeom->spot[i][1] = 50.;
    }
  }*/
  


  

// #define HALFCAM_X 0.58
// #define HALFCAM_Y 0.505
// #define CAM_Z 0.25
// #define STAN_MEAS 2.957

  
void runRayTrace(RuntimeParameters *par, FDSiteGeometry *fdsg, TGeom *tgeom, RayTrace *ray, FILE *out) {
  int i, pmt;
  fprintf(stderr, "par->ntry %d\n", par->ntry);
  for (i=0; i<par->ntry; i++) {
    pmt = trace(fdsg, tgeom, ray);
    // record position of ray that hits the camera face whether or not it found a PMT:
    // MISSED_TUBE = -2, defined in raytrace.h
    if (pmt >= MISSED_TUBE) {
      fprintf(out, "%d %d %f %f\n",
              ray->cam, pmt, ray->xcam,
              // flip the Y coordinate when using certain older geometry files
              ray->ycam*((fdsg->uniqID==0 || fdsg->uniqID==1320019200)?-1.:1.));
    }
  }
}
  
  
#define DEFAULT_NRAYS 1000000
void ParseCommandLine(int argc, char *argv[]) {
  // Set up defaults
  sprintf(par->outfn, "out.txt");
  sprintf(par->geometryFile, "%s/fdgeom/geobr.dst.gz", RTDATA);
  
// -6.067 m (nominal curvature radius) + 2.957 m (measured by Stan) = -3.110 m
#define NOMINAL_SCREEN_CENTER -3.110
  // default to the center of the screen on mirror 0
  ray->cam = 0;
  ray->vsite[0] = 0;
  ray->vsite[1] = 0;
  ray->vsite[2] = NOMINAL_SCREEN_CENTER;
  
  par->ntry = DEFAULT_NRAYS;           // rays to trace, override with -rays

  int i, j;
  double ssp;
  
  for (j=0; j<18; j++) {
    segDeflectAltDeg[j] = 0;
    segDeflectAzDeg[j] = 0;
    segSpot[j] = -1;
  }
  
  for (i=1; i<argc; i++) {
    if (strcmp(argv[i], "-geo") == 0) {
      sprintf(par->geometryFile, "%s", argv[++i]);
    }

    else if (strcmp(argv[i], "-mir") == 0) {
      ray->cam = atoi(argv[++i]);
    }

    else if (strcmp(argv[i], "-rays") == 0) {
      par->ntry = atoi(argv[++i]);
    }

    else if (strcmp(argv[i], "-o") == 0) {
      sprintf(par->outfn, "%s", argv[++i]);
    }

    else if (strcmp(argv[i], "-xy") == 0) {
      ray->vsite[0] = atof(argv[++i]);
      ray->vsite[1] = atof(argv[++i]);
    }
    
    else if (strcmp(argv[i], "-dz") == 0) {
      ray->vsite[2] = NOMINAL_SCREEN_CENTER + atof(argv[++i]);
    }
    
    else if (strcmp(argv[i], "-seg") == 0) {
      j = atoi(argv[++i]);
      segDeflectAzDeg[j] = atof(argv[++i]);
      segDeflectAltDeg[j] = atof(argv[++i]);
    }
    
    else if (strcmp(argv[i], "-ssp") == 0) {
      ssp = atof(argv[++i]);
      for (j=0; j<18; j++) {
        segSpot[j] = ssp;
      }
    }
    else {
      fprintf(stderr, "\nUnrecognized option : %s\n", argv[i]);
      PrintUsage(argv[0]);
      exit(1);
    }
  }
  
  // validation
  if (argc == 1) {
    PrintUsage(argv[0]);
    exit(1);
  }
  
  fprintf(stderr, "Run parameters:\n");
  fprintf(stderr, "Using mirror %d from geometry %s\n", ray->cam, par->geometryFile);
  fprintf(stderr, "Emitting %d rays from ( %f, %f, %f )\n", par->ntry, ray->vsite[0], ray->vsite[1], ray->vsite[2]);
  fprintf(stderr, "Writing to %s\n", par->outfn);
  fprintf(stderr, "Raytrace toggles active (from raytrace.h; re-compile required to change):\n");  
  fprintf(stderr, USE_WIGGLE?"USE_WIGGLE ":"");
  fprintf(stderr, USE_HIT_CAMERABOX?"***USE_HIT_CAMERABOX*** ":"");
  fprintf(stderr, USE_HIT_CAMERAPOLES?"***USE_HIT_CAMERAPOLES*** ":"");
  fprintf(stderr, USE_MIR_ABSORBED?"USE_MIR_ABSORBED ":"");
  fprintf(stderr, USE_HIT_CRACK?"USE_HIT_CRACK ":"");
  fprintf(stderr, USE_MISSED_CAMERA?"USE_MISSED_CAMERA ":"");
  fprintf(stderr, USE_CAMCOVER_ABSORBED?"USE_CAMCOVER_ABSORBED ":"");
  fprintf(stderr, USE_CAMCOVER_SHIFT?"USE_CAMCOVER_SHIFT ":"");
  fprintf(stderr, USE_FILTER_ABSORBED?"USE_FILTER_ABSORBED ":"");
  fprintf(stderr, USE_FILTER_SHIFT?"USE_FILTER_SHIFT ":"");
  fprintf(stderr, USE_MISSED_TUBE?"USE_MISSED_TUBE ":"");
  fprintf(stderr, USE_PMT_UNIFORMITY?"USE_PMT_UNIFORMITY ":"");
  fprintf(stderr, USE_PMT_QE?"USE_PMT_QE ":"");
  fprintf(stderr, "\n\n");
}

void PrintUsage (char *name) {
  fprintf(stderr, "\nusage : %s [options]\n", name);
  fprintf(stderr, "Options:\n");
  fprintf(stderr, "  -geo <file>       Input geometry file (default: geobr.dst.gz)\n");
  fprintf(stderr, "  -mir <m>          Record rays on mirror m (default: 0)\n");
  fprintf(stderr, "  -o <file>         Output text file name (default: out.txt)\n");
  fprintf(stderr, "  -rays <n>         Trace <n> rays from position (default: %d)\n", DEFAULT_NRAYS);
  fprintf(stderr, "  -xy <X> <Y>       Position of source is <X> meters LEFT of screen center, <Y> meters UP (defaults: 0, 0)\n");
  fprintf(stderr, "  -dz <Z>           Position of source is <Z> meters FARTHER from mirror THAN screen (default: 0)\n");
  fprintf(stderr, "  -seg <S> <X> <Y>  Rotate segment <S> <X> degrees to the right, then <Y> degrees up\n");
  fprintf(stderr, "  -ssp <W>          Set mirror spot-size parameter to <W> degrees\n");
}

void ModifySegments(FDSiteGeometry *g, int mir) {
  int i, j;
  double seg_pos[3]; // position of segment in mirror coordinates
  double cen_curve_seg[3]; // position of segment curvature center FROM segment position
  for (i=0; i<18; i++) {
    if (segSpot[i] >= 0) {
      g->seg_spot[mir][i] = segSpot[i];
    }
    if (segDeflectAzDeg[i] == 0 && segDeflectAltDeg[i] == 0)
      continue;
    
    
    for (j=0; j<3; j++) {
      seg_pos[j] = g->vseg3[mir][i][j] * g->rcurve3[mir];
      cen_curve_seg[j] = g->seg_center[mir][i][j] - seg_pos[j];
    }
    
    // Camera coordinates: mirror looks along z-axis, x-axis points to the left, and y-axis points up
    // (x and y tangent to camera face plane)
    
    // So a rotation to the "right" is a negative rotation about Y
    // and a rotation up is a negative rotation about X
    
    // but rotx and roty functions rotate axes, not vectors, so cancel the negative.
    roty(cen_curve_seg, segDeflectAzDeg[i]*D2R, cen_curve_seg);
    rotx(cen_curve_seg, segDeflectAltDeg[i]*D2R, cen_curve_seg);
    
    for (j=0; j<3; j++) {
      g->seg_center[mir][i][j] = seg_pos[j] + cen_curve_seg[j];
    }
  }
}
