
using namespace std;

#include "opencv2/opencv.hpp"
#include <vector>
#include <stdio.h>

using namespace cv;

int main( int argc, char *argv[ ] ) {

  Mat im, gray;                    // 変数宣言

  // カスケード分類器の取得
  CascadeClassifier cascade;

  if ( !cascade.load( "/usr/share/opencv/haarcascades/haarcascade_frontalface_alt.xml" ) )
    return -1;

  vector<Rect> faces;
  VideoCapture cap( 0 );            // カメラのキャプチャ

  if ( !cap.isOpened( ) )
    return -1;    // キャプチャのエラー処理

  cap.set( CV_CAP_PROP_FRAME_WIDTH,  160 );
  cap.set( CV_CAP_PROP_FRAME_HEIGHT, 120 );
  
  while ( 1 ) {

    cap >> im;                            // カメラ映像の取得

    cvtColor( im, gray, CV_RGB2GRAY );    // グレースケール変換

    // カスケード分類器で顔の探索
    cascade.detectMultiScale( gray, faces, 1.2, 2, CV_HAAR_SCALE_IMAGE, Size( 20, 20 ) );

    // 顔領域を矩形で囲む
    vector<Rect>::const_iterator r = faces.begin( );

    for ( ; r != faces.end( ); ++r ) {
      rectangle( im, Point( r->x, r->y ), Point(r->x + r->width, r->y + r->height), Scalar(20, 20, 200), 3, CV_AA);
    }

    imshow( "Camera", im );                // 映像の表示
    if ( waitKey( 30 ) >= 0 )
      break;                               // キー入力があれば終了

  }
  
  return 0;

}


