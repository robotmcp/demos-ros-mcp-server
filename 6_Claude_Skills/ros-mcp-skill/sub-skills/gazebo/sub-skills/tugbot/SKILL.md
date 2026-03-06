---
name: ros-mcp-gazebo-tugbot
description: >
  Run and control the TugBot simulation in Gazebo via ros-mcp-server. Use this skill when the
  user mentions TugBot, wants to run the default Gazebo simulation demo, or asks to test a
  Gazebo-based robot with AI control. TugBot is a four-wheel skid-steer robot in a warehouse
  (depot) world — it serves as the reference simulation for ros-mcp. This skill handles the
  full end-to-end setup: launching Gazebo (Ignition Fortress), configuring the ros-gz-bridge,
  starting rosbridge, and operating the robot via ros-mcp tools.
---

# TugBot Simulation Skill

TugBot is a four-wheel drive skid-steer robot running in a Gazebo warehouse simulation
(**Ignition Gazebo Fortress**). It is the **reference/default example** for testing Gazebo +
ros-mcp integration.

**Demo source**: `/home/bharat/ROS-MCP/demos-ros-mcp-server/1_Gazebo_Tugbot/`
(GitHub mirror: https://github.com/robotmcp/demos-ros-mcp-server/tree/main/1_Gazebo_Tugbot)

**Key files**:
- `tugbot_sim.launch.py` — single launch file that starts everything
- `tugbot_depot.sdf` — warehouse world (must be in working directory when launched)

---

## Architecture

```
AI Client (Claude / OpenClaw)
        ↓ MCP Protocol
ros-mcp-server
        ↓ WebSocket :9090
rosbridge_server  ←─── started by tugbot_sim.launch.py
        ↓ ROS 2 DDS topics
ros_gz_bridge (parameter_bridge)  ←─── started by tugbot_sim.launch.py
        ↓ Ignition Transport
ign gazebo (TugBot + Depot World)  ←─── started by tugbot_sim.launch.py
        ↓ Physics + Sensors
TugBot Robot (4-wheel skid-steer, LIDAR, odometry)
```

---

## Quick Reference

| Reference | File |
|-----------|------|
| Installation & Dependencies | [setup.md](./reference/setup.md) |
| Topics & Bridge Config | [topics.md](./reference/topics.md) |
| Control Workflows | [workflows.md](./reference/workflows.md) |

---

## Prerequisites

| Requirement | Check |
|-------------|-------|
| ROS 2 Humble | `echo $ROS_DISTRO` → `humble` |
| Ignition Gazebo Fortress | `ign gazebo --version` |
| `ros_gz_bridge` | `ros2 pkg list \| grep ros_gz_bridge` |
| `rosbridge_server` | `ros2 pkg list \| grep rosbridge` |
| `rosapi` | `ros2 pkg list \| grep rosapi` |
| Demo repo cloned | `ls /home/bharat/ROS-MCP/demos-ros-mcp-server/1_Gazebo_Tugbot/` |

Install missing packages (if needed):
```bash
sudo apt install ros-humble-ros-gz ros-humble-rosapi ros-humble-rosbridge-server
```

---

## End-to-End Startup Procedure

### Step 1: Launch Everything (Single Command)

The demo provides a single launch file that starts Gazebo, the ROS-GZ bridge,
rosbridge websocket, and the rosapi node together.

```bash
cd /home/bharat/ROS-MCP/demos-ros-mcp-server/1_Gazebo_Tugbot
source /opt/ros/humble/setup.bash
source .venv/bin/activate
ros2 launch tugbot_sim.launch.py
```

> **Note**: You must `cd` into the `1_Gazebo_Tugbot/` directory first — the launch file
> references `tugbot_depot.sdf` by filename only (no path), so the SDF file must be in
> the working directory.

Wait until:
- The Gazebo window appears with the warehouse world
- The robot (TugBot) is visible in the scene
- Console shows: `[INFO] [rosbridge_websocket]: Rosbridge WebSocket server started on port 9090`
- Press **Play** in Gazebo if the simulation is paused

What this launch file starts:
- `ign gazebo -r tugbot_depot.sdf` — Ignition Gazebo Fortress with the warehouse world
- `ros_gz_bridge parameter_bridge` — bridges Ignition topics → ROS 2 topics:
  - `/model/tugbot/cmd_vel` → `/cmd_vel` (Twist, ROS→Ignition)
  - `/model/tugbot/odometry` → `/odom` (Odometry, Ignition→ROS)
  - `/scan` (LaserScan, Ignition→ROS)
  - `/model/tugbot/tf` → `/tf` (TFMessage, Ignition→ROS)
  - `/clock` (Clock, Ignition→ROS)
- `rosbridge_websocket` on port 9090
- `rosapi_node` for topic introspection

### Step 2: Connect via ros-mcp

In your AI client (Claude, OpenClaw):

```
connect_to_robot()
```

Expected response:
```
Successfully connected to robot at 127.0.0.1:9090
- Ping: OK
- Port 9090: Open
- WebSocket: Connected
```

Then discover the system:

```
detect_ros_version()
get_topics()
get_nodes()
```

You should see topics: `/cmd_vel`, `/odom`, `/scan`, `/tf`, `/clock`
and nodes: `ros_gz_bridge`, `rosbridge_websocket`, `rosapi`

---

## Agent Behavior: What to Do Automatically

When this skill is active, the agent should proactively:

1. **Check system state** before giving instructions:
   ```
   connect_to_robot()
   get_topics()
   ```
   - If connection fails → user needs to run the launch command above (Step 1)
   - If topics missing → launch file may not be fully started yet, wait a moment

2. **Verify data is flowing** after startup:
   ```
   subscribe_once(topic="/odom", msg_type="nav_msgs/msg/Odometry", timeout=5.0)
   subscribe_once(topic="/scan", msg_type="sensor_msgs/msg/LaserScan", timeout=5.0)
   ```
   - If no data → Gazebo simulation may be paused; tell user to press Play

3. **Use the correct message type syntax** for ROS 2:
   - Always use `geometry_msgs/msg/Twist` (not `geometry_msgs/Twist`) for ROS 2

4. **Default to safe velocities** when moving the robot (≤ 0.5 m/s, ≤ 0.8 rad/s)

5. **Stop the robot** after each maneuver:
   ```
   publish_once(
     topic="/cmd_vel",
     msg_type="geometry_msgs/msg/Twist",
     msg={"linear": {"x": 0.0}, "angular": {"z": 0.0}}
   )
   ```

---

## Basic Control Commands

### Move Forward

```
publish_once(
  topic="/cmd_vel",
  msg_type="geometry_msgs/msg/Twist",
  msg={"linear": {"x": 0.3}, "angular": {"z": 0.0}}
)
```

### Move Backward

```
publish_once(
  topic="/cmd_vel",
  msg_type="geometry_msgs/msg/Twist",
  msg={"linear": {"x": -0.3}, "angular": {"z": 0.0}}
)
```

### Rotate Left

```
publish_once(
  topic="/cmd_vel",
  msg_type="geometry_msgs/msg/Twist",
  msg={"linear": {"x": 0.0}, "angular": {"z": 0.5}}
)
```

### Rotate Right

```
publish_once(
  topic="/cmd_vel",
  msg_type="geometry_msgs/msg/Twist",
  msg={"linear": {"x": 0.0}, "angular": {"z": -0.5}}
)
```

### Stop

```
publish_once(
  topic="/cmd_vel",
  msg_type="geometry_msgs/msg/Twist",
  msg={"linear": {"x": 0.0}, "angular": {"z": 0.0}}
)
```

---

## Sensor Reading Commands

### Get Current Position (Odometry)

```
subscribe_once(topic="/odom", msg_type="nav_msgs/msg/Odometry", timeout=5.0)
```

### Get LIDAR Scan

```
subscribe_once(topic="/scan", msg_type="sensor_msgs/msg/LaserScan", timeout=5.0)
```

### Get IMU Data

```
subscribe_once(topic="/imu", msg_type="sensor_msgs/msg/Imu", timeout=5.0)
```

---

## Quick Demo: Drive a Square

```
# 1. Verify connection and data flow
connect_to_robot()
get_topics()
subscribe_once(topic="/odom", msg_type="nav_msgs/msg/Odometry", timeout=5.0)

# 2. Drive a square (each side ~2 seconds forward + 90° turn)
publish_for_durations(
  topic="/cmd_vel",
  msg_type="geometry_msgs/msg/Twist",
  messages=[
    {"linear": {"x": 0.4}},
    {"linear": {"x": 0.0}, "angular": {"z": 0.8}},
    {"linear": {"x": 0.4}},
    {"linear": {"x": 0.0}, "angular": {"z": 0.8}},
    {"linear": {"x": 0.4}},
    {"linear": {"x": 0.0}, "angular": {"z": 0.8}},
    {"linear": {"x": 0.4}},
    {"linear": {"x": 0.0}, "angular": {"z": 0.8}},
    {}
  ],
  durations=[2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 0.5]
)

# 3. Check final position
subscribe_once(topic="/odom", msg_type="nav_msgs/msg/Odometry", timeout=5.0)
```

---

## Troubleshooting

### `connect_to_robot()` fails — "Connection refused"

**Cause**: rosbridge is not running (launch file not started).

**Fix**: Run the launch command from Step 1 above.

### Robot doesn't respond to `/cmd_vel`

**Cause A**: Bridge direction wrong or bridge not running.

**Fix**: Check bridge is running: `ros2 node list | grep ros_gz_bridge`

The correct Ignition topic for TugBot cmd_vel is `/model/tugbot/cmd_vel`, remapped to `/cmd_vel`.

**Cause B**: Gazebo simulation is paused.

**Fix**: Click the **Play** button in the Gazebo GUI.

### `/odom` subscribe returns no data

**Cause**: Simulation is paused or bridge isn't running.

**Fix**:
- Click Play in Gazebo GUI
- Verify: `ign topic --echo --topic /model/tugbot/odometry`

### Launch fails — "world file not found" or `tugbot_depot.sdf` not found

**Cause**: Not running from the `1_Gazebo_Tugbot/` directory.

**Fix**: Always `cd /home/bharat/ROS-MCP/demos-ros-mcp-server/1_Gazebo_Tugbot` before launching.

### "ModuleNotFoundError: No module named 'bson' or 'tornado'"

**Cause**: venv not activated or dependencies not installed.

**Fix**:
```bash
cd /home/bharat/ROS-MCP/demos-ros-mcp-server/1_Gazebo_Tugbot
source .venv/bin/activate
uv sync
```

### Gazebo doesn't start (display error)

```bash
echo $DISPLAY   # Should show :0 or :1
```

For headless servers use Xvfb.

---

## Cleanup

When done with the simulation:

```
# Stop the robot first (in AI client)
publish_once(
  topic="/cmd_vel",
  msg_type="geometry_msgs/msg/Twist",
  msg={}
)
```

Then press `Ctrl+C` in the terminal running `ros2 launch tugbot_sim.launch.py`.

---

## Next Steps

After the TugBot demo is working, users can:

1. **Drive patterns**: Square, circle, zigzag using `publish_for_durations`
2. **Obstacle avoidance**: Use `/scan` LIDAR data to react to obstacles
3. **Remote control**: Connect from a different machine using `connect_to_robot(ip="<machine_ip>")`
