# TugBot Installation & Setup

Setup guide for the TugBot simulation demo.

**Tested on**: Ubuntu 22.04, ROS 2 Humble, Ignition Gazebo Fortress

---

## Overview

The TugBot demo is self-contained — no colcon workspace or custom ROS packages to build.

**Demo location**: `/home/bharat/ROS-MCP/demos-ros-mcp-server/1_Gazebo_Tugbot/`

Key files:
- `tugbot_sim.launch.py` — launches Gazebo + bridge + rosbridge + rosapi in one go
- `tugbot_depot.sdf` — the warehouse world file

---

## System Requirements

| Component | Requirement |
|-----------|-------------|
| OS | Ubuntu 22.04 LTS |
| ROS 2 | Humble |
| Gazebo | Ignition Fortress (via `ros-humble-ros-gz`) |
| RAM | 4 GB minimum, 8 GB recommended |
| GPU | Required for Gazebo rendering |

---

## Step 1: Install ROS 2 Packages

```bash
sudo apt update
sudo apt install ros-humble-ros-gz          # Ignition Fortress + ROS 2 bridge
sudo apt install ros-humble-rosapi          # Required for topic introspection
sudo apt install ros-humble-rosbridge-server # WebSocket connection for ros-mcp
```

Verify:
```bash
source /opt/ros/humble/setup.bash
ign gazebo --version                          # Ignition Gazebo, version X.X.X
ros2 pkg list | grep ros_gz_bridge            # ros_gz_bridge
ros2 pkg list | grep rosbridge_server         # rosbridge_server
ros2 pkg list | grep rosapi                   # rosapi
```

---

## Step 2: Set Up the Demo venv

The demo uses `uv` to manage a Python venv (needed because ROS nodes run inside it).

```bash
cd /home/bharat/ROS-MCP/demos-ros-mcp-server/1_Gazebo_Tugbot

# If venv doesn't exist yet:
uv venv
source .venv/bin/activate
uv sync
```

The `.venv` should already exist at this path. If `uv` is not installed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

---

## Step 3: Launch the Simulation

```bash
cd /home/bharat/ROS-MCP/demos-ros-mcp-server/1_Gazebo_Tugbot
source /opt/ros/humble/setup.bash
source .venv/bin/activate
ros2 launch tugbot_sim.launch.py
```

> **Important**: Must run from the `1_Gazebo_Tugbot/` directory — the launch file
> references `tugbot_depot.sdf` by filename without a path.

Wait for:
1. Gazebo window with warehouse world
2. TugBot robot visible in scene
3. Console: `Rosbridge WebSocket server started on port 9090`
4. Press **Play** in Gazebo if paused

---

## Step 4: Verify

In your AI client:
```
connect_to_robot()
get_topics()
```

Expected topics: `/cmd_vel`, `/odom`, `/scan`, `/tf`, `/clock`

---

## Common Issues

### "ModuleNotFoundError: No module named 'bson'"
```bash
cd /home/bharat/ROS-MCP/demos-ros-mcp-server/1_Gazebo_Tugbot
source .venv/bin/activate
uv add pymongo tornado
```

### `ign gazebo` not found
```bash
sudo apt install ros-humble-ros-gz
source /opt/ros/humble/setup.bash
```

### Gazebo display error
```bash
echo $DISPLAY   # Must be set (e.g. :0)
# For headless: sudo apt install xvfb && Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
```
