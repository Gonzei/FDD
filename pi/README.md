# Raspberry Pi 5 (on the drone)

The Pi 5 does two jobs:

1. **Stream video** from the OV9281 camera to the laptop over Wi-Fi.
2. **Bridge commands** between the laptop (Wi-Fi) and the flight controller (UART).

It doesn't make decisions. The laptop does that.

## Setup checklist

### 1. Operating system
- Flash **Raspberry Pi OS Lite (64-bit)** with Raspberry Pi Imager.
- In Imager's settings, set the hostname, username, Wi-Fi network and enable SSH, so the Pi can be reached without a screen.

### 2. Camera (OV9281)
- Connect it with a **22-pin to 15-pin camera cable** (the Pi 5 uses the narrow 22-pin connector).
- In `/boot/firmware/config.txt`:
  - set `camera_auto_detect=0`
  - add `dtoverlay=ov9281`, or `dtoverlay=ov9281,cam0` if the camera is in the CAM0 port
- Reboot, then check that the camera is detected with `rpicam-hello --list-cameras`.

### 3. Video stream to the laptop
- **`rpicam-vid`** (built in) captures and encodes H.264 and can send it over the network.
- **MediaMTX** (optional) serves the stream as RTSP, which OpenCV on the laptop opens directly.
- Start with a modest resolution and frame rate (for example 640×400 at 30 fps), then measure the delay.

### 4. Flight controller link (later, roadmap step 6)
- Enable the hardware UART with `sudo raspi-config` → Interface Options → Serial Port: **no** login shell, **yes** serial hardware.
- Wire Pi GPIO14 (TX) → FC RX, GPIO15 (RX) → FC TX, and GND → GND. Both sides are 3.3 V logic.
- Run **mavlink-router** (or **MAVProxy**) to forward MAVLink between the UART and UDP on Wi-Fi.

### 5. Power on the drone
- Power the Pi from a **5 V BEC rated for at least 5 A**, fed by the drone battery.
- Undervoltage causes random reboots, so check for warnings in `dmesg`.
- Fit a heatsink or the official Active Cooler.
