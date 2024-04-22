// msv_math_pkg.sv originally extended by Dave Purvis from uvm_ams.sv provided by Synopsys, copyright for original material is as follows:
//-----------------------------------------------------------------------------
// This confidential and proprietary software may be used only as authorized
// by a licensing agreement from Synopsys Inc. In the event of publication,
// the following notice is applicable:
//
// (C) COPYRIGHT 2013 SYNOPSYS INC.  ALL RIGHTS RESERVED
//
// The entire notice above must be reproduced on all authorized copies.
//-----------------------------------------------------------------------------

//-----------------------------------------------------------------------------
//
// Description : Math functions
//
//-----------------------------------------------------------------------------

////////////////////////////////////////////////////////////
`ifndef _MSV_MATH_PKG_SV
`define _MSV_MATH_PKG_SV

////////////////////////////////////////////////////////////
// Package: msv_math_pkg
//
//    The <msv_math_pkg> package provides pre-defined C functions
// that are useful for modeling generators and analog behaviors
package msv_math_pkg;

  // Function: cos
  //   This function returns the cosine of *a*.
  import "DPI-C" pure function real cos(input real a);
  // Function: cosh
  //   This function returns the hyperbolic cosine of *a*
  import "DPI-C" pure function real cosh(input real a);
  // Function: acos
  //   This function returns the inverse cosine (arccosine) of *a*.
  import "DPI-C" pure function real acos(input real a);
  // Function: acosh
  //   This function returns the inverse hyperbolic cosine of *a*
  import "DPI-C" pure function real acosh(input real a);

  // Function: sin
  //   This function returns the sine of *a*.
  import "DPI-C" pure function real sin(input real a);
  // Function: sinh
  //   This function Returns the hyperbolic sine of *a*
  import "DPI-C" pure function real sinh(input real a);
  // Function: asin
  //   This function returns the inverse sine (arcsine) of *a*.
  import "DPI-C" pure function real asin(input real a);
  // Function: asinh
  //   This function returns the inverse hyperbolic sine of *a*
  import "DPI-C" pure function real asinh(input real a);

  // Function: tan
  //   This function returns the tangent of *a*
  import "DPI-C" pure function real tan(input real a);
  // Function: tanh
  //   This function returns the hyperbolic tangent of *a*
  import "DPI-C" pure function real tanh(input real a);
  // Function: atan
  //   This function returns the inverse tangent (arctangent) of *a*.
  import "DPI-C" pure function real atan(input real a);
  // Function: atanh
  //   This function returns the inverse hyperbolic tangent of *a*
  import "DPI-C" pure function real atanh(input real a);
  // Function: atan2
  //   This function retunrs the inverse tangent (arctangent) of the real parts of *a* and *b*
  import "DPI-C" pure function real atan2(input real a, input real b);

  // Function: exp
  //   This function returns the base-e exponential function of *a*, which is the e number raised to the power *a* ...
  import "DPI-C" pure function real exp(input real a);
  // Function: expm1
  //   This function returns exp( *a* ) - 1
  import "DPI-C" pure function real expm1(input real a);
  // Function: log
  //   This function returns the base-e logarithm of *a*
  import "DPI-C" pure function real log(input real a);
  // Function: log10
  //   This function returns the base-10 logarithm of *a*
  import "DPI-C" pure function real log10(input real a);
  // Function: ilogb
  //   This function returns an unbiased exponent
  import "DPI-C" pure function int  ilogb(input real a);
  // Function: log1p
  //   This function returns log_e(1.0 + *a* )
  import "DPI-C" pure function real log1p(input real a);
  // Function: logb
  //   This function returns radix-independent exponent
  import "DPI-C" pure function real logb(input real a);

  // Function: fabs
  //   This function returns the absolute value of *a*
  import "DPI-C" pure function real fabs(input real a);
  // Function: ceil
  //   This function Returns the smallest integral value that is not less than *a*
  import "DPI-C" pure function real ceil(input real a);
  // Function: floor
  //   This function returns the largest integral value that is not greater than *a*
  import "DPI-C" pure function real floor(input real a);
  // Function: fmod
  //   This function Returns the floating-point remainder of numerator/denominator (*a* / *b*).
  //   The remainder of a division operation is the result of subtracting the integral quotient multiplied by the denominator from the numerator:
  //     remainder = numerator - quotient * denominator
  import "DPI-C" pure function real fmod(input real a, input real b);
  // Function: frexp
  //   This function Breaks the floating point number *a* into its binary significand
  // (a floating point value between 0.5(included) and 1.0(excluded)) and an integral *b* for 2, such that:
  //     *a* = significand * 2 exponent
  // The exponent is stored in the location pointed by *b*, and the significand is the value returned by the function.
  // If *a* is zero, both parts (significand and exponent) are zero.
  import "DPI-C" pure function real frexp(input real a, input logic [31:0] b); // ref for 2nd arg
  // Function: ldexp
  //   This function Returns the resulting floating point value from multiplying *a* (the significand)
  // by 2 raised to the power of *b* (the exponent).
  import "DPI-C" pure function real ldexp(input real a, input logic [31:0] b);

  // Removed this as it clashes with the glibc function of the same name (but is a different function)
