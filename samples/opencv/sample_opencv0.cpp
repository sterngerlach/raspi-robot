
using namespace std;

#include "opencv2/opencv.hpp"
#include <vector>
#include <stdio.h>

using namespace cv;

int main( int argc, char *argv[ ] ) {

  Mat im0, im1, gray;                    // 変数宣言

  VideoCapture cap0( 0 );            // カメラ0のキャプチャ
  if ( !cap0.isOpened( ) )
    return -1;    // キャプチャのエラー処理
  cap0.set( CV_CAP_PROP_FRAME_WIDTH,  320 );
  cap0.set( CV_CAP_PROP_FRAME_HEIGHT, 240 );

  VideoCapture cap1( 1 );            // カメラ1のキャプチャ
  if ( !cap1.isOpened( ) )
    return -1;    // キャプチャのエラー処理
  cap1.set( CV_CAP_PROP_FRAME_WIDTH,  320 );
  cap1.set( CV_CAP_PROP_FRAME_HEIGHT, 240 );
  
  while ( 1 ) {

    cap0 >> im0;                            // カメラ映像の取得
    cap1 >> im1;                            // カメラ映像の取得

    imshow( "Camera0", im0 );                // 映像の表示
    imshow( "Camera1", im1 );                // 映像の表示
    if ( waitKey( 30 ) >= 0 )
      break;                               // キー入力があれば終了

  }
  
  return 0;

}


