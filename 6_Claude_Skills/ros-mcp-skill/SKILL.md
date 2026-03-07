---
name: ros-mcp-server
description: Connect AI models to ROS 2 robots using the ROS-MCP Server via rosbridge. Use this skill whenever the user wants to control robots, interact with ROS 2 topics/services/actions/parameters, debug robot systems, or set up AI-to-robot communication. Trigger on mentions of ROS, ROS 2, rosbridge, robot control, robot topics, robot services, turtlesim, Gazebo, or any robotic system integration with AI. Also use when users ask about listing robot capabilities, publishing/subscribing to topics, calling services, or reading sensor data from robots.
---

## Sub-Skills

| Sub-Skill | When to Use |
|-----------|-------------|
| [Gazebo Simulation](./sub-skills/gazebo/SKILL.md) | Launching Gazebo simulations, setting up ros-gz-bridge, running simulated robots with AI |
| [TugBot Demo](./sub-skills/gazebo/sub-skills/tugbot/SKILL.md) | Default simulation demo, TugBot warehouse simulation, testing Gazebo + ros-mcp end-to-end |

> Use the **Gazebo sub-skill** when working with any Gazebo simulation. Use the **TugBot sub-skill** as the default demo or when the user asks about TugBot specifically.

---

# ROS-MCP Server Skill

This skill enables AI models (Claude, GPT, Gemini) to interact with ROS 2 robots through the [ROS-MCP Server](https://github.com/robotmcp/ros-mcp-server). It provides bidirectional communication: natural language commands are translated to ROS 2 operations, and robot state/sensor data flows back to the AI.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI Client                                │
│  (Claude Desktop / VS Code / Cursor / OpenClaw / Claude Code)   │
└─────────────────────────────┬───────────────────────────────────┘
                              │ MCP Protocol (stdio/SSE)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ROS-MCP Server                              │
│              (Python, runs on client machine)                   │
└─────────────────────────────┬───────────────────────────────────┘
                              │ WebSocket (port 9090)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    rosbridge_server                             │
│              (ROS 2 node on robot/sim)                          │
└─────────────────────────────┬───────────────────────────────────┘
                              │ ROS 2 DDS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Robot System                               │
│   Topics, Services, Actions, Parameters, Sensors, Actuators     │
└─────────────────────────────────────────────────────────────────┘
```

**Key Insight**: The ROS-MCP Server communicates via rosbridge's WebSocket interface — no direct ROS CLI access needed. The agent should **never** run `rosrun`, `roslaunch`, or `roscore` — those are ROS 1 commands and do not apply here.

---

## Quick Reference

| Topic | Reference File |
|-------|----------------|
| Installation & Setup | [📦 installation.md](./reference/installation.md) |
| OpenClaw Gateway Fix (ros2 not found) | [🔧 openclaw-setup.sh](./reference/openclaw-setup.sh) |
| Tool Reference & Examples | [🔧 tools.md](./reference/tools.md) |
| Common Workflows | [🔄 workflows.md](./reference/workflows.md) |
| Troubleshooting | [🔍 troubleshooting.md](./reference/troubleshooting.md) |

---

## Setup Summary

### Prerequisites

1. **ROS 2** (Humble/Iron/Jazzy) installed and **sourced** (`echo $ROS_DISTRO` should print the distro name)
2. **rosbridge_server**: Installed and running on the robot/simulation machine
3. **Python 3.10+**: On the machine running the MCP server
4. **MCP Client**: Claude Desktop, VS Code, Cursor, Claude Code, or OpenClaw

> **Sourcing check**: Before running any ROS 2 command, verify the environment is sourced:
> ```bash
> echo $ROS_DISTRO   # Should print: humble / iron / jazzy
> ```
> If empty, source it: `source /opt/ros/humble/setup.bash` (replace `humble` with your distro).
> If using a custom workspace also run: `source ~/ros2_ws/install/setup.bash`

### Quick Install

```bash
# Install ROS-MCP Server via pip
pip install ros-mcp-server

# OR install with uv (recommended)
uv pip install ros-mcp-server
```

### Configuration

**For Claude Desktop** (`claude_desktop_config.json`):
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

**Alternative (from source with uv):**
```json
{
  "mcpServers": {
    "ros-mcp-server": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/ros-mcp-server",
        "run", "server.py"
      ]
    }
  }
}
```

**For Claude Code**:
```bash
# If installed via pip
claude mcp add-json "ros-mcp-server" '{"command":"ros-mcp","args":[]}'

# Or from source with uv
claude mcp add-json "ros-mcp-server" \
  '{"command":"uv","args":["--directory","/ABSOLUTE/PATH/ros-mcp-server","run","server.py"]}'
