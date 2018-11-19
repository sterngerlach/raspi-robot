// 
// 2014.07.10
// TSUCHIYA, Akihito
// 
// changing the I2C BUS address
//
// デフォルトではSFR02のI2Cスレーブアドレスは"0xE0"となっている。
// 4つのSFR02を同時に使用する場合は、ユニークなアドレスを割り当てなければならない。
// 詳細は「SRF02 I2C Mode.pdf」の Changing the I2C Bus Address を参照。
//
// 使用法： $ sudo ./changeAddr oldAddress newAddress
//
#include <stdio.h>
#include <fcntl.h>
#include <stdlib.h> 
#include <string.h> 
#include "/usr/include/linux/i2c-dev.h"

int main( int argc, char **argv ) {

	int fd1;
	char filename[ 20 ];
	char buf[ 10 ];
	int res;
	int range = 0;

	// 引数のチェック
	if ( argc != 3 ) {
		printf( "Invalid arguments.\n" );
		printf( "Usage: %s oldAddr newAddr\n", argv[ 0 ] );
		printf( "       Usable addresses are 0x{E0,E2,E4,E6,E8,EA,EC,EE,F0,F2,F4,F6,F8,FA,FC,FE}.\n", argv[ 0 ] );
		exit( -1 );
	}

	// 引数のチェック - 正しいアドレスが指定されているか
	if ( strcmp( argv[ 1 ], "0xE0" ) == 0 )
		buf[ 9 ] = 0xE0;
	else if ( strcmp( argv[ 1 ], "0xE2" ) == 0 )
		buf[ 9 ] = 0xE2;
	else if ( strcmp( argv[ 1 ], "0xE4" ) == 0 )
		buf[ 9 ] = 0xE4;
	else if ( strcmp( argv[ 1 ], "0xE6" ) == 0 )
		buf[ 9 ] = 0xE6;
	else if ( strcmp( argv[ 1 ], "0xE8" ) == 0 )
		buf[ 9 ] = 0xE8;
	else if ( strcmp( argv[ 1 ], "0xEA" ) == 0 )
		buf[ 9 ] = 0xEA;
	else if ( strcmp( argv[ 1 ], "0xEC" ) == 0 )
		buf[ 9 ] = 0xEC;
	else if ( strcmp( argv[ 1 ], "0xEE" ) == 0 )
		buf[ 9 ] = 0xFE;
	else if ( strcmp( argv[ 1 ], "0xF0" ) == 0 )
		buf[ 9 ] = 0xF0;
	else if ( strcmp( argv[ 1 ], "0xF2" ) == 0 )
		buf[ 9 ] = 0xF2;
	else if ( strcmp( argv[ 1 ], "0xF4" ) == 0 )
		buf[ 9 ] = 0xF4;
	else if ( strcmp( argv[ 1 ], "0xF6" ) == 0 )
		buf[ 9 ] = 0xF6;
	else if ( strcmp( argv[ 1 ], "0xF8" ) == 0 )
		buf[ 9 ] = 0xF8;
	else if ( strcmp( argv[ 1 ], "0xFA" ) == 0 )
		buf[ 9 ] = 0xFA;
	else if ( strcmp( argv[ 1 ], "0xFC" ) == 0 )
		buf[ 9 ] = 0xFC;
	else if ( strcmp( argv[ 1 ], "0xFE" ) == 0 )
		buf[ 9 ] = 0xFE;
	else {
		printf( "Invalid fromAddress.\n" );
		printf( "Usage: %s oldAddr newAddr\n", argv[ 0 ] );
		printf( "       Usable addresses are 0x{E0,E2,E4,E6,E8,EA,EC,EE,F0,F2,F4,F6,F8,FA,FC,FE}.\n", argv[ 0 ] );
		exit( -2 );
	}

	// 引数のチェック - 正しいアドレスが指定されているか
	if ( strcmp( argv[ 2 ], "0xE0" ) == 0 )
		buf[ 2 ] = 0xE0;
	else if ( strcmp( argv[ 2 ], "0xE2" ) == 0 )
		buf[ 2 ] = 0xE2;
	else if ( strcmp( argv[ 2 ], "0xE4" ) == 0 )
		buf[ 2 ] = 0xE4;
	else if ( strcmp( argv[ 2 ], "0xE6" ) == 0 )
		buf[ 2 ] = 0xE6;
	else if ( strcmp( argv[ 2 ], "0xE8" ) == 0 )
		buf[ 2 ] = 0xE8;
	else if ( strcmp( argv[ 2 ], "0xEA" ) == 0 )
		buf[ 2 ] = 0xEA;
	else if ( strcmp( argv[ 2 ], "0xEC" ) == 0 )
		buf[ 2 ] = 0xEC;
	else if ( strcmp( argv[ 2 ], "0xEE" ) == 0 )
		buf[ 2 ] = 0xFE;
	else if ( strcmp( argv[ 2 ], "0xF0" ) == 0 )
		buf[ 2 ] = 0xF0;
	else if ( strcmp( argv[ 2 ], "0xF2" ) == 0 )
		buf[ 2 ] = 0xF2;
	else if ( strcmp( argv[ 2 ], "0xF4" ) == 0 )
		buf[ 2 ] = 0xF4;
	else if ( strcmp( argv[ 2 ], "0xF6" ) == 0 )
		buf[ 2 ] = 0xF6;
	else if ( strcmp( argv[ 2 ], "0xF8" ) == 0 )
		buf[ 2 ] = 0xF8;
	else if ( strcmp( argv[ 2 ], "0xFA" ) == 0 )
		buf[ 2 ] = 0xFA;
	else if ( strcmp( argv[ 2 ], "0xFC" ) == 0 )
		buf[ 2 ] = 0xFC;
	else if ( strcmp( argv[ 2 ], "0xFE" ) == 0 )
		buf[ 2 ] = 0xFE;
	else {
		printf( "Invalid toAddress.\n" );
		printf( "Usage: %s oldAddr newAddr\n", argv[ 0 ] );
		printf( "       Usable addresses are 0x{E0,E2,E4,E6,E8,EA,EC,EE,F0,F2,F4,F6,F8,FA,FC,FE}.\n", argv[ 0 ] );
		exit( -3 );
	}

	// I2Cデータバスをオープン
	sprintf( filename, "/dev/i2c-1" );
	fd1 = open( filename, O_RDWR );
	if ( fd1 < 0 ) {
		printf( "Error on open\n" );
		exit( 1 );
	}

	// アドレスは上位7ビットが使用される
	// ex. E0(16) -> 11100000(2) -> 1110000(1) -> 70(16) コマンドラインで i2cdetectを実行した時に表示されるアドレス
	if ( ioctl( fd1, I2C_SLAVE, buf[ 9 ] >> 1 ) < 0 ) {
		printf( "Error on slave address\n" );
		exit( 1 );
	}

	// アドレスを変更するためのステップ１/３
	buf[ 0 ] = 0x00; // command register
	buf[ 1 ] = 0xA0; // procedure step1 to change address.
	if ( ( write( fd1, buf, 2 ) ) != 2 ) {
		printf( "Error send the read command\n" );
		exit( 1 );
	}
	// 念のため処理待ち
	usleep( 80000 );

	// アドレスを変更するためのステップ２/３
	buf[ 0 ] = 0x00; // command register
	buf[ 1 ] = 0xAA; // procedure step2 to change address.
	if ( ( write( fd1, buf, 2 ) ) != 2 ) {
		printf( "Error send the read command\n" );
		exit( 1 );
	}
	// 念のため処理待ち
	usleep( 80000 );

	// アドレスを変更するためのステップ３/３
	buf[ 0 ] = 0x00; // command register
	buf[ 1 ] = 0xA5; // procedure step3 to change address.
	if ( ( write( fd1, buf, 2 ) ) != 2 ) {
		printf( "Error send the read command\n" );
		exit( 1 );
	}
	// 念のため処理待ち
	usleep( 80000 );

	// アドレス変更のための準備（３つのステップ）を終え、ついに新しいアドレスをセット
	buf[ 0 ] = 0x00; // command register
	buf[ 1 ] = buf[ 2 ];
	if ( ( write( fd1, buf, 2 ) ) != 2 ) {
		printf( "Error send the read command\n" );
		exit( 1 );
	}
	// 念のため処理待ち
	usleep( 80000 );

	// データバスを閉じる
	close( fd1 );

	return 0;
}
