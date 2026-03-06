# TugBot Control Workflows

Step-by-step workflows for common TugBot simulation tasks using ros-mcp-server.

---

## Table of Contents

1. [Session Startup Workflow](#session-startup-workflow)
2. [Basic Motion Control](#basic-motion-control)
3. [Sensor Data Collection](#sensor-data-collection)
4. [Vision & Camera](#vision--camera)
5. [Navigation with Nav2](#navigation-with-nav2)
6. [Obstacle Avoidance (Manual)](#obstacle-avoidance-manual)
7. [SLAM Mapping](#slam-mapping)
8. [Multi-Step Autonomous Demo](#multi-step-autonomous-demo)

---

## Session Startup Workflow

Always run this checklist at the start of a session to verify everything is working.

### Checklist

```
# 1. Connect to rosbridge
connect_to_robot()
# Expected: "Successfully connected to robot at 127.0.0.1:9090"

# 2. Verify ROS 2
detect_ros_version()
# Expected: ROS 2, Humble or Jazzy

# 3. List all available topics
get_topics()
# Expected: /cmd_vel, /odom, /scan, /camera/image_raw, /imu, /clock

# 4. Verify data is flowing from sensors
subscribe_once(topic="/odom", msg_type="nav_msgs/msg/Odometry", timeout=5.0)
subscribe_once(topic="/scan", msg_type="sensor_msgs/msg/LaserScan", timeout=5.0)

# 5. Check all running nodes
get_nodes()
# Expected: ros_gz_bridge, rosbridge_websocket, plus TugBot nodes
```

If step 1 fails → rosbridge not running → start it in Terminal 3
If step 3 missing topics → ros-gz-bridge not running → start it in Terminal 2
If step 4 times out → Gazebo paused → press Play in Gazebo GUI

---

## Basic Motion Control

### Move forward for 2 seconds

```
# Publish for a duration using a sequence
publish_for_durations(
  topic="/cmd_vel",
  msg_type="geometry_msgs/msg/Twist",
  messages=[
    {"linear": {"x": 0.3}, "angular": {"z": 0.0}},   # Move forward
    {"linear": {"x": 0.0}, "angular": {"z": 0.0}}     # Stop
  ],
  durations=[2.0, 0.5]
)
```

### Turn 90 degrees left (counter-clockwise)

At 0.5 rad/s, a 90° turn takes π/2 ÷ 0.5 ≈ 3.14 seconds:

```
publish_for_durations(
  topic="/cmd_vel",
  msg_type="geometry_msgs/msg/Twist",
  messages=[
    {"linear": {"x": 0.0}, "angular": {"z": 0.5}},   # Turn left
    {"linear": {"x": 0.0}, "angular": {"z": 0.0}}     # Stop
  ],
  durations=[3.14, 0.5]
)
```

### Turn 90 degrees right (clockwise)

```
publish_for_durations(
  topic="/cmd_vel",
  msg_type="geometry_msgs/msg/Twist",
  messages=[
    {"linear": {"x": 0.0}, "angular": {"z": -0.5}},  # Turn right
    {"linear": {"x": 0.0}, "angular": {"z": 0.0}}     # Stop
  ],
  durations=[3.14, 0.5]
)
```

### Drive a square pattern

```
publish_for_durations(
  topic="/cmd_vel",
  msg_type="geometry_msgs/msg/Twist",
  messages=[
    {"linear": {"x": 0.4}},                           # Side 1
    {"angular": {"z": 0.8}},                          # Turn 90° (~2s at 0.8 rad/s)
    {"linear": {"x": 0.4}},                           # Side 2
    {"angular": {"z": 0.8}},                          # Turn 90°
    {"linear": {"x": 0.4}},                           # Side 3
    {"angular": {"z": 0.8}},                          # Turn 90°
    {"linear": {"x": 0.4}},                           # Side 4
    {}                                                 # Stop
  ],
  durations=[2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 0.5]
)
```

### Drive then check position

```
# Get initial position
subscribe_once(topic="/odom", msg_type="nav_msgs/msg/Odometry", timeout=5.0)

# Drive forward 1 meter (at 0.3 m/s for 3.3 seconds)
publish_for_durations(
  topic="/cmd_vel",
  msg_type="geometry_msgs/msg/Twist",
  messages=[
    {"linear": {"x": 0.3}},
    {}
  ],
  durations=[3.3, 0.5]
)

# Check new position
subscribe_once(topic="/odom", msg_type="nav_msgs/msg/Odometry", timeout=5.0)
```

---

## Sensor Data Collection

### Read LIDAR scan — distance to obstacles

```
subscribe_once(topic="/scan", msg_type="sensor_msgs/msg/LaserScan", timeout=5.0)
```

The response contains `ranges[]` — an array of distances. Key indices:
- Middle of array → straight ahead
- First element → far left
- Last element → far right

Collect multiple scans over time:

```
subscribe_for_duration(
  topic="/scan",
  msg_type="sensor_msgs/msg/LaserScan",
  duration=5,
  max_messages=5,
  throttle_rate_ms=1000
)
```

### Read IMU data

```
subscribe_once(topic="/imu", msg_type="sensor_msgs/msg/Imu", timeout=5.0)
```

Key fields:
- `angular_velocity.z` — Current yaw rate (rotation speed)
- `linear_acceleration.x` — Forward acceleration
- `orientation` — Current orientation (quaternion)

### Monitor odometry continuously

```
subscribe_for_duration(
  topic="/odom",
  msg_type="nav_msgs/msg/Odometry",
  duration=10,
  max_messages=20,
  throttle_rate_ms=500
)
```

### Read joint states

```
subscribe_once(topic="/joint_states", msg_type="sensor_msgs/msg/JointState", timeout=5.0)
```

This shows wheel positions and velocities for all four TugBot wheels.

---

## Vision & Camera

### Capture a camera frame

```
subscribe_once(
  topic="/camera/image_raw",
  msg_type="sensor_msgs/msg/Image",
  timeout=15.0,
  expects_image="true"
)
```

### Analyze the captured frame

```
analyze_previously_received_image(image_path="./camera/received_image.jpeg")
```

Ask Claude to describe what the robot "sees" — this enables vision-guided behavior.

### Full vision-guided workflow

```
# 1. Check environment visually
subscribe_once(
  topic="/camera/image_raw",
  msg_type="sensor_msgs/msg/Image",
  timeout=15.0,
  expects_image="true"
)
analyze_previously_received_image(image_path="./camera/received_image.jpeg")

# 2. Check what's ahead with LIDAR
subscribe_once(topic="/scan", msg_type="sensor_msgs/msg/LaserScan", timeout=5.0)

# 3. Based on camera/lidar data, decide on movement
# (Agent decides: forward, turn, or stay)
publish_once(
  topic="/cmd_vel",
  msg_type="geometry_msgs/msg/Twist",
  msg={"linear": {"x": 0.2}, "angular": {"z": 0.0}}
)
```

---

## Navigation with Nav2

Nav2 must be launched separately. After TugBot Gazebo is running:

```bash
# Terminal 4: Launch Nav2 navigation stack
ros2 launch tugbot_navigation2 navigation2.launch.py
```

### Verify Nav2 is running

```
get_actions()
# Should see: /navigate_to_pose, /navigate_through_poses, /follow_path
```

### Send a navigation goal

```
send_action_goal(
  action_name="/navigate_to_pose",
  action_type="nav2_msgs/action/NavigateToPose",
  goal={
    "pose": {
      "header": {
        "frame_id": "map"
      },
      "pose": {
        "position": {"x": 2.0, "y": 1.0, "z": 0.0},
        "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
      }
    }
  },
  timeout=120.0
)
```

### Monitor navigation progress

```
# Check action status
get_action_status(action_name="/navigate_to_pose")

# Monitor position while navigating
subscribe_for_duration(
  topic="/odom",
  msg_type="nav_msgs/msg/Odometry",
  duration=30,
  max_messages=30,
  throttle_rate_ms=1000
)
```

### Cancel navigation

```
cancel_action_goal(
  action_name="/navigate_to_pose",
  goal_id="<goal_id_from_send_action_goal>"
)
```

### Navigate through multiple waypoints

```
send_action_goal(
  action_name="/navigate_through_poses",
  action_type="nav2_msgs/action/NavigateThroughPoses",
  goal={
    "poses": [
      {
        "header": {"frame_id": "map"},
        "pose": {
          "position": {"x": 1.0, "y": 0.0, "z": 0.0},
          "orientation": {"w": 1.0}
        }
      },
      {
        "header": {"frame_id": "map"},
        "pose": {
          "position": {"x": 2.0, "y": 2.0, "z": 0.0},
          "orientation": {"w": 1.0}
        }
      },
      {
        "header": {"frame_id": "map"},
        "pose": {
          "position": {"x": 0.0, "y": 0.0, "z": 0.0},
          "orientation": {"w": 1.0}
        }
      }
    ]
  },
  timeout=300.0
)
```

---

## Obstacle Avoidance (Manual)

Simple reactive obstacle avoidance using LIDAR data without Nav2:

```
# 1. Get current LIDAR scan
subscribe_once(topic="/scan", msg_type="sensor_msgs/msg/LaserScan", timeout=5.0)

# Inspect the ranges[] array:
# - If center ranges are small (< 1.0m): obstacle ahead, need to turn
# - If clear: move forward

# Example: if obstacle detected ahead, turn and proceed
# (Agent decides based on scan data)

# If obstacle < 1.0m ahead — turn right
publish_for_durations(
  topic="/cmd_vel",
  msg_type="geometry_msgs/msg/Twist",
  messages=[
    {"angular": {"z": -0.5}},    # Turn right
    {"linear": {"x": 0.3}},      # Move forward
    {}                            # Stop
  ],
  durations=[2.0, 1.5, 0.5]
)

# 2. Check new scan after maneuver
subscribe_once(topic="/scan", msg_type="sensor_msgs/msg/LaserScan", timeout=5.0)
```

---

## SLAM Mapping

Launch SLAM Toolbox alongside the simulation:

```bash
# Terminal 4: Launch SLAM
ros2 launch tugbot_slam slam_toolbox.launch.py
```

With SLAM running, additional topics appear:
- `/map` — Built occupancy grid map
- `/slam_toolbox/scan_visualization` — Processed scan for SLAM

### Read the current map

```
subscribe_once(topic="/map", msg_type="nav_msgs/msg/OccupancyGrid", timeout=10.0)
```

### Drive to build the map

Move the robot around the warehouse to have SLAM build the map:

```
# Drive in a pattern to explore the warehouse
publish_for_durations(
  topic="/cmd_vel",
  msg_type="geometry_msgs/msg/Twist",
  messages=[
    {"linear": {"x": 0.3}},       # Explore forward
    {"angular": {"z": 0.5}},      # Look left
    {"linear": {"x": 0.3}},       # Continue
    {"angular": {"z": -0.5}},     # Look right
    {"linear": {"x": 0.3}},       # Continue
    {}                             # Stop
  ],
  durations=[3.0, 2.0, 3.0, 2.0, 3.0, 0.5]
)
```

---

## Multi-Step Autonomous Demo

This is a comprehensive demo that exercises all TugBot capabilities:

```
# === PHASE 1: STARTUP CHECK ===
connect_to_robot()
detect_ros_version()
get_topics()
get_nodes()

# === PHASE 2: SENSOR BASELINE ===
# Read initial state
subscribe_once(topic="/odom", msg_type="nav_msgs/msg/Odometry", timeout=5.0)
subscribe_once(topic="/scan", msg_type="sensor_msgs/msg/LaserScan", timeout=5.0)
subscribe_once(topic="/imu", msg_type="sensor_msgs/msg/Imu", timeout=5.0)

# Capture initial view
subscribe_once(
  topic="/camera/image_raw",
  msg_type="sensor_msgs/msg/Image",
  timeout=15.0,
  expects_image="true"
)
analyze_previously_received_image(image_path="./camera/received_image.jpeg")

# === PHASE 3: MOTION DEMO ===
# Drive a square
publish_for_durations(
  topic="/cmd_vel",
  msg_type="geometry_msgs/msg/Twist",
  messages=[
    {"linear": {"x": 0.3}},
    {"angular": {"z": 0.8}},
    {"linear": {"x": 0.3}},
    {"angular": {"z": 0.8}},
    {"linear": {"x": 0.3}},
    {"angular": {"z": 0.8}},
    {"linear": {"x": 0.3}},
    {"angular": {"z": 0.8}},
    {}
  ],
  durations=[2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 0.5]
)

# === PHASE 4: POST-MOTION CHECK ===
subscribe_once(topic="/odom", msg_type="nav_msgs/msg/Odometry", timeout=5.0)
subscribe_once(topic="/scan", msg_type="sensor_msgs/msg/LaserScan", timeout=5.0)

# Final camera view
subscribe_once(
  topic="/camera/image_raw",
  msg_type="sensor_msgs/msg/Image",
  timeout=15.0,
  expects_image="true"
)
analyze_previously_received_image(image_path="./camera/received_image.jpeg")

# === PHASE 5: STOP SAFELY ===
publish_once(
  topic="/cmd_vel",
  msg_type="geometry_msgs/msg/Twist",
  msg={"linear": {"x": 0.0}, "angular": {"z": 0.0}}
)
```

---

## Safety Guidelines

1. **Always stop before reading sensors** — Avoid interpreting sensor data while moving for better accuracy
2. **Use conservative velocities** — Start with ≤ 0.3 m/s linear, ≤ 0.5 rad/s angular
3. **Check LIDAR before moving** — Verify `ranges[]` don't show nearby obstacles
4. **Always send a stop command** after any movement sequence
5. **Watch Gazebo GUI** — Visual feedback helps catch unexpected behavior early
