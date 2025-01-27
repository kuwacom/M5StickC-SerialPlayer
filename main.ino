#include <M5StickC.h>
#include "src/M5StickCPlayMusic.h"
#include "src/M5StickCImageDisplay.h"

// image assets
#include "assets/winXP.h"
#include "assets/winXP_welcome.h"
#include "assets/winXP_home.h"
// audio assets
#include "assets/winXP_startup.h"
#include "assets/winXP_error.h"
#include "assets/winXP_shutdown.h"
#include "assets/dialUp.h"

#define FRAME_START_DRAW 0xA1
#define PIXEL_DRAW 0xA2
#define SET_STREAM_SIZE_RATIO 0xA3

// ディスプレイサイズ
#define DISP_WIDTH 160
#define DISP_HEIGHT 80

#define SPEAKER_PIN 26

M5StickCPlayMusic player(SPEAKER_PIN);
M5StickCImageDisplay display(DISP_WIDTH, DISP_HEIGHT);

void setup()
{
    M5.begin();
    M5.Lcd.fillScreen(TFT_BLACK);

    M5.Lcd.setRotation(1);
    // M5.Lcd.setCursor(0, 30, 4);
    // M5.Lcd.println("monitor");

    pinMode(SPEAKER_PIN, OUTPUT);

    display.displayImage(winXP);
    delay(4000);
    display.displayImage(winXP_welcome);
    player.playMusic(winXP_startup, 8000);
    delay(2000);
    // player.playMusic(dialUp, 8000);
    // delay(2000);
    display.displayImage(winXP_home);

    Serial.begin(115200);
}

void loop()
{
    static uint8_t serialBuffer[4];
    static int displayX = 0, displayY = 0, x = 0, y = 0;
    static uint8_t bufferType, r, g, b; // ピクセルのRGBデータ
    static uint8_t streamSizeRatio = 1;

    // Serialからデータを受信し、バッファに格納
    while (Serial.available() >= 4)
    {
        // バッファにデータを順次格納
        for (int i = 0; i < 4; i++)
        {
            serialBuffer[i] = Serial.read();
        }

        bufferType = serialBuffer[0];
        r = serialBuffer[1];
        g = serialBuffer[2];
        b = serialBuffer[3];

        if (bufferType == SET_STREAM_SIZE_RATIO)
        {
            streamSizeRatio = r;
            continue;
        }

        // 受け取ったモードが描画モードだったら
        if (bufferType == FRAME_START_DRAW || bufferType == PIXEL_DRAW)
        {
            if (bufferType == FRAME_START_DRAW)
            {
                // M5.Lcd.println("frame start");
                x = displayX = 0;
                y = displayY = 0;
            }

            // 受信したRGB値でピクセルを表示
            for (int i = 0; i < streamSizeRatio; i++)
                for (int j = 0; j < streamSizeRatio; j++)
                    M5.Lcd.drawPixel(displayX + i, displayY + j, M5.Lcd.color565(r, g, b));

            // M5.Lcd.drawPixel(x, y, M5.Lcd.color565(r, g, b));

            // 次のピクセル座標へ移動
            x++;
            displayX += streamSizeRatio;
            if (displayX >= DISP_WIDTH)
            {
                // M5.Lcd.println("next line");
                x = displayX = 0;
                y++;
                displayY += streamSizeRatio;
                if (displayY >= DISP_HEIGHT)
                {
                    // 座標が画面の範囲を超えた場合はリセット
                    y = displayY = 0;
                }
            }
        }
    }

    // display.displayImage(winXP_home);
    M5.update(); // ボタン状態を更新
    if (M5.BtnA.isPressed())
    { // M5ボタンが押された場合
        Serial.println("Rebooting...");
        display.displayImage(winXP_welcome);
        player.playMusic(winXP_shutdown, 8000);
        delay(1000);   // デバッグ用に1秒待機
        ESP.restart(); // システム再起動
    }
}