---
name: ros-mcp-gazebo
description: >
  Run and operate Gazebo simulations with ROS 2 and control them through ros-mcp-server. Use this
  skill when the user wants to launch a Gazebo simulation, set up the ros-gz-bridge (ROS-Gazebo
  bridge), start rosbridge so ros-mcp-server can communicate, or interact with a simulated robot
  via AI. Also triggers for mentions of: Ignition Gazebo, gz sim, ros_gz_bridge, parameter_bridge,
  Gazebo topics, Gazebo sensors, simulated robots, robot simulation, or any request to run/test
  a ROS 2 simulation with AI. When no specific simulation is specified, default to the TugBot
  demo (see sub-skills/tugbot/).
---

# Gazebo Simulation Skill (ROS-MCP)

This skill enables you to launch Gazebo simulations, bridge Gazebo's internal topics to ROS 2 via
`ros-gz-bridge`, expose them through `rosbridge_server`, and then control and observe the simulated
robot using the `ros-mcp-server` tools via Claude or any other MCP-compatible AI client.

## Sub-Skills

| Sub-Skill | When to Use |
|-----------|-------------|
| [TugBot Demo](./sub-skills/tugbot/SKILL.md) | Default Gazebo sim demo, or when the user asks about TugBot specifically |

> **Default simulation**: If the user just wants to "test Gazebo" or "run a demo simulation", use the **TugBot sub-skill** — it is a complete, well-documented example.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│             AI Client (Claude / OpenClaw)                │
└──────────────────────┬──────────────────────────────────┘
                       │ MCP Protocol
                       ▼
┌─────────────────────────────────────────────────────────┐
│                  ros-mcp-server                          │
│         (Python, runs on client machine)                 │
└──────────────────────┬──────────────────────────────────┘
                       │ WebSocket port 9090
                       ▼
┌─────────────────────────────────────────────────────────┐
│               rosbridge_server                           │
│      (ROS 2 node — exposes topics over WebSocket)        │
└──────────────────────┬──────────────────────────────────┘
                       │ ROS 2 DDS / topics
                       ▼
┌─────────────────────────────────────────────────────────┐
│                  ros-gz-bridge                           │
│   (Translates between ROS 2 msgs ↔ Gazebo msgs)         │
└──────────────────────┬──────────────────────────────────┘
                       │ Gazebo Transport
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Gazebo Simulation (gz sim)                  │
│       (Robot model, physics, sensors, world)             │
└─────────────────────────────────────────────────────────┘
```

**Key insight**: There are two bridges in play:
1. **ros-gz-bridge** (`ros_gz_bridge`) — connects Gazebo's internal transport to ROS 2 topics
2. **rosbridge_server** — connects ROS 2 topics to WebSocket so ros-mcp-server can reach them

Both must be running for full AI ↔ simulation communication.

---

## Quick Reference

| Topic | Reference File |
|-------|----------------|
| Installation & Setup | [setup.md](./reference/setup.md) |
| ros-gz-bridge Configuration | [ros-gz-bridge.md](./reference/ros-gz-bridge.md) |
| Troubleshooting | [troubleshooting.md](./reference/troubleshooting.md) |

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| ROS 2 Humble or Jazzy | Humble + Gazebo Fortress/Garden; Jazzy + Gazebo Harmonic |
| Gazebo (gz sim) | Installed alongside ROS 2 or separately |
| `ros_gz_bridge` package | `sudo apt install ros-$ROS_DISTRO-ros-gz-bridge` |
| `rosbridge_server` package | `sudo apt install ros-$ROS_DISTRO-rosbridge-server` |
| ros-mcp-server | `pip install ros-mcp-server` or from source |

---

## Complete Setup Procedure

Follow these steps **in order** to get an AI-controllable Gazebo simulation running.

### Step 1: Source ROS 2

```bash
source /opt/ros/humble/setup.bash   # or jazzy
# If using a workspace:
source ~/ros2_ws/install/setup.bash
```

### Step 2: Launch Gazebo with Your Robot

```bash
# Example: launch your simulation
ros2 launch <your_package> <your_launch_file>.launch.py

