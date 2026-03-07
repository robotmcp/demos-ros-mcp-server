# Gazebo + ros-gz-bridge Troubleshooting

Common issues and their solutions when running Gazebo simulations with ros-mcp-server.

---

## Quick Diagnostic Checklist

Run through this checklist before diving into specific issues:

```bash
# 1. Is ROS 2 sourced?
echo $ROS_DISTRO   # Should print: humble / jazzy / etc.

# 2. Is Gazebo running?
gz sim --list-worlds  # or check for the gz sim process
ps aux | grep gz

# 3. Is ros-gz-bridge running?
ros2 node list | grep ros_gz_bridge

# 4. Is rosbridge running?
ss -tlnp | grep 9090

# 5. Are topics visible?
ros2 topic list
```

In your AI client:
```
connect_to_robot()
get_topics()
get_nodes()
```

---

## Common Issues

### 1. `connect_to_robot()` fails — "Connection refused"

**Cause**: rosbridge_server is not running.

**Fix**:
```bash
source /opt/ros/$ROS_DISTRO/setup.bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

Verify it's running:
```bash
ss -tlnp | grep 9090
```

---

### 2. `get_topics()` returns an empty list or is missing Gazebo topics

**Cause A**: ros-gz-bridge is not running.

**Fix**: Start the bridge:
```bash
ros2 run ros_gz_bridge parameter_bridge \
  "/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist" \
  "/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry"
```

**Cause B**: The bridge is running but using wrong Gazebo topic names.

**Fix**: Check actual Gazebo topic names:
```bash
gz topic --list
```

Then update your bridge config to match the actual names.

**Cause C**: Gazebo simulation is not running.

**Fix**: Start your Gazebo world first, then start the bridge.

---

### 3. `subscribe_once()` on `/odom` times out

**Cause A**: Bridge is running but Gazebo is paused.

**Fix**: Unpause the simulation (press the play button in Gazebo GUI, or via service call).

**Cause B**: Lazy bridging — no active Gazebo publisher yet.

**Fix**: Ensure Gazebo simulation is actively running (not paused) with a robot that publishes odometry. Try interacting with the simulation first.

**Cause C**: Wrong message type.

**Fix**: Verify with `get_topic_type(topic="/odom")` and use the exact type returned.

---

### 4. Velocity commands (`/cmd_vel`) are published but robot doesn't move

**Cause A**: Bridge direction is wrong — set to `GZ_TO_ROS` instead of `ROS_TO_GZ`.

**Fix**: Check and correct the bridge direction:
```yaml
direction: ROS_TO_GZ   # for /cmd_vel
```

**Cause B**: Wrong Gazebo topic name — the robot model may not subscribe to the topic name you're bridging to.

**Fix**:
```bash
# List Gazebo topics to find the correct name
gz topic --list
# Look for something like /model/tugbot/cmd_vel or /robot/cmd_vel
```

Then update the `gz_topic_name` in your bridge config.

**Cause C**: The simulation is paused.

**Fix**: Resume the simulation from the Gazebo GUI or via:
```bash
gz service --service /world/default/control \
  --reqtype gz.msgs.WorldControl \
  --reptype gz.msgs.Boolean \
  --timeout 2000 \
  --req "pause: false"
```

---

### 5. `parameter_bridge` crashes or exits immediately

**Cause A**: Wrong message namespace for your distro.

**Fix**: Check your ROS/Gazebo pairing:
- Humble + Fortress: use `ignition.msgs.*`
- Jazzy + Harmonic: use `gz.msgs.*`

```bash
# Humble + Fortress example:
ros2 run ros_gz_bridge parameter_bridge \
  "/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist"
