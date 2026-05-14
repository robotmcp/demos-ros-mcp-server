# Example 9: Helicopter (Rotorcraft) Control in Gazebo

[Usage and Installation Video](https://youtu.be/buN6RT3Y99k)

This example demonstrates how to fly a **rotorcraft** inside **Ignition Gazebo Fortress** from natural-language prompts routed through the **ROS-MCP Server**. The default world is a clean minimal space with the X3 rotorcraft, a flat floor, and a red marker cube for orientation.

Takeoff, hover, directional flight, and landing are all driven from the MCP client → `rosbridge` → `ros_gz_bridge` → Ignition's `MulticopterVelocityControl` plugin.

> **Note on the name.** The craft used here is the **X3 quadrotor** from Gazebo Fuel (the same model as the built-in `multicopter_velocity_control` demo). The `9_helicopter_control` name uses *helicopter* in the broader rotorcraft sense. There is no dedicated single-main-rotor helicopter model in the open Gazebo Fortress ecosystem — ArduPilot's traditional-heli SITL frame needs a separate SITL build and is out of scope for this demo. The control surface (`cmd_vel`, `enable`) is identical to what you would use for any rotorcraft.

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
cd 9_helicopter_control
uv venv
source .venv/bin/activate
uv sync
```

## 🚀 How to Run

### 1. Launch simulation + bridges

```bash
source /opt/ros/humble/setup.bash
source .venv/bin/activate

ros2 launch helicopter_sim.launch.py
```

This loads `helicopter_minimal.sdf` by default. To launch the larger/scenic world instead:

```bash
ros2 launch helicopter_sim.launch.py world:=helicopter.sdf
```

This starts four processes:

| Process            | What it does                                                       |
| ------------------ | ------------------------------------------------------------------ |
| `ign gazebo`       | Ignition Fortress loading `helicopter_minimal.sdf` (X3 + velocity control) |
| `parameter_bridge` | Bridges Ignition ↔ ROS 2 topics (see topic map below)              |
| `rosbridge_server` | WebSocket on `ws://localhost:9090` — the MCP transport             |
| `rosapi`           | Lets MCP introspect topics / services                              |

### 2. Start the MCP client

Connect any MCP client (Claude Desktop, [robot-mcp-client](https://github.com/robotmcp/robot-mcp-client), Goose, …) to the rosbridge WebSocket at `ws://localhost:9090`.

## 🗺️ Topic Map

| ROS 2 topic           | Direction | ROS type                 | Ignition topic               |
| --------------------- | --------- | ------------------------ | ---------------------------- |
| `/helicopter/enable`  | ROS → GZ  | `std_msgs/Bool`          | `/X3/enable`                 |
| `/helicopter/cmd_vel` | ROS → GZ  | `geometry_msgs/Twist`    | `/X3/gazebo/command/twist`   |
| `/helicopter/odom`    | GZ → ROS  | `nav_msgs/Odometry`      | `/model/x3/odometry`         |
| `/tf`                 | GZ → ROS  | `tf2_msgs/TFMessage`     | `/model/x3/pose`             |
| `/clock`              | GZ → ROS  | `rosgraph_msgs/Clock`    | `/clock`                     |

**The flight is a 2-step dance:** publish `true` to `/helicopter/enable` once to arm the controller, then stream `geometry_msgs/Twist` messages on `/helicopter/cmd_vel`. `linear.z > 0` climbs, `linear.x` is forward, `angular.z` is yaw, everything in body frame.

## 🤖 Sample Prompts

Once the MCP client is connected:

### Flight control

> "Arm the helicopter and take off to 5 meters."

> "Hover in place."

> "Fly forward at 1 m/s for 4 seconds."

> "Yaw 90 degrees to the right."

> "Descend and land."

> "Disarm the controller."

### Introspection

> "List all available topics."

> "What's the current altitude of the helicopter?"

> "What message type does `/helicopter/cmd_vel` expect?"

## 🧪 Quick Manual Test (without MCP)

To sanity-check the stack from the command line in a second terminal:

```bash
source /opt/ros/humble/setup.bash

# Arm
ros2 topic pub -1 /helicopter/enable std_msgs/msg/Bool '{data: true}'

# Climb at 1 m/s (Ctrl-C after a few seconds)
ros2 topic pub -r 10 /helicopter/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {z: 1.0}}'

# Read altitude
ros2 topic echo --once /helicopter/odom --field pose.pose.position
```

Expected: `z` rises by roughly `commanded_z_velocity × seconds_commanded`.

## 📁 Files

```
9_helicopter_control/
├── helicopter_minimal.sdf      # Default clean world: floor + red marker + X3 controls
├── helicopter.sdf              # Larger world: Baylands/fallback ground + X3 controls
├── helicopter_sim.launch.py    # Starts gazebo + bridge + rosbridge + rosapi
├── pyproject.toml              # uv/pip dependencies for the MCP side
└── README.md
```

## 🔧 Tuning notes

The velocity controller gains in the SDF worlds come from the upstream Fortress demo and are conservative. If the helicopter feels sluggish or oscillates, tune these in the `MulticopterVelocityControl` plugin block:

```xml
<velocityGain>2.7 2.7 2.7</velocityGain>
<attitudeGain>2 3 0.15</attitudeGain>
<angularRateGain>0.4 0.52 0.18</angularRateGain>
<maximumLinearAcceleration>2 2 2</maximumLinearAcceleration>
```