# Or launch gz sim directly with a world file
gz sim <world_file.sdf>
```

> For the **TugBot demo** (recommended first test), see [sub-skills/tugbot/SKILL.md](./sub-skills/tugbot/SKILL.md).

### Step 3: Start ros-gz-bridge

The bridge maps Gazebo's internal topics to ROS 2 topics.

```bash
# Basic command-line bridge (replace with your robot's topic names)
ros2 run ros_gz_bridge parameter_bridge \
  /cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist \
  /odom@nav_msgs/msg/Odometry[gz.msgs.Odometry \
  /scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan
```

> **Note on message namespace**:
> - **Humble + Fortress**: use `ignition.msgs.Twist`
> - **Jazzy + Harmonic**: use `gz.msgs.Twist`

See [ros-gz-bridge.md](./reference/ros-gz-bridge.md) for YAML config and launch file patterns.

### Step 4: Start rosbridge

```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

This opens WebSocket port **9090** — the entry point for ros-mcp-server.

### Step 5: Connect via ros-mcp

In your AI client (Claude, OpenClaw):

```
connect_to_robot()           # Connects to localhost:9090
detect_ros_version()         # Confirm ROS 2
get_topics()                 # See bridged topics
```

---

## Agent Decision Logic

When the user asks to interact with a Gazebo simulation, the agent should:

1. **Check if Gazebo is running**: ask the user or run `gz sim --version` to verify
2. **Check if ros-gz-bridge is running**: look for `parameter_bridge` process or test with `get_topics()`
3. **Check if rosbridge is running**: test with `ping_robot()` or `connect_to_robot()`
4. **If any component is missing**: guide the user to start it (see setup steps above)
5. **Discover topics**: use `get_topics()` to see what the simulation exposes
6. **Interact**: use MCP tools to publish commands and subscribe to sensor data

### Auto-Diagnosis Sequence

Run this sequence to check what is and isn't running:

```
# Step 1: Test rosbridge connection
connect_to_robot(ip="127.0.0.1", port=9090)

# Step 2: Check ROS version
detect_ros_version()

# Step 3: List all bridged topics
get_topics()

# Step 4: List all nodes (should see gz_bridge, rosbridge)
get_nodes()

# Step 5: Confirm Gazebo-bridged topics exist
# Look for /cmd_vel, /odom, /scan, or robot-specific topics
```

If `get_topics()` returns an empty list or is missing expected topics, the ros-gz-bridge is not running or not configured correctly.

---

## Rosbridge Configuration Options

### Default (localhost)

```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

### Remote Access (bind to all interfaces)

```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml address:=0.0.0.0
```

### Custom Port

```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml port:=9091
```

---

## General Simulation Interaction Patterns

### Move a Robot

```
publish_once(
  topic="/cmd_vel",
  msg_type="geometry_msgs/msg/Twist",
  msg={"linear": {"x": 0.5}, "angular": {"z": 0.0}}
)
```

### Stop a Robot

```
publish_once(
  topic="/cmd_vel",
  msg_type="geometry_msgs/msg/Twist",
  msg={"linear": {"x": 0.0}, "angular": {"z": 0.0}}
)
```

### Read Odometry

```
subscribe_once(topic="/odom", msg_type="nav_msgs/msg/Odometry")
```

### Read LIDAR

```
subscribe_once(topic="/scan", msg_type="sensor_msgs/msg/LaserScan", timeout=5.0)
```

### Capture Camera Frame

```
subscribe_once(
  topic="/camera/image_raw",
  msg_type="sensor_msgs/msg/Image",
  timeout=10.0,
  expects_image="true"
)
analyze_previously_received_image(image_path="./camera/received_image.jpeg")
```

---

## ROS 2 Distro ↔ Gazebo Version Matrix

| ROS 2 Distro | Gazebo Version | Bridge Package | Msg Namespace |
|--------------|---------------|----------------|---------------|
| Humble | Fortress (default) | `ros-humble-ros-gz-bridge` | `ignition.msgs.*` |
| Humble | Garden (optional) | `ros-humble-ros-gz-bridge` | `gz.msgs.*` |
| Iron | Garden | `ros-iron-ros-gz-bridge` | `gz.msgs.*` |
| Jazzy | Harmonic | `ros-jazzy-ros-gz-bridge` | `gz.msgs.*` |

Install the bridge for your distro:

```bash
sudo apt install ros-$ROS_DISTRO-ros-gz-bridge
```

---

## Common ros-gz-bridge Topic Syntax

```bash
# Format: /ros_topic@ros_type@direction@gz_type
# Symbols: ] = ROS→Gazebo only, [ = Gazebo→ROS only, @ (both sides) = bidirectional

# Velocity command (ROS → Gazebo)
/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist

# Odometry (Gazebo → ROS)
/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry

# LIDAR scan (Gazebo → ROS)
/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan

# Camera image (Gazebo → ROS)
/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image

# IMU (Gazebo → ROS)
/imu@sensor_msgs/msg/Imu[gz.msgs.IMU

# Clock (Gazebo → ROS, needed for sim time)
/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock
```

---

## Next Steps

- **Default demo**: Run the [TugBot simulation](./sub-skills/tugbot/SKILL.md) for a complete end-to-end example
- **Bridge config**: See [ros-gz-bridge.md](./reference/ros-gz-bridge.md) for YAML and launch file approaches
- **Setup**: See [setup.md](./reference/setup.md) for full installation instructions
- **Troubleshooting**: See [troubleshooting.md](./reference/troubleshooting.md) for common issues
