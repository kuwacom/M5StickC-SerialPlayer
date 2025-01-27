import argparse
import cv2
import serial
import time

FRAME_START_DRAW = 0xA1
PIXEL_DRAW = 0xA2

SET_STREAM_SIZE_RATIO = 0xA3

def videoToSerial(serialPort, serialInterval, videoPath, streamSizeRatio, dispWidth, dispHeight, skipCount):
    dispWidth = int(dispWidth / streamSizeRatio)
    dispHeight = int(dispHeight / streamSizeRatio)
    
    # シリアルポートの設定
    ser = serial.Serial(serialPort, 115200, timeout=1)

    cap = cv2.VideoCapture(videoPath)

    if not cap.isOpened():
        print("動画の読み込みに失敗しました。")
        exit()

    frameCount = 0
    totalFrameCount = 0

    # 実際に送る映像のサイズ倍率を設定
    ser.write(bytes([SET_STREAM_SIZE_RATIO, streamSizeRatio, 0, 0]))

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            totalFrameCount += 1
            if skipCount > frameCount:
                frameCount += 1    
                continue
            frameCount = 0
            
            # フレームリサイズ
            resizedFrame = cv2.resize(frame, (dispWidth, dispHeight))

            # フレームをBGRからRGBに変換
            rgbFrame = cv2.cvtColor(resizedFrame, cv2.COLOR_BGR2RGB)

            cv2.imshow("Preview", frame)
            print(f"Frame: {totalFrameCount}")
            
            if cv2.waitKey(1) & 0xFF == 27:
                break

            # 各ピクセルを逐次送信
            for y in range(dispHeight):
                for x in range(dispWidth):
                    r, g, b = rgbFrame[y, x]
                    # ピクセルごとのRGBデータ送信
                    if (serialInterval > 0):
                        time.sleep(serialInterval / 1000)
                    if x == 0 and y == 0:
                        # フレーム開始マーカーを送信
                        # print("FRAME_START")
                        ser.write(bytes([FRAME_START_DRAW, r, g, b]))
                    else:
                        # Type Draw Modeでデータ送信
                        ser.write(bytes([PIXEL_DRAW, r, g, b]))

            # print("FRAME_END")

            # 送信間隔
            # time.sleep(1 / 30)

    finally:
        cap.release()
        ser.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="動画をシリアル経由で送信")
    parser.add_argument("serialPort", help="シリアルポート名（例: COM10, /dev/usb.xxxx）")
    parser.add_argument("videoPath", help="動画ファイルのパス")
    # この倍率は、160x80のdisplayに対して40x20のフレームデータを表示するためのもの
    parser.add_argument("-ssr", "--streanSizeRatio", type=int, default=2, help="シリアルで送信する映像データのサイズ倍率（デフォルト: 2）")
    parser.add_argument("-dw", "--dispWidth", type=int, default=160, help="ディスプレイの幅（デフォルト: 160）")
    parser.add_argument("-dh", "--dispHeight", type=int, default=80, help="ディスプレイの高さ（デフォルト: 80）")
    parser.add_argument("-s", "--skipCount", type=int, default=4, help="スキップするフレーム数（デフォルト: 4）")
    parser.add_argument("-si", "--serialInterval", type=float, default=0, help="シリアル通信の間隔[ms]（デフォルト: 0）")

    args = parser.parse_args()

    # 動画を指定のシリアルポートに送信
    videoToSerial(args.serialPort, args.serialInterval, args.videoPath, args.streanSizeRatio, args.dispWidth, args.dispHeight, args.skipCount)
