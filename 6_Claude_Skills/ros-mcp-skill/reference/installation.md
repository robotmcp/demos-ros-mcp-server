# ROS-MCP Server Installation Guide

Complete setup instructions for connecting AI models to ROS/ROS2 robots.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Install ROS-MCP Server](#install-ros-mcp-server)
3. [Configure MCP Clients](#configure-mcp-clients)
4. [Install rosbridge](#install-rosbridge)
5. [OpenClaw Gateway Fix (ros2 not found)](#openclaw-gateway-fix)
6. [Verify Installation](#verify-installation)
7. [Platform-Specific Notes](#platform-specific-notes)

---

## Prerequisites

### On Your Client Machine (where AI runs)

| Requirement | Version | Check Command |
|-------------|---------|---------------|
| Python | 3.10+ | `python3 --version` |
| pip | 23.0+ | `pip --version` |
| uv (recommended) | latest | `uv --version` |
| Git | any | `git --version` |

### On Your Robot/Simulation Machine

| Requirement | Options |
|-------------|---------|
| ROS Version | ROS 2 (Humble/Iron/Jazzy) |
| rosbridge_server | Installed via apt |
| Network | Accessible from client machine (or localhost for same machine) |

> **Sourcing check**: Before running anything, verify ROS 2 is sourced:
> ```bash
> echo $ROS_DISTRO   # Should print: humble / iron / jazzy
> ```
> If empty: `source /opt/ros/humble/setup.bash` (replace with your distro).
> To make it permanent: `echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc`

---

## Install ROS-MCP Server

### Option 1: pip install (Simplest)

```bash
pip install ros-mcp-server
```

### Option 2: uv install (Recommended)

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install ros-mcp-server
uv pip install ros-mcp-server
```

### Option 3: From Source (For Development)

```bash
# Clone the repository
git clone https://github.com/robotmcp/ros-mcp-server.git
cd ros-mcp-server

# Install with uv
uv sync

# Or with pip
pip install -e .
```

**⚠️ WSL Users**: Clone to your WSL home directory (`/home/username/`), NOT the Windows mount (`/mnt/c/Users/...`).

---

## Configure MCP Clients

### Claude Desktop

**Find config file location:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

**Configuration (pip install):**
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

**Configuration (from source with uv):**
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

**Configuration (from source with Python):**
```json
{
  "mcpServers": {
    "ros-mcp-server": {
      "command": "python",
      "args": ["/absolute/path/to/ros-mcp-server/server.py"]
    }
  }
}
```

After editing, **completely restart Claude Desktop**:
```bash
# macOS/Linux: Kill and restart
pkill -f claude-desktop
# Then relaunch Claude Desktop

# Windows: Use Task Manager to end Claude Desktop, then relaunch
```

### Claude Code (CLI)

```bash
# Add MCP server
claude mcp add-json "ros-mcp-server" \
  '{"command":"uv","args":["--directory","/absolute/path/to/ros-mcp-server","run","server.py"]}'

# Or if installed via pip
claude mcp add-json "ros-mcp-server" '{"command":"ros-mcp","args":[]}'

# Verify it's added
claude mcp list
```

### VS Code / Cursor

Add to your MCP configuration file (`.vscode/mcp.json` or `~/.cursor/mcp.json`):

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

### OpenClaw

Add to your OpenClaw skills or configure as an MCP extension. The ros-mcp-server works as a standard MCP server.

---

## Install rosbridge

rosbridge_server must be installed on the machine running ROS (robot or simulation).

### ROS 2 (Humble/Iron/Jazzy)

```bash
# Install rosbridge_server
sudo apt update
sudo apt install ros-${ROS_DISTRO}-rosbridge-server

# Example for Humble:
sudo apt install ros-humble-rosbridge-server
```

### Launch rosbridge

```bash
# Source your ROS 2 installation (if not already sourced)
source /opt/ros/$ROS_DISTRO/setup.bash

# Source your workspace (if using custom messages)
source ~/ros2_ws/install/setup.bash

# Launch rosbridge
ros2 launch rosbridge_server rosbridge_websocket_launch.xml

# For remote access (bind to all interfaces):
ros2 launch rosbridge_server rosbridge_websocket_launch.xml address:=0.0.0.0
```

**Default Settings:**
- **Port**: 9090
- **Address**: localhost (127.0.0.1) by default
- **Protocol**: WebSocket

---

## OpenClaw Gateway Fix

OpenClaw's gateway runs as a **systemd service** with a hardcoded PATH that does not include `/opt/ros/<distro>/bin`. Without this fix, every bash command the agent runs will fail with `ros2: command not found` — even if your terminal has ROS sourced perfectly.

**One-time fix** — run this after installing the skill:

```bash
# Make sure ROS 2 is sourced in your terminal first
source /opt/ros/humble/setup.bash   # replace humble with your distro

# Run the setup script
chmod +x ~/.openclaw/skills/ros-mcp-skill/reference/openclaw-setup.sh
~/.openclaw/skills/ros-mcp-skill/reference/openclaw-setup.sh
```

The script creates a systemd drop-in at `~/.config/systemd/user/openclaw-gateway.service.d/ros-env.conf` that injects all required ROS 2 environment variables. **Re-run the script if you change your ROS distro.**

> **Why a drop-in?** OpenClaw regenerates its base `.service` file on updates. A drop-in is merged on top automatically, so your fix survives updates.

---

## Verify Installation

### Step 1: Test rosbridge is Running

```bash
# Check if rosbridge is listening on port 9090
# Linux/macOS:
netstat -tlnp | grep 9090
# or
ss -tlnp | grep 9090

# Should show something like:
# tcp  0  0  127.0.0.1:9090  0.0.0.0:*  LISTEN  12345/python3
```

### Step 2: Test MCP Server Connection

In your MCP client (Claude Desktop, etc.), the ros-mcp-server tools should appear. Try:

```
# Connect to rosbridge (localhost)
connect_to_robot()

# Or with explicit parameters
connect_to_robot(ip="127.0.0.1", port=9090)
```

**Expected Response:**
```
Successfully connected to robot at 127.0.0.1:9090
- Ping: OK
- Port 9090: Open
- WebSocket: Connected
```

### Step 3: Discover ROS System

```
# Check ROS version
detect_ros_version()

# List topics
get_topics()

# List services
get_services()

# List nodes
get_nodes()
```

### Step 4: Test with Turtlesim (Optional but Recommended)

**Terminal 1 - Start turtlesim:**
```bash
ros2 run turtlesim turtlesim_node
```

**Terminal 2 - Ensure rosbridge is running**

**In MCP Client:**
```
connect_to_robot()
get_topics()
# Should see /turtle1/cmd_vel, /turtle1/pose, etc.

# Move the turtle
publish_once(
  topic="/turtle1/cmd_vel",
  msg_type="geometry_msgs/Twist",
  msg={"linear": {"x": 2.0}, "angular": {"z": 0.0}}
)
```

If the turtle moves, your setup is complete! 🎉

---

## Platform-Specific Notes

### macOS

- Install ROS 2 via [robostack](https://robostack.github.io/) (conda-based)
- Or use Docker with ROS images

```bash
# Install via conda (robostack)
conda create -n ros_env
conda activate ros_env
conda install -c robostack-staging ros-humble-desktop
conda install -c robostack-staging ros-humble-rosbridge-server
```

### Windows

**Option 1: WSL2 (Recommended)**
```bash
# In WSL2 Ubuntu:
sudo apt install ros-humble-desktop ros-humble-rosbridge-server

# Run rosbridge in WSL2
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

**Option 2: Docker**
```bash
docker run -it --rm -p 9090:9090 osrf/ros:humble-desktop \
  bash -c "source /opt/ros/humble/setup.bash && \
           apt update && apt install -y ros-humble-rosbridge-server && \
           ros2 launch rosbridge_server rosbridge_websocket_launch.xml address:=0.0.0.0"
```

### Linux (Native)

Standard installation as documented above.

### Docker Environments

```yaml
# docker-compose.yml example
version: '3'
services:
  ros2:
    image: osrf/ros:humble-desktop
    ports:
      - "9090:9090"
    command: >
      bash -c "
        apt update && apt install -y ros-humble-rosbridge-server &&
        source /opt/ros/humble/setup.bash &&
        ros2 launch rosbridge_server rosbridge_websocket_launch.xml address:=0.0.0.0
      "
```

```bash
docker-compose up
```

---

## Environment Variables

The ros-mcp-server can be configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ROSBRIDGE_HOST` | `127.0.0.1` | Default rosbridge host |
| `ROSBRIDGE_PORT` | `9090` | Default rosbridge port |

Set in your MCP config:
```json
{
  "mcpServers": {
    "ros-mcp-server": {
      "command": "ros-mcp",
      "args": [],
      "env": {
        "ROSBRIDGE_HOST": "192.168.1.100",
        "ROSBRIDGE_PORT": "9090"
      }
    }
  }
}
```

---

## Network Configuration

### Same Machine (Default)

No special configuration needed. rosbridge binds to localhost by default.

### Remote Robot

1. **On robot**: Bind rosbridge to all interfaces
   ```bash
   ros2 launch rosbridge_server rosbridge_websocket_launch.xml address:=0.0.0.0
   ```

2. **Firewall**: Open port 9090
   ```bash
   sudo ufw allow 9090/tcp
   ```

3. **Connect from MCP**: Use robot's IP address
   ```
   connect_to_robot(ip="192.168.1.100", port=9090)
   ```

### Through VPN/Tailscale

Use the Tailscale IP address of your robot:
```
connect_to_robot(ip="100.x.x.x", port=9090)
```

### SSH Tunnel (Alternative)

```bash
# Create tunnel from local 9090 to robot's 9090
ssh -L 9090:localhost:9090 user@robot-hostname
```

Then connect to localhost:
```
connect_to_robot(ip="127.0.0.1", port=9090)
```

---

## Next Steps

- [🔧 Tool Reference](./tools.md) - Detailed tool documentation
- [🔄 Common Workflows](./workflows.md) - Step-by-step guides
- [🔍 Troubleshooting](./troubleshooting.md) - Solving common issues