```

### Start rosbridge (on robot/simulation machine)

```bash
source /opt/ros/$ROS_DISTRO/setup.bash   # if not already sourced
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

Verify it's running: `ss -tlnp | grep 9090` — should show a LISTEN socket.

---

## Available MCP Tools

The ROS-MCP Server provides these tools (automatically available once connected):

### Connection & Discovery
| Tool | Description |
|------|-------------|
| `connect_to_robot` | Connect to robot via IP/port with connectivity test |
| `ping_robot` | Test if robot IP is reachable and rosbridge port is open |
| `detect_ros_version` | Detect ROS version and distribution via rosbridge |
| `get_verified_robots_list` | List pre-verified robot models with spec files |
| `get_verified_robot_spec` | Load specifications for verified robot models |

### Node Introspection
| Tool | Description |
|------|-------------|
| `get_nodes` | List all currently running ROS nodes |
| `get_node_details` | Get node's publishers, subscribers, and services |

### Topics
| Tool | Description |
|------|-------------|
| `get_topics` | List all available ROS topics |
| `get_topic_type` | Get message type for a specific topic |
| `get_topic_details` | Get detailed info including publishers/subscribers |
| `get_message_details` | Get complete structure of a message type |
| `subscribe_once` | Subscribe and return first message received |
| `subscribe_for_duration` | Collect messages over a time period |
| `publish_once` | Publish a single message to a topic |
| `publish_for_durations` | Publish sequence of messages with delays |

### Services
| Tool | Description |
|------|-------------|
| `get_services` | List all available ROS services |
| `get_service_type` | Get the type for a specific service |
| `get_service_details` | Get request/response structures and provider nodes |
| `call_service` | Call a ROS service with request data |

### Actions (ROS 2 Only)
| Tool | Description |
|------|-------------|
| `get_actions` | List all available ROS actions |
| `get_action_details` | Get goal, result, and feedback structures |
| `get_action_status` | Get status of a specific action |
| `send_action_goal` | Send a goal to an action server |
| `cancel_action_goal` | Cancel a running action goal |

### Parameters (ROS 2 Only)
| Tool | Description |
|------|-------------|
| `get_parameters` | List all parameter names for a node |
| `get_parameter` | Get a single parameter value |
| `get_parameter_details` | Get parameter value, type, and metadata |
| `set_parameter` | Set a parameter value |
| `has_parameter` | Check if a parameter exists |
| `delete_parameter` | Delete a parameter |

### Vision
| Tool | Description |
|------|-------------|
| `analyze_previously_received_image` | Analyze images received from ROS operations |

---

## Connection Workflow

When starting a new robot control session, follow this sequence:

### 1. Connect to the Robot

```
# Default (localhost:9090)
connect_to_robot()

# Remote robot
connect_to_robot(ip="192.168.1.100", port=9090)

# With custom timeouts
connect_to_robot(ip="192.168.1.100", port=9090, ping_timeout=5, port_timeout=5)
```

### 2. Verify Connection & Discover Capabilities

```
# Check ROS version
detect_ros_version()

# List all available topics
get_topics()

# List all available services
get_services()

# List all nodes
get_nodes()

# For ROS 2: List actions and parameters
get_actions()
get_parameters("/node_name")
```

### 3. Explore Specific Interfaces

```
# Understand a topic's message structure
get_topic_type("/cmd_vel")
get_message_details("geometry_msgs/Twist")

# Understand a service's interface
get_service_type("/spawn")
get_service_details("/spawn")
```

### 4. Interact with the Robot

```
# Subscribe to sensor data
subscribe_once(topic="/scan", msg_type="sensor_msgs/LaserScan")

# Publish commands
publish_once(
  topic="/cmd_vel",
  msg_type="geometry_msgs/Twist",
  msg={"linear": {"x": 0.5}, "angular": {"z": 0.0}}
)

# Call services
call_service(
  service_name="/spawn",
  service_type="turtlesim/Spawn",
  request={"x": 5.0, "y": 5.0, "theta": 0.0, "name": "turtle2"}
)
```

---

## Common Message Types Reference

### Motion Control

**geometry_msgs/Twist** (velocity commands):
```json
{
  "linear": {"x": 0.0, "y": 0.0, "z": 0.0},
  "angular": {"x": 0.0, "y": 0.0, "z": 0.0}
}
```

**geometry_msgs/Pose** (position + orientation):
```json
{
  "position": {"x": 0.0, "y": 0.0, "z": 0.0},
  "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
}
```

### Common Topics

| Topic Pattern | Type | Purpose |
|---------------|------|---------|
| `/cmd_vel` | geometry_msgs/Twist | Velocity commands |
| `/odom` | nav_msgs/Odometry | Odometry data |
| `/scan` | sensor_msgs/LaserScan | LIDAR data |
| `/camera/image_raw` | sensor_msgs/Image | Camera images |
| `/joint_states` | sensor_msgs/JointState | Joint positions/velocities |
| `/tf` | tf2_msgs/TFMessage | Transform tree |

