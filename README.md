# FDD: Face Detecting Drone

A drone that finds a person, follows them, and, if they're facing away (for example, running from it), flies around them until it's in front and can detect their face.

## Architecture

A **Raspberry Pi 5** on the drone streams camera video to a **laptop** over Wi-Fi. The laptop does all the vision and decision-making and sends commands back. The Pi passes those commands to a **flight controller**, which keeps the drone stable.

```
OV9281 camera ─(ribbon)─► Raspberry Pi 5 ──(Wi-Fi video)──► Laptop (the brain)
                               ▲                              │  detection, pose, tracking,
                               │                              │  prediction, decisions
                               └──────(Wi-Fi commands)────────┘
                               │
                               └──(UART wire)──► Flight controller ──► motors
```

- **Raspberry Pi 5:** streams video and bridges MAVLink (the flight controller's protocol) between Wi-Fi and its UART. Setup notes are in [pi/README.md](pi/README.md).
- **Laptop:** runs detection, tracking, pose, prediction and control in Python. Code lives in [laptop/](laptop/).
- **Flight controller:** runs **ArduPilot** and keeps the drone stable. The Pi doesn't fly the drone.
- **Manual override:** a normal RC transmitter stays connected to the flight controller at all times.

## Project layout

```
FDD/
├── README.md          this file
├── laptop/            runs on the laptop: vision, tracking, control
│   └── requirements.txt
└── pi/                runs on the Raspberry Pi 5: camera stream, MAVLink bridge
    └── README.md      Pi setup checklist
```

## Hardware

| Part | Notes |
|---|---|
| Raspberry Pi 5 (16 GB) | Built-in Wi-Fi (2.4 / 5 GHz). Needs a heatsink or Active Cooler. |
| OV9281 global shutter camera | The chosen camera, see below |
| 22-pin to 15-pin camera cable | The Pi 5 uses the narrow camera connector |
| 5 V BEC, 5 A or more | Powers the Pi from the drone battery |
| ArduPilot flight controller + GPS | Keeps the drone stable, with failsafes |
| Frame, motors, ESCs, battery | Sized to carry the Pi 5 and camera (about 100 g extra) |
| RC transmitter + receiver | Manual override |

## Camera

**Chosen: 1MP OV9281 monochrome global shutter camera (120 fps, 79° FOV).**

- **Global shutter** captures the whole frame at once, so drone vibration and fast turns don't warp the image the way a rolling shutter does.
- **120 fps** gives sharp frames of fast-moving people. Stream at a lower frame rate (for example 30 fps) to save Wi-Fi bandwidth.
- **The trade-off is that it's monochrome.** Face detection and pose estimation work well in grayscale. Telling people apart by clothing color is weaker, which matters only when several people are in frame.

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

### Raspberry Pi 5 (Raspberry Pi OS Lite, 64-bit)

| Tool | Purpose |
|---|---|
| `rpicam-vid` | Capture from the camera and stream H.264 over the network (built in) |
| Picamera2 | Python camera control, if more than plain streaming is needed |
| MediaMTX (optional) | Serve the stream as RTSP so OpenCV on the laptop can open it easily |
| mavlink-router or MAVProxy | Forward MAVLink between the flight controller's UART and Wi-Fi |

### Laptop (Python), listed in [laptop/requirements.txt](laptop/requirements.txt)

| Purpose | Library |
|---|---|
| Video input, drawing | OpenCV (`opencv-python`) |
| Face detection + pose | MediaPipe (use the Tasks API) |
| Person detection + tracking | Ultralytics YOLO (pose models, built-in ByteTrack) |
| Motion prediction | FilterPy |
| Control | simple-pid |
| Talking to the drone | pymavlink |

### Simulation and tools

- **ArduPilot SITL** + **Gazebo**: simulated drone and world
- **QGroundControl** or **Mission Planner**: ground station

## Roadmap

1. **Face + pose with the laptop webcam** (OpenCV, MediaPipe). Label a person as facing / side / away.
2. **Person detection + tracking** (Ultralytics YOLO). The same ID stays on a person as they move.
3. **Prediction + control logic** (FilterPy, simple-pid). Print commands like "orbit left, yaw right" on screen.
4. **Pi 5 + camera stream** (`rpicam-vid`). Stream the OV9281 to the laptop, run the step 1–3 code on it, and measure the delay. No drone needed.
5. **Simulated drone** (ArduPilot SITL, Gazebo, pymavlink). Fly the simulated drone with the face-following logic.
6. **Pi as the MAVLink bridge.** Laptop → Wi-Fi → Pi 5 → UART → flight controller on the desk, **propellers off**. Confirm it responds in QGroundControl.
7. **Build and fly the drone manually** with ArduPilot and an RC transmitter.
8. **Connect everything**: open field, walking speed, RC override in hand.

Steps 1–3 need only a laptop and a webcam.

**Later:** the Pi 5 can run some of the vision itself, and much more with an AI HAT+ accelerator. That would move the brain onto the drone and take the laptop out of the control loop.

## Things to plan for

- **Wi-Fi drops:** configure ArduPilot's failsafe so that a lost link makes the drone hover, land or return home, instead of continuing on its last command.
- **Latency:** video to the laptop, processing, and a command back can take a few hundred milliseconds. That's fine for following someone walking, but hard for orbiting a runner. Measure it in step 4.
- **Range:** the Pi's Wi-Fi reaches tens of meters, so the laptop has to stay nearby. 5 GHz has less lag and 2.4 GHz reaches farther.
- **Power:** the Pi 5 must get a steady 5 V. Undervoltage causes reboots mid-flight.
- **Speed:** a running person moves at about 3–6 m/s, and the drone must be noticeably faster to orbit them.
- **Obstacles:** while orbiting, the drone flies sideways and backwards into space its camera can't see. Test only in wide-open areas.

## Further reading

- [ArduPilot docs](https://ardupilot.org): "Companion Computers" and "SITL" sections
- [Raspberry Pi camera docs](https://www.raspberrypi.com/documentation/computers/camera_software.html): `rpicam-vid` streaming and Picamera2
- [Ultralytics docs](https://docs.ultralytics.com): Pose and Track pages
- [MediaPipe docs](https://ai.google.dev/edge/mediapipe): Pose Landmarker and Face Detector
- [OpenCV Python tutorials](https://docs.opencv.org)
- [pymavlink docs](https://mavlink.io/en/mavgen_python/)
- *Kalman and Bayesian Filters in Python* by Roger Labbe (free online)

## Safety and rules

Check local drone regulations before flying outdoors. In the US, this means FAA registration and the TRUST test for recreational pilots. A drone that tracks faces also raises privacy concerns, so only track people who have agreed to it.
