# hand_teleop

A ROS 2 package for teleoperation of a robot arm using hand gestures captured via webcam.  
Built with [MediaPipe](https://mediapipe.dev/) for hand tracking and designed for modularity — easy to extend with new gesture commands or robot backends.

---

## ✋ What it does

| Node | Role |
|------|------|
| `gesture_node` | Reads webcam, detects hands via MediaPipe, publishes gesture commands |
| `arm_controller_node` | Subscribes to gesture commands and drives the robot arm |

- **Left hand** → finger count selects which joint/motor to control (1 finger = joint 0, 2 = joint 1, …)
- **Right hand** → fist gesture + move up/down sends increment/decrement commands to the selected joint

---

## 📁 Project Structure

```
hand_teleop/                        ← ROS 2 workspace root
├── src/
│   └── hand_teleop/                ← ROS 2 package
│       ├── hand_teleop/            ← Python package (importable modules)
│       │   ├── __init__.py
│       │   ├── gesture/
│       │   │   ├── __init__.py
│       │   │   ├── finger_counter.py       ← left hand: counts fingers
│       │   │   └── right_hand_tracker.py   ← right hand: direction + fist
│       │   └── controller/
│       │       ├── __init__.py
│       │       └── motor_controller.py     ← hardware interface (swap for real hw)
│       ├── nodes/
│       │   ├── gesture_node.py     ← ROS 2 node: camera → gesture topic
│       │   └── arm_controller_node.py  ← ROS 2 node: gesture topic → robot
│       ├── launch/
│       │   └── teleop.launch.py    ← launches both nodes together
│       ├── config/
│       │   └── params.yaml         ← tunable parameters (thresholds, camera id…)
│       ├── msg/                    ← custom ROS 2 messages (if needed later)
│       ├── resource/
│       │   └── hand_teleop
│       ├── test/
│       │   └── test_finger_counter.py
│       ├── package.xml
│       ├── setup.py
│       └── setup.cfg
├── .gitignore
├── CONTRIBUTING.md
├── Mechanical
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- ROS 2 (Humble / Iron / Jazzy)
- Python 3.10+
- A webcam

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/hand_teleop.git
cd hand_teleop
```

### 2. Install Python dependencies

```bash
pip install mediapipe opencv-python
```

### 3. Build the workspace

```bash
cd hand_teleop          # workspace root
colcon build
source install/setup.bash
```

### 4. Run

```bash
# Launch both nodes at once
ros2 launch hand_teleop teleop.launch.py

# Or run nodes individually
ros2 run hand_teleop gesture_node
ros2 run hand_teleop arm_controller_node
```

### 5. Calibrate

With the application running, hold your **right hand still** in the neutral position and press **`c`** to set the zero line.

---

## 🎮 Controls

| Gesture | Action |
|---------|--------|
| Left hand — 1 finger | Select joint 0 |
| Left hand — 2 fingers | Select joint 1 |
| Left hand — 3 fingers | Select joint 2 |
| Left hand — 4 fingers | Select joint 3 |
| Right hand — fist + move **up** | Increment selected joint |
| Right hand — fist + move **down** | Decrement selected joint |
| Keyboard `c` | Calibrate neutral (zero) line |
| Keyboard `q` | Quit |

---

## ⚙️ Configuration

Edit `config/params.yaml` to tune behaviour without touching code:

```yaml
gesture_node:
  ros__parameters:
    camera_id: 0          # webcam index
    detection_confidence: 0.5
    tracking_confidence: 0.5

arm_controller_node:
  ros__parameters:
    neutral_threshold: 0.05   # dead-zone around zero line (normalized)
    step_size: 1              # position units per command
```

---

## 🗺️ ROS 2 Topics

| Topic | Type | Published by | Subscribed by |
|-------|------|--------------|---------------|
| `/gesture/selected_joint` | `std_msgs/Int32` | `gesture_node` | `arm_controller_node` |
| `/gesture/direction` | `std_msgs/String` | `gesture_node` | `arm_controller_node` |
| `/gesture/is_fist` | `std_msgs/Bool` | `gesture_node` | `arm_controller_node` |

---

## 🛠️ Roadmap

- [In progress] Hand gesture detection (MediaPipe)
- [ ] Left/right hand identification by label
- [ ] Motor mock controller
- [ ] ROS 2 nodes wired up
- [ ] Real robot arm interface
- [ ] Custom ROS 2 message `GestureCmd`
- [ ] Launch file with parameters
- [ ] Unit tests

---

