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
    matrix.begin();
    Bridge.begin();
    Bridge.provide("set_core_bars", set_core_bars);
}

void loop() {
    if (has_new_bars) {
        has_new_bars = false;
        render_bars(pending_bars);
    }
    delay(10);
}
