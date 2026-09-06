#!/usr/bin/env python3
import json
import os
import socket
import struct
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import psutil


def load_env_file():
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parent.parent / ".env",
    ]
    for env_path in candidates:
        if env_path.is_file():
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ.setdefault(key.strip(), val.strip().strip("\"'"))
            break


load_env_file()

ARDUINO_HOST = os.environ.get("ARDUINO_HOST", "juno")
ARDUINO_PORT = int(os.environ.get("ARDUINO_PORT", "5000"))
METRICS_INTERVAL = float(os.environ.get("METRICS_INTERVAL", "1.0"))
_resolved_host_ip = None


def resolve_host(host):
    # Already an IPv4 address
    try:
        socket.inet_aton(host)
        return host
    except socket.error:
        pass

    # Standard system DNS
    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        pass

    # Direct Tailscale MagicDNS fallback at 100.100.100.100
    try:
        header = struct.pack(">HHHHHH", 0x1234, 0x0100, 1, 0, 0, 0)
        qname = b"".join(bytes([len(p)]) + p.encode("ascii") for p in host.split(".")) + b"\x00"
        qtype = struct.pack(">HH", 1, 1)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1.5)
        sock.sendto(header + qname + qtype, ("100.100.100.100", 53))
        data, _ = sock.recvfrom(512)
        sock.close()
        if len(data) >= 16:
            return socket.inet_ntoa(data[-4:])
    except Exception:
        pass

    return host


def get_endpoint_url():
    global _resolved_host_ip
    if not _resolved_host_ip:
        _resolved_host_ip = resolve_host(ARDUINO_HOST)
    return f"http://{_resolved_host_ip}:{ARDUINO_PORT}/metrics"


def get_cpu_temperature():
    if not hasattr(psutil, "sensors_temperatures"):
        return 0.0

    temps = psutil.sensors_temperatures()
    if not temps:
        return 0.0

    preferred_sensors = ["thinkpad", "coretemp", "k10temp", "cpu_thermal", "zenpower", "acpitz"]
    for sensor in preferred_sensors:
        if sensor in temps and temps[sensor]:
            for entry in temps[sensor]:
                if entry.current and entry.current > 0:
                    return float(round(entry.current, 1))

    for entries in temps.values():
        for entry in entries:
            if entry.current and entry.current > 0:
                return float(round(entry.current, 1))

    return 0.0


def collect_metrics():
    # Calling with interval=None returns usage since last call or system boot
    cpu_cores = [float(round(val, 1)) for val in psutil.cpu_percent(percpu=True, interval=None)]
    ram = float(round(psutil.virtual_memory().percent, 1))
    swap = float(round(psutil.swap_memory().percent, 1))
    cpu_temp = get_cpu_temperature()

    return {
        "cpu_cores": cpu_cores,
        "ram": ram,
        "swap": swap,
        "cpu_temp": cpu_temp,
    }


def send_metrics(payload):
    global _resolved_host_ip
    data = json.dumps(payload).encode("utf-8")
    url = get_endpoint_url()
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Host": f"{ARDUINO_HOST}:{ARDUINO_PORT}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            return resp.status == 200
    except urllib.error.URLError:
        _resolved_host_ip = None
        raise


def main():
    print(f"Monitoring system stats -> target: http://{ARDUINO_HOST}:{ARDUINO_PORT}/metrics")
    print(f"Update interval: {METRICS_INTERVAL}s (Ctrl+C to quit)\n")

    # Prime psutil CPU percentages
    psutil.cpu_percent(percpu=True, interval=None)
    time.sleep(0.2)

    while True:
        metrics = collect_metrics()
        try:
            success = send_metrics(metrics)
            status = "OK" if success else "FAILED"
        except urllib.error.URLError as err:
            status = f"CONNECT ERROR: {err.reason}"
        except Exception as err:
            status = f"ERROR: {err}"

        cores_str = ", ".join(f"{c}%" for c in metrics["cpu_cores"])
        print(
            f"[{status}] CPU: [{cores_str}] | RAM: {metrics['ram']}% | "
            f"SWAP: {metrics['swap']}% | Temp: {metrics['cpu_temp']}°C"
        )

        time.sleep(METRICS_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting monitor...")
        sys.exit(0)