//// Function: modf
////   This function Break into fractional and integral parts
////   Breaks *a* into two parts: the integer part (stored in the object pointed by *b*) and the fractional part (returned by the function).
////   Each part has the same sign as *a*.
//import "DPI-C" pure function real modf(input real a, input real b); // ref for 2nd arg

  // Function: pow
  //   This function returns *a* raised to the power *b*
  import "DPI-C" pure function real pow(input real a, input real b);
  // Function: sqrt
  //   This function returns the square root of *a*
  import "DPI-C" pure function real sqrt(input real a);
  // Function: hypot
  //   This function returns the length of the hypotenuse of a right-angled triangle with sides of length
  //   *a* and *b*.
  import "DPI-C" pure function real hypot(input real a, input real b);

  // Function: erf
  //   This function returns the error function of x; defined as
  //   erf(x) = 2/sqrt(pi)* integral from 0 to x of exp(-t*t) dt
  //   The erfc() function returns the complementary error function of x, that is 1.0 - erf(x).
  import "DPI-C" pure function real erf(input real a);
  // Function: erfc
  //   This function returns the complementary error function 1.0 - erf(x).
  import "DPI-C" pure function real erfc(input real a);

  // Function: gamma
  //   This function returns the gamma function of *a*
  import "DPI-C" pure function real gamma(input real a);
  // Function: lgamma
  //   This function returns the logarithm gamma function of *a*
  import "DPI-C" pure function real lgamma(input real a);

  // Function: j0
  //   This function returns the relevant Bessel value of x of the first kind of order 0
  import "DPI-C" pure function real j0(input real a);
  // Function: j1
  //   This function returns the relevant Bessel value of x of the first kind of order 1
  import "DPI-C" pure function real j1(input real a);
  // Function: jn
  //   This function returns the relevant Bessel value of x of the first kind of order n
  import "DPI-C" pure function real jn(input int i, input real a);

  // Function: y0
  //   This function returns the relevant Bessel value of x of the second kind of order 0
  import "DPI-C" pure function real y0(input real a);
  // Function: y1
  //   This function returns the relevant Bessel value of x of the second kind of order 1
  import "DPI-C" pure function real y1(input real a);
  // Function: yn
  //   This function returns the relevant Bessel value of x of the second kind of order n
  import "DPI-C" pure function real yn(input int i, input real a);

  // Function: isnan
  //   This function returns a non-zero value if value *a* is "not-a-number" (NaN), and 0 otherwise.
  import "DPI-C" pure function int  isnan(input real a);

  // Function: cbrt
  //   This function returns the real cube root of their argument *a*.
  import "DPI-C" pure function real cbrt(input real a);

  // Function: nextafter
  //   This function returns the next representable floating-point value following x in
  //   the direction of y.  Thus, if y is less than x, nextafter() shall return the largest
  //   representable floating-point number less than x.
  import "DPI-C" pure function real nextafter(input real a, input real b);

  // Function: remainder
  //   This function returns the floating-point remainder r= *a*- n*y* when *y* is non-zero. The value n is the integral value nearest the
  //   exact value *a*/ *y*.  When |n-*a*/*y*|=0.5, the value n is chosen to be even.
  import "DPI-C" pure function real remainder(input real a, input real b);

  // Function: rint
  //   This function returns the integral value (represented as a double) nearest *a* in the direction of the current rounding mode
  import "DPI-C" pure function real rint(input real a);
  // Function: scalb
  //   This function returns  *a* * r** *b*, where r is the radix of the machine floating-point arithmetic
  import "DPI-C" pure function real scalb(input real a, input real b);

endpackage: msv_math_pkg

`endif // _MSV_MATH_PKG_SV
