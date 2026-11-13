# FDD: Face Detecting Drone

A drone that finds a person, follows them, and, if they're facing away (for example, running from it), flies around them until it's in front and can detect their face.

## Architecture

The laptop is the brain. The drone carries a camera and a Raspberry Pi Zero 2 W that streams video, a Raspberry Pi Pico 2 W as the Wi-Fi command link, and a flight controller that keeps it stable.

```
OV9281 camera ─(ribbon)─► Pi Zero 2 W ──(Wi-Fi video)──► Laptop
                                                           │  detection, pose, tracking,
                                                           │  prediction, decisions
Pico 2 W on drone ◄──────────(Wi-Fi commands)──────────────┘
     │
     └──(UART wire)──► Flight controller ──► motors
```

- **Video:** the camera is a Raspberry Pi CSI (ribbon cable) camera, which the Pico 2 W can't connect to. A **Raspberry Pi Zero 2 W** reads the camera, compresses the video to H.264 in hardware, and streams it over Wi-Fi to the laptop. (The Zero 2 W could also take over the Pico's bridge role later, which would leave one fewer board on the drone.)
- **Flight control:** a flight controller running **ArduPilot** keeps the drone stable. The Pico does not fly the drone.
- **Pico 2 W role:** a transparent Wi-Fi-to-serial bridge. The laptop speaks MAVLink (the flight controller's protocol) using a full Python library, and the Pico passes the bytes between Wi-Fi and the flight controller's UART.
- **Manual override:** a normal RC transmitter stays connected to the flight controller at all times.

## Camera

**Chosen: 1MP OV9281 monochrome global shutter camera (120 fps, 79° FOV).**

- **Global shutter** captures the whole frame at once, so drone vibration and fast turns don't warp the image the way a rolling shutter does.
- **120 fps** gives sharp frames of fast-moving people. Stream at a lower frame rate (for example 30 fps) to save Wi-Fi bandwidth.
- **The trade-off is that it's monochrome.** Face detection and pose estimation work well in grayscale. Telling people apart by clothing color is weaker, which matters only when several people are in frame.
- **Setup:** enable it on the Zero 2 W with `dtoverlay=ov9281` in `/boot/firmware/config.txt`. The Zero 2 W has the narrow 22-pin camera connector, so it needs a **Pi Zero camera cable (22-pin to 15-pin)**. The cable that comes with the camera usually won't fit.

**Spare: Arducam OV5647 day-night camera (5MP, IR-cut, IR LEDs).** It's color, with a rolling shutter. Keep it for later night-vision experiments. It's heavier and uses more power because of the IR LEDs.

## How it gets in front of a person

A face detector can't see someone from behind, so the system tracks the whole body first:

1. **Person detection:** find the body from any angle.
2. **Tracking:** keep the same ID on the same person across frames.
3. **Pose estimation:** use keypoints (nose, eyes, ears, shoulders) to decide whether the person is facing the drone, side-on, or facing away.
4. **Prediction:** a Kalman filter estimates where the person is heading, so the drone aims for where they *will be*.
5. **Orbit:** move sideways, yaw to keep them centered, and hold distance, all at once, to swing around to their front.
6. **Face detection:** run once the drone is in front.

These steps form a state machine: **search → acquire person → follow → orbit to front → detect face → hold**.

## Libraries

### Pico 2 W (MicroPython, all built in)

Flash the **RPI_PICO2_W** MicroPython firmware build. It's a different build from the original Pico W's.

| Module | Purpose |
|---|---|
| `network` | Connect to Wi-Fi |
| `socket` | Send/receive UDP packets |
| `machine.UART` | Talk to the flight controller |
| `asyncio` | Handle both directions at once |

### Pi Zero 2 W (Raspberry Pi OS Lite)

| Tool | Purpose |
|---|---|
| `rpicam-vid` | Capture from the camera and stream H.264 over the network (built in) |
| Picamera2 | Python camera control, if more than plain streaming is needed |
| MediaMTX (optional) | Serve the stream as RTSP so OpenCV on the laptop can open it easily |

### Laptop (Python)

| Purpose | Library |
|---|---|
| Video input, drawing | OpenCV (`opencv-python`) |
| Face detection + pose | MediaPipe (use the Tasks API) |
| Person detection + tracking | Ultralytics YOLO (pose models, built-in ByteTrack) |
| Motion prediction | FilterPy |
| Control | simple-pid |
| Talking to the drone | pymavlink (or MAVSDK-Python) |

### Simulation and tools

- **ArduPilot SITL** + **Gazebo**: simulated drone and world
- **QGroundControl** or **Mission Planner**: ground station

## Roadmap

1. **Face + pose with the laptop webcam** (OpenCV, MediaPipe). Label a person as facing / side / away.
2. **Person detection + tracking** (Ultralytics YOLO). The same ID stays on a person as they move.
3. **Prediction + control logic** (FilterPy, simple-pid). Print commands like "orbit left, yaw right" on screen.
4. **Pico 2 W Wi-Fi basics** (`network`, `socket`). Send messages from the laptop and blink the LED on command.
5. **Simulated drone** (ArduPilot SITL, Gazebo, pymavlink). Fly the simulated drone with the face-following logic, using the laptop camera as a stand-in.
6. **Wireless camera** (OV9281 + Pi Zero 2 W, `rpicam-vid`). Stream to the laptop, feed it into the step 1–3 code, and measure the delay.
7. **Pico as a bridge.** Laptop → Wi-Fi → Pico → UART → flight controller on the desk, **propellers off**. Confirm it responds in QGroundControl.
8. **Build and fly the drone manually** with ArduPilot and an RC transmitter.
9. **Connect everything**: open field, walking speed, RC override in hand.

Steps 1–4 need only a laptop, a webcam and the Pico.

## Things to plan for

- **Wi-Fi drops:** configure ArduPilot's failsafe so that a lost link makes the drone hover, land or return home, instead of continuing on its last command.
- **Latency:** video to the laptop, processing, and a command back can take a few hundred milliseconds. That's fine for following someone walking, but hard for orbiting a runner. Measure it in step 6.
- **Range:** the Pico's and Zero 2 W's Wi-Fi reach tens of meters, so the laptop has to stay nearby. A laptop hotspot or a travel router can put the Zero 2 W and the Pico on one network.
- **Speed:** a running person moves at about 3–6 m/s, and the drone must be noticeably faster to orbit them.
- **Obstacles:** while orbiting, the drone flies sideways and backwards into space its camera can't see. Test only in wide-open areas.

## Further reading

- [ArduPilot docs](https://ardupilot.org): "Companion Computers" and "SITL" sections
- [MAVSDK docs](https://mavsdk.mavlink.io): Python examples, especially offboard control
- [Ultralytics docs](https://docs.ultralytics.com): Pose and Track pages
- [MediaPipe docs](https://ai.google.dev/edge/mediapipe): Pose Landmarker and Face Detector
- [OpenCV Python tutorials](https://docs.opencv.org)
- [Raspberry Pi camera docs](https://www.raspberrypi.com/documentation/computers/camera_software.html): `rpicam-vid` streaming and Picamera2
- *Kalman and Bayesian Filters in Python* by Roger Labbe (free online)

## Safety and rules

Check local drone regulations before flying outdoors. In the US, this means FAA registration and the TRUST test for recreational pilots. A drone that tracks faces also raises privacy concerns, so only track people who have agreed to it.
