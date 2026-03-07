# TugBot Topics & ros-gz-bridge Configuration

Complete topic reference for the TugBot simulation and the ros-gz-bridge configuration needed
to expose those topics to ROS 2 (and thus to ros-mcp-server).

---

## Topic Overview

TugBot exposes the following ROS 2 topics (after bridging from Gazebo):

### Motion Control

| ROS 2 Topic | Direction | Type | Description |
|-------------|-----------|------|-------------|
| `/cmd_vel` | → Robot | `geometry_msgs/msg/Twist` | Velocity commands (linear.x, angular.z) |

### Localization & State

| ROS 2 Topic | Direction | Type | Description |
|-------------|-----------|------|-------------|
| `/odom` | Robot → | `nav_msgs/msg/Odometry` | Wheel odometry (pose + velocity) |
| `/tf` | Robot → | `tf2_msgs/msg/TFMessage` | Dynamic transform frames |
| `/tf_static` | Robot → | `tf2_msgs/msg/TFMessage` | Static transform frames |
| `/joint_states` | Robot → | `sensor_msgs/msg/JointState` | Wheel joint positions and velocities |

### Sensors

| ROS 2 Topic | Direction | Type | Description |
|-------------|-----------|------|-------------|
| `/scan` | Robot → | `sensor_msgs/msg/LaserScan` | 2D LIDAR scan data |
| `/camera/image_raw` | Robot → | `sensor_msgs/msg/Image` | Camera RGB image |
| `/camera/camera_info` | Robot → | `sensor_msgs/msg/CameraInfo` | Camera calibration info |
| `/imu` | Robot → | `sensor_msgs/msg/Imu` | IMU (accelerometer + gyroscope) |

### Simulation Control

| ROS 2 Topic | Direction | Type | Description |
|-------------|-----------|------|-------------|
| `/clock` | Sim → | `rosgraph_msgs/msg/Clock` | Simulation time |

---

## Gazebo Internal Topic Names

These are the topic names inside Gazebo's transport layer. They must match what your SDF/launch
file defines. Typical TugBot Gazebo topic names:

| Gazebo Topic | Maps To ROS 2 Topic |
|-------------|---------------------|
| `/model/tugbot/cmd_vel` | `/cmd_vel` |
| `/model/tugbot/odometry` | `/odom` |
| `/lidar` | `/scan` |
| `/camera` | `/camera/image_raw` |
| `/camera_info` | `/camera/camera_info` |
| `/imu` | `/imu` |
| `/clock` | `/clock` |

To verify exact Gazebo topic names in your running simulation:

```bash
gz topic --list
gz topic --echo --topic /model/tugbot/odometry   # Test a specific topic
```

---

## ros-gz-bridge Configuration

### Command-line bridge (Jazzy / Gazebo Harmonic — `gz.msgs`)

```bash
ros2 run ros_gz_bridge parameter_bridge \
  "/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist" \
  "/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry" \
  "/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan" \
  "/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image" \
  "/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo" \
  "/imu@sensor_msgs/msg/Imu[gz.msgs.IMU" \
  "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock" \
  "/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V"
```

### Command-line bridge (Humble / Gazebo Fortress — `ignition.msgs`)

```bash
ros2 run ros_gz_bridge parameter_bridge \
  "/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist" \
  "/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry" \
  "/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan" \
  "/camera/image_raw@sensor_msgs/msg/Image[ignition.msgs.Image" \
  "/camera/camera_info@sensor_msgs/msg/CameraInfo[ignition.msgs.CameraInfo" \
  "/imu@sensor_msgs/msg/Imu[ignition.msgs.IMU" \
  "/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock" \
  "/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V"
```

### YAML configuration file (recommended for reproducibility)

Save as `tugbot_bridge.yaml`:

```yaml
# tugbot_bridge.yaml — ros-gz-bridge config for TugBot simulation
# For Jazzy/Harmonic: gz.msgs.*
# For Humble/Fortress: replace gz.msgs with ignition.msgs

---
# Velocity commands (AI → Robot)
- ros_topic_name: /cmd_vel
  gz_topic_name: /model/tugbot/cmd_vel
  ros_type_name: geometry_msgs/msg/Twist
  gz_type_name: gz.msgs.Twist
  direction: ROS_TO_GZ
  lazy: true

# Odometry (Robot → AI)
- ros_topic_name: /odom
  gz_topic_name: /model/tugbot/odometry
  ros_type_name: nav_msgs/msg/Odometry
  gz_type_name: gz.msgs.Odometry
  direction: GZ_TO_ROS
  lazy: true

# LIDAR scan (Robot → AI)
- ros_topic_name: /scan
  gz_topic_name: /lidar
  ros_type_name: sensor_msgs/msg/LaserScan
  gz_type_name: gz.msgs.LaserScan
  direction: GZ_TO_ROS
  lazy: true

# Camera image (Robot → AI)
- ros_topic_name: /camera/image_raw
  gz_topic_name: /camera
  ros_type_name: sensor_msgs/msg/Image
  gz_type_name: gz.msgs.Image
  direction: GZ_TO_ROS
  lazy: true

# Camera info (Robot → AI)
- ros_topic_name: /camera/camera_info
  gz_topic_name: /camera_info
  ros_type_name: sensor_msgs/msg/CameraInfo
  gz_type_name: gz.msgs.CameraInfo
  direction: GZ_TO_ROS
  lazy: true

# IMU (Robot → AI)
- ros_topic_name: /imu
  gz_topic_name: /imu
  ros_type_name: sensor_msgs/msg/Imu
  gz_type_name: gz.msgs.IMU
  direction: GZ_TO_ROS
  lazy: true

# Simulation clock (always bridged for sim time)
- ros_topic_name: /clock
  gz_topic_name: /clock
  ros_type_name: rosgraph_msgs/msg/Clock
  gz_type_name: gz.msgs.Clock
  direction: GZ_TO_ROS
  lazy: false

# TF transforms
- ros_topic_name: /tf
  gz_topic_name: /model/tugbot/pose
  ros_type_name: tf2_msgs/msg/TFMessage
  gz_type_name: gz.msgs.Pose_V
  direction: GZ_TO_ROS
  lazy: true
```

