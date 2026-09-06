# Cepheus load indicator for Arduino UNO Q

Display laptop CPU per-core load, RAM, and SWAP usage in real time on the Arduino UNO Q built-in 13×8 LED matrix, with connection status feedback on the 4 upper RGB LEDs.

## Project structure

```text
.
├── app.yaml               # App Lab manifest exposing port 5000
├── python/
│   └── main.py            # MPU HTTP server and Bridge dispatcher
├── sketch/
│   ├── sketch.ino         # MCU firmware driving LED matrix and status LEDs
│   └── sketch.yaml        # Zephyr board profile and libraries
├── client/
│   ├── monitor.py         # Laptop metrics collector (psutil)
│   ├── Dockerfile         # Lightweight Python container
│   ├── requirements.txt   # Client Python dependencies
│   └── .dockerignore
├── docker-compose.yml     # Client Docker compose configuration
├── Makefile               # App deployment and client container controls
└── .env                   # Host and port configuration
```

## Display layout

### LED matrix (13×8)

* Columns 0–7: CPU logical cores (1-pixel-wide vertical bars)
* Column 8: blank spacer column
* Columns 9–10: RAM usage (2-pixel-wide bar)
* Column 11: blank spacer column
* Column 12: SWAP usage (1-pixel-wide bar, lit at least 1 pixel when SWAP > 0%)

### Upper RGB status LEDs

* Green: message received (flashes for 350 ms on each packet)
* Yellow: waiting for next message (healthy connection)
* Red: disconnected or idle (no packet received for 10 seconds or waiting for first connection)

## Configuration

Default environment values are loaded from `.env`:

```env
ARDUINO_HOST=juno
ARDUINO_PORT=5000
METRICS_INTERVAL=1.0
```

`monitor.py` automatically falls back to direct Tailscale MagicDNS resolution (`100.100.100.100`) if bare hostnames cannot be resolved by standard host DNS.

## Deploying to the Arduino UNO Q

Ensure SSH access to your board is configured (e.g. `arduino@juno`).

### Makefile targets

* `make deploy`
  Stops any running app instance, syncs files, and starts the container with live logs

* `make start`
  Starts the app and prints container logs

* `make stop`
  Stops the app on the board

* `make logs`
  Fetches recent container logs

* `make logs-follow`
  Follows container logs in real time

* `make status`
  Lists current app state on the board

## Running the laptop client

### Running natively

1. Install dependencies:
   ```bash
   pip install -r client/requirements.txt
   ```
2. Start the monitor:
   ```bash
   python3 client/monitor.py
   ```

### Running with Docker

* `make client-build`
  Builds the slim client container (`python:3.12-slim`)

* `make client-run`
  Starts the client in the background with host network and PID access

* `make client-logs`
  Streams live logs from the client container

* `make client-stop`
  Stops the client container

