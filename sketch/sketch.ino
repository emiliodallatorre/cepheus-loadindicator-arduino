// SPDX-FileCopyrightText: Copyright (C) 2025 ARDUINO SA <http://www.arduino.cc>
//
// SPDX-License-Identifier: MPL-2.0

#include "Arduino_RouterBridge.h"
#include <Arduino_LED_Matrix.h>

static const int ROWS = 8;
static const int COLS = 13;

ArduinoLEDMatrix matrix;
String pending_bars = "";
volatile bool has_new_bars = false;

void set_status_leds(bool r, bool g, bool b) {
    // LED 3 (PWM channels)
    analogWrite(LED3_R, r ? 255 : 0);
    analogWrite(LED3_G, g ? 255 : 0);
    analogWrite(LED3_B, b ? 255 : 0);

    // LED 4 (active low digital channels)
    digitalWrite(LED4_R, r ? LOW : HIGH);
    digitalWrite(LED4_G, g ? LOW : HIGH);
    digitalWrite(LED4_B, b ? LOW : HIGH);
}

void render_bars(const String& bars) {
    uint8_t frame[ROWS][COLS] = {0};
    int len = bars.length();

    for (int col = 0; col < COLS && col < len; col++) {
        char c = bars.charAt(col);
        int h = (c >= '0' && c <= '8') ? (c - '0') : 0;
        // Draw 1-pixel wide vertical bar from bottom (row 7) upwards
        for (int row = ROWS - h; row < ROWS; row++) {
            frame[row][col] = 1;
        }
    }

    matrix.setGrayscaleBits(1);
    matrix.draw(&frame[0][0]);
}

void set_core_bars(String bars) {
    pending_bars = bars;
    has_new_bars = true;
}

void setup() {
    pinMode(LED4_R, OUTPUT);
    pinMode(LED4_G, OUTPUT);
    pinMode(LED4_B, OUTPUT);

    // Initial status: Red (waiting for connection)
    set_status_leds(true, false, false);

    matrix.begin();
    Bridge.begin();
    Bridge.provide("set_core_bars", set_core_bars);
    Bridge.provide("set_status_leds", set_status_leds);
}

void loop() {
    if (has_new_bars) {
        has_new_bars = false;
        render_bars(pending_bars);
    }
    delay(10);
}