Launch with the YAML config:

```bash
ros2 run ros_gz_bridge parameter_bridge \
  --ros-args -p config_file:=/path/to/tugbot_bridge.yaml
```

---

## Message Type Details

### `/cmd_vel` — geometry_msgs/msg/Twist

TugBot is a **skid-steer robot**: it controls motion via differential wheel speed.

```json
{
  "linear": {
    "x": 0.0,    // Forward/backward speed (m/s). Typical range: -0.5 to 0.5
    "y": 0.0,    // Not used for skid-steer
    "z": 0.0     // Not used
  },
  "angular": {
    "x": 0.0,    // Not used
    "y": 0.0,    // Not used
    "z": 0.0     // Rotation speed (rad/s). Positive = CCW (left). Range: -1.0 to 1.0
  }
}
```

**Safe velocity limits for testing**:
- Linear: ≤ 0.5 m/s
- Angular: ≤ 0.8 rad/s

### `/odom` — nav_msgs/msg/Odometry

```json
{
  "header": {"frame_id": "odom"},
  "child_frame_id": "base_link",
  "pose": {
    "pose": {
      "position": {"x": 0.0, "y": 0.0, "z": 0.0},
      "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
    }
  },
  "twist": {
    "twist": {
      "linear": {"x": 0.0, "y": 0.0, "z": 0.0},
      "angular": {"x": 0.0, "y": 0.0, "z": 0.0}
    }
  }
}
```

Key fields:
- `pose.pose.position.x/y` — Current position in the odom frame
- `pose.pose.orientation.z/w` — Current heading (quaternion, use to compute yaw)
- `twist.twist.linear.x` — Current forward velocity
- `twist.twist.angular.z` — Current rotation rate

### `/scan` — sensor_msgs/msg/LaserScan

```json
{
  "header": {"frame_id": "lidar_link"},
  "angle_min": -3.14,       // Start angle (radians)
  "angle_max": 3.14,        // End angle (radians)
  "angle_increment": 0.01,  // Angular resolution between points
  "range_min": 0.1,         // Minimum valid range (m)
  "range_max": 30.0,        // Maximum valid range (m)
  "ranges": [...]           // Array of distances (meters). 0.0 or inf = invalid
}
```

Key usage:
- Check `ranges[len/2]` for distance straight ahead
- Check `ranges[0]` and `ranges[-1]` for left/right extremes
- Values of `inf` or `0.0` indicate no detection within sensor range

### `/camera/image_raw` — sensor_msgs/msg/Image

```json
{
  "header": {"frame_id": "camera_link"},
  "height": 480,
  "width": 640,
  "encoding": "rgb8",
  "data": [...]    // Raw pixel data
}
```

After receiving, use:
```
analyze_previously_received_image(image_path="./camera/received_image.jpeg")
```

---

## Checking Topics with ros-mcp Tools

```
# List all topics
get_topics()

# Get message type for a topic
get_topic_type(topic="/scan")

# Get full message structure
get_message_details(message_type="sensor_msgs/msg/LaserScan")

# Get publisher/subscriber info
get_topic_details(topic="/cmd_vel")

# Read one message
subscribe_once(topic="/odom", msg_type="nav_msgs/msg/Odometry", timeout=5.0)
```

---

## Nav2 Topics (when navigation stack is running)

If using `tugbot_navigation2` launch file, additional topics become available:

| Topic | Type | Description |
|-------|------|-------------|
| `/map` | `nav_msgs/msg/OccupancyGrid` | Static or SLAM map |
| `/global_costmap/costmap` | `nav_msgs/msg/OccupancyGrid` | Global planning costmap |
| `/local_costmap/costmap` | `nav_msgs/msg/OccupancyGrid` | Local obstacle avoidance costmap |
| `/plan` | `nav_msgs/msg/Path` | Current planned path |
| `/cmd_vel_nav` | `geometry_msgs/msg/Twist` | Nav2's velocity output |

Nav2 actions (via `get_actions()`):
- `/navigate_to_pose`
- `/navigate_through_poses`
- `/follow_path`
- `/compute_path_to_pose`

See [workflows.md](./workflows.md#navigation-with-nav2) for Nav2 usage.
