# Example 9: Quadcopter Control in Gazebo

[![Quadcopter Control Demo](https://img.youtube.com/vi/buN6RT3Y99k/0.jpg)](https://youtu.be/buN6RT3Y99k)

Watch: [Quadcopter Control in Gazebo with ROS-MCP](https://youtu.be/buN6RT3Y99k)

This example demonstrates how to fly an **X3 quadcopter drone** inside **Ignition Gazebo Fortress** from natural-language prompts routed through the **ROS-MCP Server**. The default world is a clean minimal space with the X3 model, a flat floor, and a red marker cube for orientation.

Takeoff, hover, directional flight, and landing are all driven from the MCP client → `rosbridge` → `ros_gz_bridge` → Ignition's `MulticopterVelocityControl` plugin.

## 📋 Tested On

  * **OS:** Ubuntu 22.04 LTS (arm64)
  * **ROS Distro:** ROS 2 Humble
  * **Simulator:** Ignition Gazebo Fortress (6.16.0)
  * **Python Manager:** `uv`

## 🛠️ Prerequisites

```bash
sudo apt update
sudo apt install ros-humble-ros-gz            # ROS 2 ↔ Ignition bridge
sudo apt install ros-humble-rosapi            # topic/service introspection
sudo apt install ros-humble-rosbridge-server  # WebSocket transport for MCP
```

The first time you launch the world, Gazebo downloads the X3 model from [Fuel](https://fuel.gazebosim.org/) (~2 MB, internet required).

## 📦 Installation

```bash
cd 9_quadcopter_control
uv venv
source .venv/bin/activate
uv sync
```

## 🚀 How to Run

### 1. Launch simulation + bridges

```bash
source /opt/ros/humble/setup.bash
source .venv/bin/activate

ros2 launch quadcopter_sim.launch.py
```

This loads `quadcopter_minimal.sdf` by default. To launch the larger/scenic world instead:

```bash
ros2 launch quadcopter_sim.launch.py world:=quadcopter.sdf
```

This starts four processes:

| Process            | What it does                                                       |
| ------------------ | ------------------------------------------------------------------ |
| `ign gazebo`       | Ignition Fortress loading `quadcopter_minimal.sdf` (X3 + velocity control) |
| `parameter_bridge` | Bridges Ignition ↔ ROS 2 topics (see topic map below)              |
| `rosbridge_server` | WebSocket on `ws://localhost:9090` — the MCP transport             |
| `rosapi`           | Lets MCP introspect topics / services                              |

### 2. Start the MCP client

Connect any MCP client (Claude Desktop, [robot-mcp-client](https://github.com/robotmcp/robot-mcp-client), Goose, …) to the rosbridge WebSocket at `ws://localhost:9090`.

## 🗺️ Topic Map

| ROS 2 topic           | Direction | ROS type                 | Ignition topic               |
| --------------------- | --------- | ------------------------ | ---------------------------- |
| `/quadcopter/enable`  | ROS → GZ  | `std_msgs/Bool`          | `/X3/enable`                 |
| `/quadcopter/cmd_vel` | ROS → GZ  | `geometry_msgs/Twist`    | `/X3/gazebo/command/twist`   |
| `/quadcopter/odom`    | GZ → ROS  | `nav_msgs/Odometry`      | `/model/x3/odometry`         |
| `/tf`                 | GZ → ROS  | `tf2_msgs/TFMessage`     | `/model/x3/pose`             |
| `/clock`              | GZ → ROS  | `rosgraph_msgs/Clock`    | `/clock`                     |

**The flight is a 2-step dance:** publish `true` to `/quadcopter/enable` once to arm the controller, then stream `geometry_msgs/Twist` messages on `/quadcopter/cmd_vel`. `linear.z > 0` climbs, `linear.x` is forward, `angular.z` is yaw, everything in body frame.

## 🤖 Sample Prompts

Once the MCP client is connected:

### Flight control

> "Arm the quadcopter and take off to 5 meters."

> "Hover in place."

> "Fly forward at 1 m/s for 4 seconds."

> "Yaw 90 degrees to the right."

> "Descend and land."

> "Disarm the controller."

### Introspection

> "List all available topics."

> "What's the current altitude of the quadcopter?"

> "What message type does `/quadcopter/cmd_vel` expect?"

## 🧪 Quick Manual Test (without MCP)

To sanity-check the stack from the command line in a second terminal:

```bash
source /opt/ros/humble/setup.bash

# Arm
ros2 topic pub -1 /quadcopter/enable std_msgs/msg/Bool '{data: true}'

# Climb at 1 m/s (Ctrl-C after a few seconds)
ros2 topic pub -r 10 /quadcopter/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {z: 1.0}}'

# Read altitude
ros2 topic echo --once /quadcopter/odom --field pose.pose.position
```

Expected: `z` rises by roughly `commanded_z_velocity × seconds_commanded`.

## 📁 Files

```
9_quadcopter_control/
├── quadcopter_minimal.sdf      # Default clean world: floor + red marker + X3 controls
├── quadcopter.sdf              # Larger world: Baylands/fallback ground + X3 controls
├── quadcopter_sim.launch.py    # Starts gazebo + bridge + rosbridge + rosapi
├── pyproject.toml              # uv/pip dependencies for the MCP side
└── README.md
```

## 🔧 Tuning notes

The velocity controller gains in the SDF worlds come from the upstream Fortress demo and are conservative. If the quadcopter feels sluggish or oscillates, tune these in the `MulticopterVelocityControl` plugin block:

```xml
<velocityGain>2.7 2.7 2.7</velocityGain>
<attitudeGain>2 3 0.15</attitudeGain>
<angularRateGain>0.4 0.52 0.18</angularRateGain>
<maximumLinearAcceleration>2 2 2</maximumLinearAcceleration>
```