---

## Turtlesim Example (Testing Setup)

Turtlesim is the "hello world" of ROS — perfect for testing your setup:

### Start Turtlesim

```bash
# Terminal 1: Start turtlesim
ros2 run turtlesim turtlesim_node

# Terminal 2: Start rosbridge
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

### Control via MCP Tools

```
# Connect
connect_to_robot()

# Discover available topics
get_topics()
# Returns: /turtle1/cmd_vel, /turtle1/pose, etc.

# Move the turtle forward
publish_once(
  topic="/turtle1/cmd_vel",
  msg_type="geometry_msgs/Twist",
  msg={"linear": {"x": 2.0}, "angular": {"z": 0.0}}
)

# Rotate the turtle
publish_once(
  topic="/turtle1/cmd_vel",
  msg_type="geometry_msgs/Twist",
  msg={"linear": {"x": 0.0}, "angular": {"z": 1.5}}
)

# Get turtle's current pose
subscribe_once(topic="/turtle1/pose", msg_type="turtlesim/Pose")

# Spawn a new turtle
call_service(
  service_name="/spawn",
  service_type="turtlesim/Spawn",
  request={"x": 3.0, "y": 3.0, "theta": 0.0, "name": "turtle2"}
)

# Clear drawing
call_service(
  service_name="/clear",
  service_type="std_srvs/Empty",
  request={}
)
```

---

## Best Practices

### 1. Always Discover Before Acting
Before sending commands, always:
- Use `get_topics()` to see what's available
- Use `get_message_details()` to understand message structure
- Use `subscribe_once()` to verify data is flowing

### 2. Handle Message Type Syntax
- Use `geometry_msgs/msg/Twist` (ROS 2 style) when using the full namespace
- The MCP server also accepts shorthand `geometry_msgs/Twist` — both work

### 3. Use Timeouts Appropriately
- Slow topics (cameras, point clouds): increase timeout
- Fast topics (IMU, odometry): default timeout is fine

```
subscribe_once(
  topic="/camera/image_raw",
  msg_type="sensor_msgs/Image",
  timeout=10.0,  # 10 second timeout for slow camera
  expects_image="true"  # Hint for faster processing
)
```

### 4. Check Service Response
Service calls return results — always check them:
```
result = call_service(
  service_name="/spawn",
  service_type="turtlesim/Spawn",
  request={"x": 5.0, "y": 5.0, "name": "turtle2"}
)
# Result contains success/failure info
```

---

## Error Handling

### Common Issues

| Error | Likely Cause | Solution |
|-------|--------------|----------|
| Connection refused | rosbridge not running | Start rosbridge_server |
| Ping succeeds, port fails | ROS running, rosbridge not started | Launch rosbridge specifically |
| Topic not found | Wrong topic name or not published | Use `get_topics()` to discover |
| Message type mismatch | Wrong msg_type specified | Use `get_topic_type()` to check |
| Service timeout | Service not available or slow | Check service exists with `get_services()` |

### Diagnostic Steps

1. **Test connectivity**: `ping_robot(ip="...", port=9090)`
2. **Check rosbridge**: Verify rosbridge node is running
3. **List available interfaces**: `get_topics()`, `get_services()`
4. **Verify message types**: `get_message_details("...")`

---

## Remote Robot Setup

For robots on a different machine:

### On Robot Machine
```bash
# Ensure rosbridge binds to all interfaces (not just localhost)
ros2 launch rosbridge_server rosbridge_websocket_launch.xml address:=0.0.0.0
```

### From MCP Client
```
# Connect using robot's IP
connect_to_robot(ip="192.168.1.100", port=9090)
```

### Firewall Notes
- Ensure port 9090 (default) is open
- For Docker: expose port 9090
- For VPN/Tailscale: use the robot's Tailscale IP

---

## Safety Considerations

1. **Start Slow**: When testing new robots, use low velocities
2. **Emergency Stop**: Know your robot's e-stop procedure
3. **Simulation First**: Test commands in Gazebo/simulation before real hardware
4. **Monitor Continuously**: Use `subscribe_for_duration()` to monitor robot state
5. **Timeout Handling**: Set appropriate timeouts for long-running actions

---

## Next Steps

- **[📦 Installation Guide](./reference/installation.md)**: Detailed setup instructions
- **[🔧 Tool Reference](./reference/tools.md)**: Complete tool documentation with examples
- **[🔄 Common Workflows](./reference/workflows.md)**: Step-by-step workflow guides
- **[🔍 Troubleshooting](./reference/troubleshooting.md)**: Solving common issues
