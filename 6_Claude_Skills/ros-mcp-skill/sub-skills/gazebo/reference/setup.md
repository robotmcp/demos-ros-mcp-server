# Gazebo + ROS 2 + ros-mcp Setup Guide

Complete installation and configuration guide for running Gazebo simulations with AI control via ros-mcp-server.

---

## Table of Contents

1. [Install ROS 2](#install-ros-2)
2. [Install Gazebo](#install-gazebo)
3. [Install ros-gz-bridge](#install-ros-gz-bridge)
4. [Install rosbridge-server](#install-rosbridge-server)
5. [Install ros-mcp-server](#install-ros-mcp-server)
6. [Verify the Stack](#verify-the-stack)

---

## Install ROS 2

Choose your distribution based on your Ubuntu version:

| Ubuntu | ROS 2 Distro | Gazebo Pairing |
|--------|-------------|----------------|
| 22.04 | Humble (LTS) | Fortress or Garden |
| 22.04 | Iron | Garden |
| 24.04 | Jazzy (LTS) | Harmonic |

### Humble (Ubuntu 22.04)

```bash
# Set locale
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# Add ROS 2 apt repository
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | \
  sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# Install
sudo apt update
sudo apt install ros-humble-desktop
```

### Jazzy (Ubuntu 24.04)

```bash
# Same process but replace humble with jazzy
sudo apt install ros-jazzy-desktop
```

### Source ROS 2 (add to ~/.bashrc for persistence)

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

---

## Install Gazebo

### Humble → Gazebo Fortress (default)

```bash
sudo apt install ros-humble-ros-gz
```

This installs Gazebo Fortress and all integration packages in one step.

### Humble → Gazebo Garden (optional, newer)

```bash
# Install Gazebo Garden
sudo apt install ros-humble-ros-gz-garden
```

### Jazzy → Gazebo Harmonic

```bash
sudo apt install ros-jazzy-ros-gz
```

This installs Gazebo Harmonic (the recommended pairing for Jazzy).

### Standalone Gazebo install (alternative)

```bash
# Gazebo Harmonic standalone
sudo apt install gazebo-harmonic

# Or via snap (not recommended for ROS integration)
# sudo snap install gz-harmonic
```

### Verify Gazebo installation

```bash
gz sim --version
# Should print: Gazebo Sim, version X.X.X

# Launch empty world to test
gz sim empty.sdf
```

---

## Install ros-gz-bridge

The bridge package should be installed as part of `ros-gz` above, but verify:

```bash
# Check if installed
ros2 pkg list | grep ros_gz_bridge

# If missing, install explicitly
sudo apt install ros-$ROS_DISTRO-ros-gz-bridge

# Example for Humble:
sudo apt install ros-humble-ros-gz-bridge

# Example for Jazzy:
sudo apt install ros-jazzy-ros-gz-bridge
```

### Verify the bridge is accessible

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
ros2 run ros_gz_bridge parameter_bridge --help
```

---

## Install rosbridge-server

```bash
sudo apt install ros-$ROS_DISTRO-rosbridge-server

# Example:
sudo apt install ros-humble-rosbridge-server
# or
sudo apt install ros-jazzy-rosbridge-server
```

### Verify rosbridge

```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
# Should print: Rosbridge WebSocket server started on port 9090
```

Test the WebSocket port is open (in another terminal):

```bash
ss -tlnp | grep 9090
# Should show a LISTEN socket on port 9090
```

---

## Install ros-mcp-server

### Option 1: pip (simplest)

```bash
pip install ros-mcp-server
```

### Option 2: uv (recommended)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Install ros-mcp-server
uv pip install ros-mcp-server
```

### Option 3: From source

```bash
git clone https://github.com/robotmcp/ros-mcp-server.git
cd ros-mcp-server
uv sync
```

### Configure MCP Client

**Claude Desktop** (`~/.config/Claude/claude_desktop_config.json` on Linux):

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

**If from source with uv:**

```json
{
  "mcpServers": {
    "ros-mcp-server": {
      "command": "uv",
      "args": [
        "--directory", "/absolute/path/to/ros-mcp-server",
        "run", "server.py"
      ]
    }
  }
}
```

**Claude Code (CLI):**

```bash
claude mcp add-json "ros-mcp-server" '{"command":"ros-mcp","args":[]}'
# Or from source:
claude mcp add-json "ros-mcp-server" \
  '{"command":"uv","args":["--directory","/path/to/ros-mcp-server","run","server.py"]}'
```

---

## Verify the Stack

### Full system check (run in order)

**Terminal 1 — Gazebo:**
```bash
source /opt/ros/$ROS_DISTRO/setup.bash
gz sim empty.sdf    # or your world file
```

**Terminal 2 — ros-gz-bridge:**
```bash
source /opt/ros/$ROS_DISTRO/setup.bash
ros2 run ros_gz_bridge parameter_bridge \
  /clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock
```

**Terminal 3 — rosbridge:**
```bash
source /opt/ros/$ROS_DISTRO/setup.bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

**In your AI client (MCP):**
```
connect_to_robot()
detect_ros_version()
get_topics()
get_nodes()
```

Expected nodes you should see: `ros_gz_bridge`, `rosbridge_websocket`

### Port check

```bash
# rosbridge WebSocket
ss -tlnp | grep 9090

# Gazebo transport (usually not needed to check)
# Gazebo uses its own transport layer internally
```

---

## Environment Variables

Set these to avoid repeating arguments:

```bash
# In ~/.bashrc
export ROS_DISTRO=humble          # or jazzy
export ROSBRIDGE_HOST=127.0.0.1
export ROSBRIDGE_PORT=9090

# Source ROS 2
source /opt/ros/$ROS_DISTRO/setup.bash
```

---

## Docker Setup (Alternative)

If you prefer a containerized environment:

```dockerfile
# Dockerfile (Humble + Gazebo Fortress)
FROM osrf/ros:humble-desktop

RUN apt-get update && apt-get install -y \
    ros-humble-ros-gz \
    ros-humble-rosbridge-server \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip install ros-mcp-server

CMD ["bash"]
```

```yaml
# docker-compose.yml
version: '3'
services:
  ros-gazebo:
    build: .
    ports:
      - "9090:9090"   # rosbridge
      - "11345:11345" # Gazebo transport (if needed remotely)
    environment:
      - DISPLAY=$DISPLAY
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix  # for GUI
    command: >
      bash -c "
        source /opt/ros/humble/setup.bash &&
        ros2 launch rosbridge_server rosbridge_websocket_launch.xml address:=0.0.0.0
      "
```

---

## WSL2 Notes

Running Gazebo GUI in WSL2 requires a display server:

```bash
# Install VcXsrv or use WSLg (Windows 11 only)
export DISPLAY=:0
export LIBGL_ALWAYS_INDIRECT=1

# Test display
xclock  # or xeyes
```

For Windows 11 + WSL2, WSLg provides native display support — no extra configuration needed.
