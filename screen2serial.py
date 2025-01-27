import argparse
import cv2
import serial
import time
import numpy as np
import pyautogui

FRAME_START_DRAW = 0xA1
PIXEL_DRAW = 0xA2
SET_STREAM_SIZE_RATIO = 0xA3

def screenToSerial(serialPort, serialInterval, streamSizeRatio, dispWidth, dispHeight, skipCount):
    dispWidth = int(dispWidth / streamSizeRatio)
    dispHeight = int(dispHeight / streamSizeRatio)

    # シリアルポートの設定
    ser = serial.Serial(serialPort, 115200, timeout=1)

    frameCount = 0
    totalFrameCount = 0

    # 実際に送る映像のサイズ倍率を設定
    ser.write(bytes([SET_STREAM_SIZE_RATIO, streamSizeRatio, 0, 0]))

    try:
        while True:
            # 画面全体をキャプチャ
            screenshot = pyautogui.screenshot()
            screenshot = screenshot.convert('RGB')
            screenFrame = np.array(screenshot)

            # フレームをBGRからRGBに変換（OpenCV互換の配列に変換）
            # プレビューとかだとこれ必要だけど、配列からデータとして取得するときは何故か b,g,r になるから利用しない
            # pyautogui.screenshot() # 自体がRGBで取得しているのかもしれない

            totalFrameCount += 1
            if skipCount > frameCount:
                frameCount += 1    
                continue
            frameCount = 0

            # フレームリサイズ
            resizedFrame = cv2.resize(screenFrame, (dispWidth, dispHeight))
            previewFrame = cv2.cvtColor(resizedFrame, cv2.COLOR_BGR2RGB)

            # プレビューを表示
            cv2.imshow("Screen Preview", previewFrame)
            print(f"Frame: {totalFrameCount}")

            # 各ピクセルを逐次送信
            for y in range(dispHeight):
                for x in range(dispWidth):
                    r, g, b = resizedFrame[y, x]
                    # ピクセルごとのRGBデータ送信
                    if serialInterval > 0:
                        time.sleep(serialInterval / 1000)
                    if x == 0 and y == 0:
                        # フレーム開始マーカーを送信
                        ser.write(bytes([FRAME_START_DRAW, r, g, b]))
                    else:
                        # Type Draw Modeでデータ送信
                        ser.write(bytes([PIXEL_DRAW, r, g, b]))

            # # フレーム間隔
            # time.sleep(1 / 30)

            if cv2.waitKey(1) & 0xFF == 27:  # ESCキーで終了
                break

    finally:
        ser.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="画面キャプチャをシリアル経由で送信")
    parser.add_argument("serialPort", help="シリアルポート名（例: COM10, /dev/usb.xxxx）")
    parser.add_argument("-ssr", "--streanSizeRatio", type=int, default=2, help="シリアルで送信する映像データのサイズ倍率（デフォルト: 2）")
    parser.add_argument("-dw", "--dispWidth", type=int, default=160, help="ディスプレイの幅（デフォルト: 160）")
    parser.add_argument("-dh", "--dispHeight", type=int, default=80, help="ディスプレイの高さ（デフォルト: 80）")
    parser.add_argument("-s", "--skipCount", type=int, default=0, help="スキップするフレーム数（デフォルト: 0）")
    parser.add_argument("-si", "--serialInterval", type=float, default=0, help="シリアル通信の間隔[ms]（デフォルト: 0）")

    args = parser.parse_args()

    # 画面キャプチャを指定のシリアルポートに送信
    screenToSerial(args.serialPort, args.serialInterval, args.streanSizeRatio, args.dispWidth, args.dispHeight, args.skipCount)
