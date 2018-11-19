// Include header file
#include <wiringPi.h>

// Main function
int main( void ) {
  int i;

  // Initialize WiringPi
  if ( wiringPiSetupGpio( ) == -1 )
    return 1;

  // Set GPIO19 pin to output mode
  pinMode( 19, OUTPUT );

  // Repeat LED blinking 10 times
  for ( i = 0; i < 10; i++ ) {
    digitalWrite( 19, 0 );
    delay( 950 );
    digitalWrite( 19, 1 );
    delay( 50 );
  }

  // Turn off LED
  digitalWrite( 19, 0 );

  return 0;
}

