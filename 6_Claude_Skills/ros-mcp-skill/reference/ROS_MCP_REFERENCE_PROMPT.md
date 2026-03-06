# ROS-MCP Server Complete Reference Guide

> **Purpose**: This document serves as a comprehensive guide and reference prompt for using the ROS-MCP Server to control ROS/ROS2 robots via AI models like Claude. Use this as context when working with the ROS-MCP tools.

---

## What is the ROS-MCP Server?

The [ROS-MCP Server](https://github.com/robotmcp/ros-mcp-server) connects large language models (Claude, GPT, Gemini) with ROS/ROS2 robots through the Model Context Protocol (MCP). It enables:

- **Natural language robot control** → Commands translated to ROS operations
- **Full robot visibility** → Subscribe to topics, call services, read sensor data
- **Bidirectional communication** → Both control robots AND observe their state
- **ROS 2** → Works with ROS 2 (Humble/Iron/Jazzy) via rosbridge WebSocket
- **No robot code changes** → Only requires rosbridge_server node

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI Client                                │
│     (Claude Desktop / VS Code / Claude Code / OpenClaw)         │
└─────────────────────────────┬───────────────────────────────────┘
                              │ MCP Protocol
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ROS-MCP Server                              │
│              (Python, runs on client machine)                   │
└─────────────────────────────┬───────────────────────────────────┘
                              │ WebSocket (port 9090)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    rosbridge_server                             │
│              (ROS/ROS2 node on robot/simulation)                │
└─────────────────────────────┬───────────────────────────────────┘
                              │ ROS/ROS2 DDS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Robot System                               │
│   Topics, Services, Actions, Parameters, Sensors, Actuators     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Setup Checklist

### Prerequisites
- [ ] ROS 2 (Humble/Iron/Jazzy) installed and sourced — `echo $ROS_DISTRO` prints the distro name
- [ ] rosbridge_server package installed and **running** on port 9090
- [ ] Python 3.10+ on client machine
- [ ] MCP client (Claude Desktop, VS Code, Claude Code, OpenClaw, etc.)

> If `ros2` commands fail, source the environment first:
> `source /opt/ros/humble/setup.bash` (replace `humble` with your distro)

### Installation
```bash
# Install ROS-MCP Server
pip install ros-mcp-server
# OR
uv pip install ros-mcp-server
```

### Start rosbridge (on robot)
```bash
source /opt/ros/$ROS_DISTRO/setup.bash   # if not already sourced
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

### Configure MCP Client

**Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "ros-mcp-server": {
      "command": "ros-mcp",
      "args": []
    }
  }
}
```

---

## Complete Tool Reference

### Connection & Discovery

| Tool | Purpose | Example |
|------|---------|---------|
| `connect_to_robot` | Connect to robot | `connect_to_robot(ip="192.168.1.100", port=9090)` |
| `ping_robot` | Test connectivity | `ping_robot(ip="192.168.1.100", port=9090)` |
| `detect_ros_version` | Get ROS version | `detect_ros_version()` |
| `get_verified_robots_list` | List known robots | `get_verified_robots_list()` |
| `get_verified_robot_spec` | Get robot specs | `get_verified_robot_spec(name="unitree_go2")` |

### Nodes

| Tool | Purpose | Example |
|------|---------|---------|
| `get_nodes` | List all nodes | `get_nodes()` |
| `get_node_details` | Node's pub/sub/services | `get_node_details(node="/turtlesim")` |

### Topics

| Tool | Purpose | Example |
|------|---------|---------|
| `get_topics` | List all topics | `get_topics()` |
| `get_topic_type` | Get message type | `get_topic_type(topic="/cmd_vel")` |
| `get_topic_details` | Full topic info | `get_topic_details(topic="/cmd_vel")` |
| `get_message_details` | Message structure | `get_message_details(message_type="geometry_msgs/Twist")` |
| `subscribe_once` | Get one message | `subscribe_once(topic="/odom", msg_type="nav_msgs/Odometry")` |
| `subscribe_for_duration` | Collect messages | `subscribe_for_duration(topic="/scan", duration=5)` |
| `publish_once` | Send one message | `publish_once(topic="/cmd_vel", msg_type="geometry_msgs/Twist", msg={...})` |
| `publish_for_durations` | Sequence of messages | `publish_for_durations(topic="/cmd_vel", messages=[...], durations=[...])` |

### Services

| Tool | Purpose | Example |
|------|---------|---------|
| `get_services` | List all services | `get_services()` |
| `get_service_type` | Get service type | `get_service_type(service="/spawn")` |
| `get_service_details` | Request/response structure | `get_service_details(service="/spawn")` |
| `call_service` | Call a service | `call_service(service_name="/spawn", service_type="turtlesim/Spawn", request={...})` |

### Actions (ROS 2 Only)

| Tool | Purpose | Example |
|------|---------|---------|
| `get_actions` | List all actions | `get_actions()` |
| `get_action_details` | Goal/result/feedback | `get_action_details(action="/navigate_to_pose")` |
| `get_action_status` | Check action state | `get_action_status(action_name="/navigate_to_pose")` |
| `send_action_goal` | Send goal | `send_action_goal(action_name="...", action_type="...", goal={...})` |
| `cancel_action_goal` | Cancel goal | `cancel_action_goal(action_name="...", goal_id="...")` |

### Parameters (ROS 2 Only)

| Tool | Purpose | Example |
|------|---------|---------|
| `get_parameters` | List node params | `get_parameters(node_name="/turtlesim")` |
| `get_parameter` | Get param value | `get_parameter(name="/turtlesim:background_r")` |
| `get_parameter_details` | Full param info | `get_parameter_details(name="/turtlesim:background_r")` |
| `set_parameter` | Set param value | `set_parameter(name="/turtlesim:background_r", value="255")` |
| `has_parameter` | Check if exists | `has_parameter(name="/turtlesim:background_r")` |
| `delete_parameter` | Delete param | `delete_parameter(name="/my_node:temp_param")` |

### Vision

| Tool | Purpose | Example |
|------|---------|---------|
| `analyze_previously_received_image` | Analyze saved image | `analyze_previously_received_image(image_path="./camera/received_image.jpeg")` |

---

## Standard Workflow

### Phase 1: Connect
```python
connect_to_robot(ip="192.168.1.100", port=9090)
detect_ros_version()
```

### Phase 2: Discover
```python
get_nodes()
get_topics()
get_services()
get_actions()  # ROS 2 only
```

### Phase 3: Explore
```python
# Understand a topic
get_topic_type(topic="/cmd_vel")
get_message_details(message_type="geometry_msgs/Twist")

# Understand a service
get_service_details(service="/spawn")
```

### Phase 4: Interact
```python
# Read sensor data
subscribe_once(topic="/scan", msg_type="sensor_msgs/LaserScan")

# Send commands
publish_once(
  topic="/cmd_vel",
  msg_type="geometry_msgs/Twist",
  msg={"linear": {"x": 0.5}, "angular": {"z": 0.0}}
)

# Call services
call_service(
  service_name="/spawn",
  service_type="turtlesim/Spawn",
  request={"x": 5.0, "y": 5.0, "name": "turtle2"}
)
```

---

## Common Message Types

### geometry_msgs/Twist (velocity commands)
```json
{
  "linear": {"x": 0.0, "y": 0.0, "z": 0.0},
  "angular": {"x": 0.0, "y": 0.0, "z": 0.0}
}
```

### geometry_msgs/Pose (position + orientation)
```json
{
  "position": {"x": 0.0, "y": 0.0, "z": 0.0},
  "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
}
```

### geometry_msgs/PoseStamped (pose with header)
```json
{
  "header": {"frame_id": "map"},
  "pose": {
    "position": {"x": 0.0, "y": 0.0, "z": 0.0},
    "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
  }
}
```

### Common Topic Patterns
| Topic | Type | Purpose |
|-------|------|---------|
| `/cmd_vel` | geometry_msgs/Twist | Velocity commands |
| `/odom` | nav_msgs/Odometry | Odometry data |
| `/scan` | sensor_msgs/LaserScan | LIDAR data |
| `/camera/image_raw` | sensor_msgs/Image | Camera images |
| `/joint_states` | sensor_msgs/JointState | Joint positions |
| `/tf`, `/tf_static` | tf2_msgs/TFMessage | Transforms |

---

## Turtlesim Quick Reference

**Start turtlesim:**
```bash
# Terminal 1
ros2 run turtlesim turtlesim_node

# Terminal 2
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

**Common commands:**
```python
# Connect
connect_to_robot()

# Move forward
publish_once(topic="/turtle1/cmd_vel", msg_type="geometry_msgs/Twist", msg={"linear": {"x": 2.0}})

# Rotate
publish_once(topic="/turtle1/cmd_vel", msg_type="geometry_msgs/Twist", msg={"angular": {"z": 1.5}})

# Get position
subscribe_once(topic="/turtle1/pose", msg_type="turtlesim/Pose")

# Spawn turtle
call_service(service_name="/spawn", service_type="turtlesim/Spawn", request={"x": 3.0, "y": 3.0, "name": "turtle2"})

# Set pen color
call_service(service_name="/turtle1/set_pen", service_type="turtlesim/SetPen", request={"r": 255, "g": 0, "b": 0, "width": 3, "off": 0})

# Clear canvas
call_service(service_name="/clear", service_type="std_srvs/Empty", request={})

# Reset
call_service(service_name="/reset", service_type="std_srvs/Empty", request={})
```

---

## Navigation (Nav2) Quick Reference

```python
# Check Nav2 is running
get_actions()  # Look for /navigate_to_pose

# Navigate to pose
send_action_goal(
  action_name="/navigate_to_pose",
  action_type="nav2_msgs/action/NavigateToPose",
  goal={
    "pose": {
      "header": {"frame_id": "map"},
      "pose": {
        "position": {"x": 2.0, "y": 1.0, "z": 0.0},
        "orientation": {"w": 1.0}
      }
    }
  },
  timeout=120.0
)

# Cancel navigation
cancel_action_goal(action_name="/navigate_to_pose", goal_id="<goal_id>")
```

---

## Troubleshooting Quick Reference

| Problem | Likely Cause | Solution |
|---------|--------------|----------|
| Connection refused | rosbridge not running | Start rosbridge |
| Ping OK, port fails | rosbridge not started | Launch rosbridge specifically |
| Topic not found | Wrong name or not published | Use `get_topics()` |
| Subscribe timeout | No publisher or slow rate | Increase timeout, check publishers |
| Publish no effect | No subscriber or wrong type | Check `get_topic_details()` |
| Service timeout | Service unavailable | Use `get_services()` to verify |
| Action not found | No action servers running | Check `ros2 node list`; ensure action servers are up |
| Parameter not found | Wrong format | Format: `/node:param_name` — use `get_parameters(node_name="...")` |

**Diagnostic sequence:**
```python
ping_robot(ip="...", port=9090)
connect_to_robot(ip="...", port=9090)
detect_ros_version()
get_topics()
get_services()
get_nodes()
```

---

## Best Practices

1. **Always discover before acting** - Use `get_topics()`, `get_message_details()` first
2. **Verify data flow** - Use `subscribe_once()` to confirm topics have data
3. **Handle message type syntax** — both `geometry_msgs/Twist` and `geometry_msgs/msg/Twist` work; MCP server accepts either
4. **Set appropriate timeouts** - Cameras/slow topics need longer timeouts
5. **Check service responses** - Service calls return results, verify success
6. **Start slow** - Use low velocities when testing new robots
7. **Know emergency stop** - Have e-stop procedure ready
8. **Simulation first** - Test in Gazebo before real hardware

---

## Remote Robot Setup

**On robot (bind to all interfaces):**
```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml address:=0.0.0.0
```

**Firewall:**
```bash
sudo ufw allow 9090/tcp
```

**Connect:**
```python
connect_to_robot(ip="192.168.1.100", port=9090)
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ROSBRIDGE_HOST` | `127.0.0.1` | Default rosbridge host |
| `ROSBRIDGE_PORT` | `9090` | Default rosbridge port |

---

*This reference is based on the [ROS-MCP Server](https://github.com/robotmcp/ros-mcp-server) v2.2.1+*
