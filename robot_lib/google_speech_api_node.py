# coding: utf-8
# google_speech_api_node.py

# https://github.com/GoogleCloudPlatform/python-docs-samples/tree/master/speech/cloud-client
# https://cloud.google.com/speech-to-text/docs/reference/rpc/google.cloud.speech.v1
# https://cloud.google.com/speech-to-text/docs/reference/rest/v1/speech/recognize

import multiprocessing as mp
import os
import pyaudio
import queue
import sys

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

from data_sender_node import DataSenderNode

class MicrophoneStream(object):
    """
    マイクからの入力音声をストリームイテレータで返すためのクラス
    """
    
    # 1秒間のサンプリング回数
    RECORDING_RATE = 16000
    # 0.1秒間のサンプリング回数
    RECORDING_CHUNK = int(RECORDING_RATE / 10)

    def __init__(self):
        """コンストラクタ"""
        self.__rate = MicrophoneStream.RECORDING_RATE
        self.__chunk = MicrophoneStream.RECORDING_CHUNK

        self.__audio_buffer = queue.Queue()
        self.__is_closed = True

    def __enter__(self):
        """マイクからの録音を開始"""
        self.__audio_interface = pyaudio.PyAudio()
        self.__audio_stream = self.__audio_interface.open(
            format=pyaudio.paInt16, channels=1, rate=self.__rate,
            input=True, frames_per_buffer=self.__chunk,
            stream_callback=self.__fill_buffer)
        
        self.__is_closed = False

        return self

    def __exit__(self, type, value, traceback):
        """マイクからの録音を終了"""
        self.__audio_stream.stop_stream()
        self.__audio_stream.close()
        self.__is_closed = True
        
        # 録音の終了を伝達
        self.__audio_buffer.put(None)

        self.__audio_interface.terminate()

    def __fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """音声ストリームからのデータをバッファに挿入"""
        self.__audio_buffer.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.__is_closed:
            # 1つ以上のデータがバッファ内に格納されていることを保証
            chunk = self.__audio_buffer.get()
            # データがNoneであれば音声ストリームの終了を示す
            if chunk is None:
                return

            data = [chunk]

            while True:
                try:
                    # バッファから音声データを取得
                    chunk = self.__audio_buffer.get_nowait()
                    if chunk is None:
                        return

                    data.append(chunk)
                except queue.Empty:
                    break
            
            yield b"".join(data)

class GoogleSpeechApiNode(DataSenderNode):
    """
    Google Cloud Speech APIにより音声認識を行うクラス
    """

    def __init__(self, process_manager, msg_queue):
        """コンストラクタ"""
        super().__init__(process_manager, msg_queue)

        # Google Cloud Speech APIの初期化
        self.__setup_google_speech_api()

    def __setup_google_speech_api(self):
        """Google Cloud Speech APIの初期化"""
        # 環境変数GOOGLE_APPLICATION_CREDENTIALSを設定
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = \
            os.path.join(os.path.dirname(__file__), "speech-api-credentials.json")

        # Google Cloud Speech APIの初期化
        self.__language_code = "ja-JP"
        self.__speech_client = speech.SpeechClient()
        self.__recognition_config = types.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=MicrophoneStream.RECORDING_RATE,
            language_code=self.__language_code)
        self.__streaming_config = types.StreamingRecognitionConfig(
            config=self.__recognition_config,
            interim_results=True)

    def update(self):
        """音声入力を処理"""

        try:
            while True:
                try:
                    with MicrophoneStream() as mic_stream:
                        audio_generator = mic_stream.generator()
                        requests = (types.StreamingRecognizeRequest(audio_content=content)
                                    for content in audio_generator)
                        responses = self.__speech_client.streaming_recognize(
                            self.__streaming_config, requests)
                    
                        # 音声認識の結果をアプリケーションに送信
                        for response in responses:
                            # 認識結果が含まれない場合は無視
                            if not response.results:
                                continue
                            # 最初の認識結果のみを取得
                            result = response.results[0]
                            
                            # 認識結果が含まれない場合は無視
                            if not result.alternatives:
                                continue
                            # 認識の途中である場合は無視
                            if not result.is_final:
                                continue

                            # 認識結果の最初の候補を取得
                            transcript = result.alternatives[0].transcript
                            confidence = result.alternatives[0].confidence
                            words = result.alternatives[0].words

                            # アプリケーションに送出するメッセージを生成
                            result_msg = {}
                            # 認識した全体の文章
                            result_msg["transcript"] = transcript
                            # 認識された語彙のリスト
                            result_msg["words"] = [(word_info.word, confidence) for word_info in words]

                            # 認識した語彙に方向が含まれる場合
                            for direction in ("左", "右"):
                                if direction in transcript:
                                    result_msg["direction"] = (direction, confidence)

                            # 認識した語彙に命令が含まれる場合
                            for command in ("進め", "すすめ", "ブレーキ", "ストップ", "黙れ", "曲がれ"):
                                if command in transcript:
                                    result_msg["command"] = (command, confidence)

                            # アプリケーションにメッセージを送出
                            self.send_message("speechapi", result_msg)
                except Exception as e:
                    print("GoogleSpeechApiNode::update(): exception was thrown: {}".format(e))
                    continue
        except KeyboardInterrupt:
            # プロセスが割り込まれた場合
            print("GoogleSpeechApiNode::process_input(): KeyboardInterrupt occurred")

