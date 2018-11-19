//モータスピードを指定時間でスロープで上げ下げする

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include <wiringPi.h>
#include <wiringPiSPI.h>

int L6470_SPI_CHANNEL; 
int BUFSIZE = 32;

// 関数プロトタイプ。
void L6470_write(unsigned char data);
void L6470_init(void);
void L6470_run(long speed);
void L6470_run_both(long speed);
void L6470_softstop();
void L6470_softhiz();

int main(int argc, char **argv)
{
        int i,j;
        long speed = 0;

        char*str = (char*)malloc ( BUFSIZE*sizeof( char ));
        char c;
		long s;
		float sl;
		long S = 0;
			

        printf("***** start spi test program *****\n");

        // SPI channel 0 を 1MHz で開始。
        //if (wiringPiSPISetup(L6470_SPI_CHANNEL, 1000000) < 0)
        if (wiringPiSPISetup(0, 1000000) < 0){
                printf("SPI Setup failed:\n");
        }
        if (wiringPiSPISetup(1, 1000000) < 0){
                printf("SPI Setup failed:\n");
        }

        // L6470の初期化。
		L6470_SPI_CHANNEL = 0;
        L6470_init();
		L6470_SPI_CHANNEL = 1;
		L6470_init();

        while(1)
        {
            printf( "speed?? (Maximum: +-40000)\n");
            scanf( "%ld", &s );
            printf( "slope time? \n");
            scanf( "%f", &sl );
            
            //　順方向のスピードを与えられたとき
            if(  s != 0 && s > speed ){
                for(i = speed; i <= s; i=i+100 ) {
                    speed = i;
                    usleep(75*1000000*sl/s);  // 100-->75 下五行のプログラム実行時間を考慮して。
                    printf("%d\n", i ); 
                    L6470_run_both(speed);
                }
                
            }

            //　逆方向のスピードを与えられたとき
            if(  s != 0 && s < speed ){
                for(i = speed; i >= s; i=i-100 ) {
                    speed = i;
                    usleep(abs(75*1000000*sl/s));
                    printf("%d\n", i ); 
                    L6470_run_both(speed);
                }
            }

            //　順方向のスピードのとき、停止の命令を与えられたとき
            if( s == 0 && speed > 0){
                for(j = speed; j >= 0; j=j-100 ) {
                    speed = j;
                    usleep(75*1000000*sl/i);
                    printf("%d\n", j ); 
                    L6470_run_both(speed);
                }
            }

            //　逆方向のスピードのとき、停止の命令を与えられたとき
            if( s == 0 && speed < 0){
                for(j = speed; j <= 0; j=j+100 ) {
                    speed = j;
                    usleep(75*-1000000*sl/i);
                    printf("%d\n", j ); 
                    L6470_run_both(speed);
                }
            }
        }

        return 0;
}


void L6470_write(unsigned char data)
{
        wiringPiSPIDataRW(L6470_SPI_CHANNEL, &data, 1);
	/* wiringPiSPIDataRW(0, &data, 1);
	wiringPiSPIDataRW(1, &data, 1); */
}

void L6470_init()
{
        // MAX_SPEED設定。
        /// レジスタアドレス。
        L6470_write(0x07);
        // 最大回転スピード値(10bit) 初期値は 0x41
        L6470_write(0x00);
        L6470_write(0x25);

        // KVAL_HOLD設定。
        /// レジスタアドレス。
        L6470_write(0x09);
        // モータ停止中の電圧設定(8bit)
        L6470_write(0xFF);

        // KVAL_RUN設定。
        /// レジスタアドレス。
        L6470_write(0x0A);
        // モータ定速回転中の電圧設定(8bit)
        L6470_write(0xFF);

        // KVAL_ACC設定。
        /// レジスタアドレス。
        L6470_write(0x0B);
        // モータ加速中の電圧設定(8bit)
        L6470_write(0xFF);

        // KVAL_DEC設定。
        /// レジスタアドレス。
        L6470_write(0x0C);
        // モータ減速中の電圧設定(8bit) 初期値は 0x8A
        L6470_write(0x40);

        // OCD_TH設定。
        /// レジスタアドレス。
        L6470_write(0x13);
        // オーバーカレントスレッショルド設定(4bit)
        L6470_write(0x0F);

        // STALL_TH設定。
        /// レジスタアドレス。
        L6470_write(0x14);
        // ストール電流スレッショルド設定(4bit)
        L6470_write(0x7F);

		//start slopeデフォルト
        /// レジスタアドレス。
		L6470_write(0x0e);
		L6470_write(0x00);

		//デセラレーション設定
        /// レジスタアドレス。
		L6470_write(0x10);
		L6470_write(0x29);

}

void L6470_run(long speed)
{
        unsigned short dir;
        unsigned long spd;
        unsigned char spd_h;
        unsigned char spd_m;
        unsigned char spd_l;

        // 方向検出。
        if (speed < 0)
        {
                dir = 0x50;
                spd = -1 * speed;
        }
        else
        {
                dir = 0x51;
                spd = speed;
        }

        // 送信バイトデータ生成。
        spd_h = (unsigned char)((0x0F0000 & spd) >> 16);
        spd_m = (unsigned char)((0x00FF00 & spd) >> 8);
        spd_l = (unsigned char)(0x00FF & spd);

        // コマンド（レジスタアドレス）送信。
        L6470_write(dir);
        // データ送信。
        L6470_write(spd_h);
        L6470_write(spd_m);
        L6470_write(spd_l);
}

void L6470_run_both(long speed)
{
		L6470_SPI_CHANNEL = 0;
	    L6470_run(speed);
		L6470_SPI_CHANNEL = 1;
		L6470_run(-1*speed);		
}

void L6470_softstop()
{
        unsigned short dir;
        printf("***** SoftStop. *****\n");
        dir = 0xB0;
        // コマンド（レジスタアドレス）送信。
        L6470_write(dir);
        delay(1000);
}

void L6470_softhiz()
{
        unsigned short dir;
        printf("***** Softhiz. *****\n");
        dir = 0xA8;
        // コマンド（レジスタアドレス）送信。
        L6470_write(dir);
        delay(1000);
}
