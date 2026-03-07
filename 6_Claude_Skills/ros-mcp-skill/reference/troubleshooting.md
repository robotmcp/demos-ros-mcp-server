# ROS-MCP Server Troubleshooting Guide

Solutions for common issues when using the ROS-MCP Server.

---

## Table of Contents

1. [Connection Issues](#connection-issues)
2. [Topic Issues](#topic-issues)
3. [Service Issues](#service-issues)
4. [Action Issues](#action-issues)
5. [Parameter Issues](#parameter-issues)
6. [Message Type Issues](#message-type-issues)
7. [Performance Issues](#performance-issues)
8. [Platform-Specific Issues](#platform-specific-issues)
9. [Diagnostic Commands](#diagnostic-commands)

---

## Connection Issues

### Problem: `ros2`: command not found (or ROS commands fail silently)

**Symptoms**: Any `ros2` command fails, or the agent attempts `rosrun`/`roslaunch` and those fail.

**Cause**: ROS 2 environment not sourced in the current shell.

**Fix**:
```bash
# Check if ROS 2 is sourced
echo $ROS_DISTRO   # Should print: humble / iron / jazzy

# If empty, source it:
source /opt/ros/humble/setup.bash    # replace humble with your distro

# If using a custom workspace too:
source ~/ros2_ws/install/setup.bash

# Verify:
ros2 --version
```

**Permanent fix** — add to `~/.bashrc`:
```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

> **Note**: Do NOT use `rosrun`, `roslaunch`, or `roscore` — these are ROS 1 commands. Always use `ros2 run`, `ros2 launch`.

---

### Problem: "Connection refused"

**Symptoms**: `connect_to_robot()` fails with connection refused error.

**Causes & Solutions**:

| Cause | Solution |
|-------|----------|
| rosbridge not running | Start rosbridge: `ros2 launch rosbridge_server rosbridge_websocket_launch.xml` |
| Wrong port | Default is 9090, verify with `ss -tlnp \| grep 9090` |
| Firewall blocking | Open port: `sudo ufw allow 9090/tcp` |
| Wrong IP address | Verify robot IP with `hostname -I` on robot |

**Diagnostic steps**:
```python
# Step 1: Ping the robot
ping_robot(ip="192.168.1.100", port=9090)

# If ping succeeds but port fails:
# → rosbridge is not running

# If ping fails:
# → Network issue or wrong IP
```

---

### Problem: Ping succeeds but port check fails

**Symptoms**: `ping_robot()` shows IP is reachable but port 9090 is closed.

**Solution**: Start rosbridge on the robot:

```bash
source /opt/ros/$ROS_DISTRO/setup.bash   # if not already sourced
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

**Verify rosbridge is running**:
```bash
ss -tlnp | grep 9090
# or
ros2 node list | grep rosbridge
```

---

### Problem: Cannot connect to remote robot

**Symptoms**: Works locally but not from another machine.

**Causes & Solutions**:

1. **rosbridge bound to localhost only**
   ```bash
   # Launch with address binding to all interfaces:
   ros2 launch rosbridge_server rosbridge_websocket_launch.xml address:=0.0.0.0
   ```

2. **Firewall on robot**
   ```bash
   sudo ufw allow 9090/tcp
   ```

3. **Network segmentation**
   - Ensure both machines are on same network/subnet
   - Try using direct IP, not hostname

4. **VPN/Tailscale**
   - Use Tailscale IP instead of local IP

---

### Problem: MCP server not appearing in Claude Desktop

**Symptoms**: ros-mcp-server tools don't show up in Claude.

**Solutions**:

1. **Verify config file syntax**
   ```json
   {
     "mcpServers": {
       "ros-mcp-server": {
         "command": "uv",
         "args": ["--directory", "/path/to/ros-mcp-server", "run", "server.py"]
       }
     }
   }
   ```

2. **Use absolute paths** - Relative paths may not work

3. **Restart Claude Desktop completely**
   ```bash
   # Kill all Claude processes
   pkill -f claude-desktop
   
   # Restart
   claude-desktop
   ```

4. **Check Claude Desktop logs** for MCP errors

---

## Topic Issues

### Problem: "Topic not found"

**Symptoms**: Cannot subscribe to or publish to a topic.

**Diagnostic steps**:
```python
# List all available topics
get_topics()

# Check exact topic name (case-sensitive!)
# Common mistake: /Cmd_vel vs /cmd_vel
```

**Common causes**:
- Typo in topic name
- Node publishing topic isn't running
- Topic is namespaced (e.g., `/robot1/cmd_vel` not `/cmd_vel`)

---

### Problem: Subscribe returns no data / timeout

**Symptoms**: `subscribe_once()` times out.

**Causes & Solutions**:

1. **No publisher on topic**
   ```python
   # Check if topic has publishers
   get_topic_details(topic="/your_topic")
   # Look for "publishers" in response
   ```

2. **Publisher rate too slow**
   ```python
   # Increase timeout
   subscribe_once(topic="/slow_topic", msg_type="...", timeout=30.0)
   ```

3. **Wrong message type**
   ```python
   # Get correct type
   get_topic_type(topic="/your_topic")
   ```

---

### Problem: Publish doesn't seem to work

**Symptoms**: `publish_once()` succeeds but robot doesn't respond.

**Checklist**:

1. **Verify topic exists and has subscriber**
   ```python
   get_topic_details(topic="/cmd_vel")
   # Check "subscribers" list
   ```

2. **Check message format**
   ```python
   get_message_details(message_type="geometry_msgs/Twist")
   # Ensure your message matches
   ```

3. **Robot may need continuous commands**
   - Some robots stop if they don't receive commands continuously
   - Use `publish_for_durations()` instead

4. **Check robot state**
   - Emergency stop engaged?
   - Motors enabled?
   - Safety system active?

---

### Problem: Messages silently dropped (ROS 2)

**Symptoms**: Publish succeeds but subscriber never receives.

**Cause**: QoS (Quality of Service) mismatch between publisher and subscriber.

**Solution**: The ROS-MCP server typically uses compatible QoS, but the robot node might have strict requirements. Check the robot's documentation for required QoS settings.

---

## Service Issues

### Problem: Service call timeout

**Symptoms**: `call_service()` hangs or times out.

**Causes & Solutions**:

1. **Service not available**
   ```python
   # List available services
   get_services()
   
   # Check if your service is listed
   ```

2. **Service is slow**
   ```python
   # Increase timeout
   call_service(
     service_name="/slow_service",
     service_type="...",
     request={},
     timeout=60.0
   )
   ```

3. **Wrong service type**
   ```python
   # Get correct type
   get_service_type(service="/your_service")
   ```

---

### Problem: Service call returns error

**Symptoms**: Service call fails with request format error.

**Solution**: Check request field names:
```python
# Get correct field names
get_service_details(service="/spawn")

# Use EXACTLY those field names
# Don't add underscores or change case
```

**Common mistake**:
```python
# WRONG (added underscore)
request={"_x": 5.0, "_y": 5.0}

# CORRECT
request={"x": 5.0, "y": 5.0}
```

---

## Action Issues

### Problem: Actions not available

**Symptoms**: `get_actions()` returns empty list.

**Possible causes**:
- No action servers running in the current ROS 2 session
- rosbridge version doesn't support actions

**Verify ROS version**:
```python
detect_ros_version()
```

**Check running nodes**:
```bash
ros2 node list
```

---

### Problem: Action goal fails immediately

**Symptoms**: `send_action_goal()` returns failure.

**Solutions**:

1. **Check action interface**
   ```python
   get_action_details(action="/your_action")
   # Verify goal structure matches
   ```

2. **Check action server state**
   ```python
   get_action_status(action_name="/your_action")
   ```

3. **Verify prerequisites** (e.g., Nav2 needs a map)

---

## Parameter Issues

### Problem: Parameter not found

**Symptoms**: `get_parameter()` fails.

**Note**: Parameter tools only work with ROS 2.

**Solutions**:
```python
# Verify ROS 2
detect_ros_version()

# List all parameters for the node
get_parameters(node_name="/your_node")

# Check parameter name format: /node:param_name
get_parameter(name="/turtlesim:background_r")
```

---

### Problem: Parameter change has no effect

**Symptoms**: `set_parameter()` succeeds but behavior doesn't change.

**Possible causes**:
- Node doesn't dynamically reload parameters
- Need to call a service to apply changes

**Solution for turtlesim example**:
```python
# Change parameter
set_parameter(name="/turtlesim:background_r", value="255")

# Apply by clearing (forces redraw)
call_service(service_name="/clear", service_type="std_srvs/Empty", request={})
```

---

## Message Type Issues

### Problem: "Unknown message type"

**Symptoms**: Can't subscribe/publish due to message type error.

**Solutions**:

1. **Check exact type name**
   ```python
   get_topic_type(topic="/your_topic")
   ```

2. **Message type syntax** — use either form, the MCP server handles both:
   - Shorthand: `geometry_msgs/Twist`
   - Full ROS 2 style: `geometry_msgs/msg/Twist`

3. **Custom messages not found**
   - Ensure workspace is sourced before starting rosbridge
   ```bash
   source ~/ros2_ws/install/setup.bash
   ros2 launch rosbridge_server rosbridge_websocket_launch.xml
   ```

---

### Problem: Message structure mismatch

**Symptoms**: Publish fails with structure error.

**Solution**: Use `get_message_details()` to see exact structure:
```python
get_message_details(message_type="geometry_msgs/Twist")
```

Then match your message exactly:
```python
# Full structure
msg={
  "linear": {"x": 0.0, "y": 0.0, "z": 0.0},
  "angular": {"x": 0.0, "y": 0.0, "z": 0.0}
}

# Partial (unset fields default to zero)
msg={"linear": {"x": 0.5}}
```

---

## Performance Issues

### Problem: Slow response times

**Symptoms**: Commands take a long time to execute.

**Solutions**:

1. **Network latency**
   - Use wired connection instead of WiFi
   - Check network with `ping`

2. **High-bandwidth topics**
   ```python
   # Use throttling
   subscribe_once(
     topic="/camera/image_raw",
     msg_type="sensor_msgs/Image",
     throttle_rate_ms=1000
   )
   ```

3. **rosbridge overloaded**
   - Too many subscriptions
   - Reduce subscription frequency

---

### Problem: Image topics very slow

**Symptoms**: Camera subscriptions timeout or take very long.

**Solutions**:

1. **Use image hint**
   ```python
   subscribe_once(
     topic="/camera/image_raw",
     msg_type="sensor_msgs/Image",
     expects_image="true",  # Faster processing
     timeout=30.0
   )
   ```

2. **Use compressed topics if available**
   ```python
   subscribe_once(
     topic="/camera/image_raw/compressed",
     msg_type="sensor_msgs/CompressedImage"
   )
   ```

3. **Reduce image resolution** at the source

---

## Platform-Specific Issues

### WSL2 Issues

**Problem**: Can't connect to rosbridge running in WSL2 from Windows.

**Solution**: 
```bash
# In WSL2, bind to all interfaces
ros2 launch rosbridge_server rosbridge_websocket_launch.xml address:=0.0.0.0

# Find WSL2 IP
hostname -I

# Connect using that IP from Windows
```

---

### Docker Issues

**Problem**: Can't reach rosbridge in Docker container.

**Solution**: Expose port in docker-compose or docker run:
```yaml
# docker-compose.yml
ports:
  - "9090:9090"
```
```bash
# docker run
docker run -p 9090:9090 ...
```

---

### macOS Issues

**Problem**: ROS not available on macOS.

**Solutions**:
1. Use Docker
2. Use robostack (conda)
3. Run rosbridge on a Linux machine and connect remotely

---

## Diagnostic Commands

### Quick System Check

```python
# 1. Test connection
connect_to_robot(ip="192.168.1.100", port=9090)

# 2. Check ROS version
detect_ros_version()

# 3. List everything
get_nodes()
get_topics()
get_services()

# 4. For ROS 2
get_actions()
```

### Check Specific Interface

```python
# Topic
get_topic_type(topic="/cmd_vel")
get_topic_details(topic="/cmd_vel")
get_message_details(message_type="geometry_msgs/Twist")

# Service
get_service_type(service="/spawn")
get_service_details(service="/spawn")

# Node
get_node_details(node="/turtlesim")
```

### Verify Data Flow

```python
# Check if topic has data
subscribe_once(topic="/your_topic", msg_type="...", timeout=5.0)

# Monitor for a period
subscribe_for_duration(
  topic="/your_topic",
  msg_type="...",
  duration=10,
  max_messages=5
)
```

---

## Getting Help

### Check rosbridge Logs

```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml --screen
```

### Check MCP Server Logs

Enable verbose logging in your MCP client configuration or check Claude Desktop's developer console.

### Report Issues

For persistent issues, report to:
- https://github.com/robotmcp/ros-mcp-server/issues

Include:
- ROS version and distribution
- rosbridge version
- Error messages
- Steps to reproduce
