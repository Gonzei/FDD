# FDD: Face Detecting Drone

A drone that finds a person, follows them, and, if they're facing away (for example, running from it), flies around them until it's in front and can detect their face.

## Architecture

The laptop is the brain. The drone carries a camera, a Raspberry Pi Pico 2 W as a Wi-Fi link, and a flight controller that keeps it stable.

```
Camera on drone ──(video)──────────────► Laptop
                                            │  detection, pose, tracking,
                                            │  prediction, decisions
Pico 2 W on drone ◄──(Wi-Fi commands)───────┘
     │
     └──(UART wire)──► Flight controller ──► motors
```

- **Video:** the Pico 2 W can't handle video, so the camera has its own link to the laptop:
  - **ESP32-CAM**: cheap and light, and streams over Wi-Fi in a format OpenCV can open directly. Easiest to start with.
  - **Analog FPV camera + video transmitter**, with a USB video receiver on the laptop: lower latency and longer range, but more parts.
- **Flight control:** a flight controller running **ArduPilot** keeps the drone stable. The Pico does not fly the drone.
- **Pico 2 W role:** a transparent Wi-Fi-to-serial bridge. The laptop speaks MAVLink (the flight controller's protocol) using a full Python library, and the Pico passes the bytes between Wi-Fi and the flight controller's UART.
- **Manual override:** a normal RC transmitter stays connected to the flight controller at all times.

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
6. **Wireless camera** (ESP32-CAM or FPV). Feed it into the step 1–3 code and measure the delay.
7. **Pico as a bridge.** Laptop → Wi-Fi → Pico → UART → flight controller on the desk, **propellers off**. Confirm it responds in QGroundControl.
8. **Build and fly the drone manually** with ArduPilot and an RC transmitter.
9. **Connect everything**: open field, walking speed, RC override in hand.

Steps 1–4 need only a laptop, a webcam and the Pico.

## Things to plan for

- **Wi-Fi drops:** configure ArduPilot's failsafe so that a lost link makes the drone hover, land or return home, instead of continuing on its last command.
- **Latency:** video to the laptop, processing, and a command back can take a few hundred milliseconds. That's fine for following someone walking, but hard for orbiting a runner. Measure it in step 6.
- **Range:** the Pico's Wi-Fi reaches tens of meters, so the laptop has to stay nearby. A laptop hotspot or a travel router can put the camera and the Pico on one network.
- **Speed:** a running person moves at about 3–6 m/s, and the drone must be noticeably faster to orbit them.
- **Obstacles:** while orbiting, the drone flies sideways and backwards into space its camera can't see. Test only in wide-open areas.

## Further reading

- [ArduPilot docs](https://ardupilot.org): "Companion Computers" and "SITL" sections
- [MAVSDK docs](https://mavsdk.mavlink.io): Python examples, especially offboard control
- [Ultralytics docs](https://docs.ultralytics.com): Pose and Track pages
- [MediaPipe docs](https://ai.google.dev/edge/mediapipe): Pose Landmarker and Face Detector
- [OpenCV Python tutorials](https://docs.opencv.org)
- *Kalman and Bayesian Filters in Python* by Roger Labbe (free online)

## Safety and rules

Check local drone regulations before flying outdoors. In the US, this means FAA registration and the TRUST test for recreational pilots. A drone that tracks faces also raises privacy concerns, so only track people who have agreed to it.
