# SPDX-FileCopyrightText: Copyright (C) 2025 ARDUINO SA <http://www.arduino.cc>
#
# SPDX-License-Identifier: MPL-2.0

# SPDX-FileCopyrightText: Copyright (C) 2025 ARDUINO SA <http://www.arduino.cc>
#
# SPDX-License-Identifier: MPL-2.0

import json
import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from queue import Queue, Empty

try:
    from arduino.app_utils import App, Bridge, Leds
except ImportError:
    class MockLeds:
        @staticmethod
        def set_led1_color(r, g, b):
            pass

        @staticmethod
        def set_led2_color(r, g, b):
            pass

    class MockBridge:
        @staticmethod
        def call(method, *args):
            print(f"[MockBridge] Bridge.call({method}, {args})")

    class MockApp:
        @staticmethod
        def run(user_loop=None):
            print("[MockApp] Running mock loop...")
            try:
                while True:
                    if user_loop:
                        user_loop()
                    else:
                        time.sleep(1)
            except KeyboardInterrupt:
                pass

    Bridge = MockBridge()
    App = MockApp()
    Leds = MockLeds()

PORT = int(os.environ.get("PORT", "5000"))
NUM_COLS = 13
MAX_ROWS = 8

update_queue = Queue(maxsize=1)
latest_metrics = {
    "cpu_cores": [],
    "ram": 0.0,
    "swap": 0.0,
    "cpu_temp": 0.0,
    "last_updated": 0,
}

last_message_time = 0.0
green_until = 0.0
last_applied_color = None


def set_upper_leds(r: bool, g: bool, b: bool):
    try:
        Leds.set_led1_color(r, g, b)
        Leds.set_led2_color(r, g, b)
    except Exception:
        pass

    try:
        Bridge.call("set_status_leds", r, g, b)
    except Exception:
        pass


class MetricsHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path not in ("/metrics", "/"):
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            payload = json.loads(post_data.decode("utf-8"))
            cpu_cores = payload.get("cpu_cores", [])
            ram = float(payload.get("ram", 0.0))
            swap = float(payload.get("swap", 0.0))
            cpu_temp = float(payload.get("cpu_temp", 0.0))

            global latest_metrics, last_message_time, green_until
            now = time.time()
            last_message_time = now
            green_until = now + 0.35

            latest_metrics = {
                "cpu_cores": cpu_cores,
                "ram": ram,
                "swap": swap,
                "cpu_temp": cpu_temp,
                "last_updated": now,
            }

            # Total 13 columns:
            # - Cols 0..7: CPU cores (up to 8 logical cores)
            # - Col 8: Spacer (blank)
            # - Cols 9..10: RAM (2 pixels wide)
            # - Col 11: Spacer (blank)
            # - Col 12: SWAP (1 pixel wide)
            bar_heights = ["0"] * NUM_COLS

            # CPU cores on the left (up to 8 cores)
            for idx, core_usage in enumerate(cpu_cores[:8]):
                usage_pct = max(0.0, min(100.0, float(core_usage)))
                height = int(round((usage_pct / 100.0) * MAX_ROWS))
                bar_heights[idx] = str(height)

            # RAM bar: 2 pixels wide at columns 9 and 10
            ram_pct = max(0.0, min(100.0, ram))
            ram_height = int(round((ram_pct / 100.0) * MAX_ROWS))
            bar_heights[9] = str(ram_height)
            bar_heights[10] = str(ram_height)

            # SWAP bar: 1 pixel wide at column 12
            swap_pct = max(0.0, min(100.0, swap))
            swap_height = int(round((swap_pct / 100.0) * MAX_ROWS))
            if swap_pct > 0 and swap_height == 0:
                swap_height = 1
            bar_heights[12] = str(swap_height)

            bars_str = "".join(bar_heights)

            # Keep only latest update in queue
            if update_queue.full():
                try:
                    update_queue.get_nowait()
                except Empty:
                    pass
            update_queue.put_nowait(bars_str)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')

        except Exception as err:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = json.dumps({"status": "error", "message": str(err)})
            self.wfile.write(response.encode("utf-8"))

    def do_GET(self):
        if self.path in ("/metrics", "/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(latest_metrics).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


def loop():
    global last_applied_color
    now = time.time()

    # Determine status color:
    # - Red: not receiving since >= 10s (or never received)
    # - Green: received message within last 350ms
    # - Yellow: waiting for next message
    if last_message_time == 0.0 or (now - last_message_time) >= 10.0:
        current_color = (True, False, False)
    elif now < green_until:
        current_color = (False, True, False)
    else:
        current_color = (True, True, False)

    if current_color != last_applied_color:
        last_applied_color = current_color
        set_upper_leds(*current_color)

    try:
        bars_str = update_queue.get(timeout=0.05)
        Bridge.call("set_core_bars", bars_str)
    except Empty:
        time.sleep(0.05)


def start_server():
    server = HTTPServer(("0.0.0.0", PORT), MetricsHandler)
    print(f"Metrics server listening on port {PORT}")
    server.serve_forever()


server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

App.run(user_loop=loop)