```

**Cause B**: Malformed bridge argument string.

**Fix**: Double-check the syntax — the direction character goes between the two type names:
```bash
# Correct:
"/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry"
# Wrong:
"/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry["
```

**Cause C**: ros-gz-bridge package not installed.

**Fix**:
```bash
sudo apt install ros-$ROS_DISTRO-ros-gz-bridge
```

---

### 6. Topics appear in ROS but data is not flowing

**Cause**: Gazebo side may not be publishing because the bridge is using lazy mode and no subscriber is active on the ROS side, or Gazebo simulation is not running.

**Fix**: Verify the Gazebo side is actively publishing:
```bash
gz topic --echo --topic /model/my_robot/odometry
```

If nothing prints, the robot model may not be set up to publish on that topic. Check the SDF file for sensor/plugin definitions.

---

### 7. Camera image topic exists but `subscribe_once` returns nothing

**Cause A**: Camera plugin not configured in SDF/URDF.

**Fix**: Check the robot's SDF file has a camera sensor and ros_gz plugin:
```xml
<sensor name="camera" type="camera">
  <camera>
    <horizontal_fov>1.047</horizontal_fov>
    <image><width>640</width><height>480</height></image>
  </camera>
  <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
    <render_engine>ogre2</render_engine>
  </plugin>
</sensor>
```

**Cause B**: Timeout too short for high-resolution images.

**Fix**:
```
subscribe_once(
  topic="/camera/image_raw",
  msg_type="sensor_msgs/msg/Image",
  timeout=15.0,
  expects_image="true"
)
```

---

### 8. Simulation time vs. wall clock issues

**Symptom**: TF errors, timestamp mismatches, nav2 not working.

**Fix**: Use sim time across all nodes:
```bash
ros2 run my_node my_node --ros-args -p use_sim_time:=true
```

And ensure `/clock` is bridged:
```bash
ros2 run ros_gz_bridge parameter_bridge \
  "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"
```

---

### 9. `ros2 node list` doesn't show `ros_gz_bridge`

**Cause**: The bridge process crashed or was never started.

**Fix**: Start it again in a terminal:
```bash
source /opt/ros/$ROS_DISTRO/setup.bash
ros2 run ros_gz_bridge parameter_bridge \
  "/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist" \
  "/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry"
```

Watch the terminal for error messages.

---

### 10. `detect_ros_version()` fails or returns unknown

**Cause**: rosbridge is running but ROS 2 has no active nodes beyond rosbridge itself.

**Fix**: Ensure your simulation launch file is running and nodes are active:
```bash
ros2 node list
```

Start your simulation first, then check again.

---

## Full Reset Procedure

If things are in a broken state, do a full clean restart:

```bash
# 1. Kill everything
pkill -f gz
pkill -f ros_gz_bridge
pkill -f rosbridge

# 2. Clean up any zombie ROS 2 daemon
ros2 daemon stop && ros2 daemon start

# 3. Re-source ROS 2
source /opt/ros/$ROS_DISTRO/setup.bash
# If using a workspace:
source ~/ros2_ws/install/setup.bash

# 4. Restart in order:
#    Terminal 1: Gazebo
#    Terminal 2: ros-gz-bridge
#    Terminal 3: rosbridge
```

---

## Useful Debug Commands

```bash
# Check Gazebo topics
gz topic --list

# Echo a Gazebo topic
gz topic --echo --topic /model/my_robot/cmd_vel

# Check ROS 2 topics
ros2 topic list
ros2 topic echo /odom
ros2 topic hz /scan         # Check publish rate

# Check all active nodes
ros2 node list

# Check who is publishing to a topic
ros2 topic info /cmd_vel

# Check rosbridge port
ss -tlnp | grep 9090

# Check for process errors
journalctl -u ros_gz_bridge --no-pager -n 50
```

---

## Getting Help

- Check [ROS Answers](https://answers.ros.org/) for ros_gz_bridge questions
- Check [Gazebo Community](https://community.gazebosim.org/) for simulation issues
- Refer to [ros-gz-bridge docs](./ros-gz-bridge.md) for configuration details
- For TugBot-specific issues, see [TugBot troubleshooting](../sub-skills/tugbot/SKILL.md#troubleshooting)
