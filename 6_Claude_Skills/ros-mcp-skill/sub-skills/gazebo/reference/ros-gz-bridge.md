# ros-gz-bridge Configuration Reference

The `ros_gz_bridge` package provides bidirectional communication between ROS 2 and Gazebo's
internal transport system. This document covers all configuration methods and patterns.

---

## Table of Contents

1. [How the Bridge Works](#how-the-bridge-works)
2. [Command-Line Bridge](#command-line-bridge)
3. [YAML Configuration](#yaml-configuration)
4. [Launch File Integration](#launch-file-integration)
5. [Supported Message Types](#supported-message-types)
6. [Bridge Direction Flags](#bridge-direction-flags)
7. [Common Robot Topic Mappings](#common-robot-topic-mappings)
8. [Advanced Options](#advanced-options)

---

## How the Bridge Works

Gazebo and ROS 2 have independent transport systems:
- **Gazebo**: Uses `gz-transport` (or `ignition-transport`) with its own topic namespace and message format
- **ROS 2**: Uses DDS with standard ROS message types

The bridge (`parameter_bridge`) acts as a translator:

```
ROS 2 Topic                    Gazebo Topic
/cmd_vel (Twist)    ←→    /model/robot/cmd_vel (gz.msgs.Twist)
/odom (Odometry)    ←→    /model/robot/odometry (gz.msgs.Odometry)
/scan (LaserScan)   ←      /lidar (gz.msgs.LaserScan)
```

The Gazebo topic names come from your **SDF/world file** (how the model is defined).
The ROS topic names are what you choose to expose.

---

## Command-Line Bridge

### Syntax

```bash
ros2 run ros_gz_bridge parameter_bridge \
  "<ros_topic>@<ros_type><direction><gz_type>" \
  "<ros_topic>@<ros_type><direction><gz_type>"
```

### Direction symbols

| Symbol | Meaning |
|--------|---------|
| `@` (between types) | Bidirectional |
| `[` (between types) | Gazebo → ROS only |
| `]` (between types) | ROS → Gazebo only |

### Example

```bash
ros2 run ros_gz_bridge parameter_bridge \
  "/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist" \
  "/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry" \
  "/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan" \
  "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"
```

### Humble (Fortress) — use `ignition.msgs` namespace

```bash
ros2 run ros_gz_bridge parameter_bridge \
  "/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist" \
  "/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry" \
  "/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan"
```

---

## YAML Configuration

For complex setups with many topics, use a YAML config file. This is the recommended approach
for reproducible setups.

### Create a bridge config file

```yaml
# bridge_config.yaml
---
- ros_topic_name: /cmd_vel
  gz_topic_name: /model/my_robot/cmd_vel
  ros_type_name: geometry_msgs/msg/Twist
  gz_type_name: gz.msgs.Twist
  direction: ROS_TO_GZ
  lazy: true

- ros_topic_name: /odom
  gz_topic_name: /model/my_robot/odometry
  ros_type_name: nav_msgs/msg/Odometry
  gz_type_name: gz.msgs.Odometry
  direction: GZ_TO_ROS
  lazy: true

- ros_topic_name: /scan
  gz_topic_name: /lidar
  ros_type_name: sensor_msgs/msg/LaserScan
  gz_type_name: gz.msgs.LaserScan
  direction: GZ_TO_ROS
  lazy: true

- ros_topic_name: /camera/image_raw
  gz_topic_name: /camera
  ros_type_name: sensor_msgs/msg/Image
  gz_type_name: gz.msgs.Image
  direction: GZ_TO_ROS
  lazy: true

- ros_topic_name: /camera/camera_info
  gz_topic_name: /camera_info
  ros_type_name: sensor_msgs/msg/CameraInfo
  gz_type_name: gz.msgs.CameraInfo
  direction: GZ_TO_ROS
  lazy: true

- ros_topic_name: /imu
  gz_topic_name: /imu
  ros_type_name: sensor_msgs/msg/Imu
  gz_type_name: gz.msgs.IMU
  direction: GZ_TO_ROS
  lazy: true

- ros_topic_name: /clock
  gz_topic_name: /clock
  ros_type_name: rosgraph_msgs/msg/Clock
  gz_type_name: gz.msgs.Clock
  direction: GZ_TO_ROS
  lazy: false   # Clock should always bridge
```

### Launch with YAML config

```bash
ros2 run ros_gz_bridge parameter_bridge \
  --ros-args -p config_file:=/path/to/bridge_config.yaml
```

### Direction values in YAML

| Value | Meaning |
|-------|---------|
| `BIDIRECTIONAL` | Both directions |
| `ROS_TO_GZ` | ROS → Gazebo |
| `GZ_TO_ROS` | Gazebo → ROS |

---

## Launch File Integration

### Python launch file (recommended)

```python
# my_bridge.launch.py
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # Path to bridge config
    bridge_config = os.path.join(
        get_package_share_directory('my_package'),
        'config',
        'bridge_config.yaml'
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': bridge_config,
            'qos_overrides./tf_static.publisher.durability': 'transient_local',
        }],
        output='screen'
    )

    return LaunchDescription([bridge])
```

### Inline bridge topics in a launch file

```python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
        ],
        output='screen'
    )

    return LaunchDescription([bridge])
```

---

## Supported Message Types

### Geometry

| ROS 2 Type | Gazebo Type |
|------------|-------------|
| `geometry_msgs/msg/Twist` | `gz.msgs.Twist` |
| `geometry_msgs/msg/Pose` | `gz.msgs.Pose` |
| `geometry_msgs/msg/PoseStamped` | `gz.msgs.Pose` |
| `geometry_msgs/msg/PoseArray` | `gz.msgs.Pose_V` |
| `geometry_msgs/msg/Transform` | `gz.msgs.Pose` |
| `geometry_msgs/msg/TransformStamped` | `gz.msgs.Pose` |
| `geometry_msgs/msg/Wrench` | `gz.msgs.Wrench` |
| `geometry_msgs/msg/Vector3` | `gz.msgs.Vector3d` |
| `geometry_msgs/msg/Point` | `gz.msgs.Vector3d` |

### Navigation

| ROS 2 Type | Gazebo Type |
|------------|-------------|
| `nav_msgs/msg/Odometry` | `gz.msgs.Odometry` |
| `nav_msgs/msg/OccupancyGrid` | `gz.msgs.OccupancyGrid` |

### Sensors

| ROS 2 Type | Gazebo Type |
|------------|-------------|
| `sensor_msgs/msg/LaserScan` | `gz.msgs.LaserScan` |
| `sensor_msgs/msg/Image` | `gz.msgs.Image` |
| `sensor_msgs/msg/CameraInfo` | `gz.msgs.CameraInfo` |
| `sensor_msgs/msg/Imu` | `gz.msgs.IMU` |
| `sensor_msgs/msg/PointCloud2` | `gz.msgs.PointCloudPacked` |
| `sensor_msgs/msg/JointState` | `gz.msgs.Model` |
| `sensor_msgs/msg/BatteryState` | `gz.msgs.BatteryState` |
| `sensor_msgs/msg/MagneticField` | `gz.msgs.Magnetometer` |
| `sensor_msgs/msg/FluidPressure` | `gz.msgs.FluidPressure` |

### Standard / System

| ROS 2 Type | Gazebo Type |
|------------|-------------|
| `std_msgs/msg/Bool` | `gz.msgs.Boolean` |
| `std_msgs/msg/Float32` | `gz.msgs.Float` |
| `std_msgs/msg/Float64` | `gz.msgs.Double` |
| `std_msgs/msg/Int32` | `gz.msgs.Int32` |
| `std_msgs/msg/String` | `gz.msgs.StringMsg` |
| `std_msgs/msg/Header` | `gz.msgs.Header` |
| `std_msgs/msg/Empty` | `gz.msgs.Empty` |
| `rosgraph_msgs/msg/Clock` | `gz.msgs.Clock` |

### Transforms

| ROS 2 Type | Gazebo Type |
|------------|-------------|
| `tf2_msgs/msg/TFMessage` | `gz.msgs.Pose_V` |

### For Humble/Fortress: Replace `gz.msgs` with `ignition.msgs`

---

## Bridge Direction Flags

### When to use each direction

**`ROS_TO_GZ` (or `]` in CLI)**: Use for commands from ROS to Gazebo
- `/cmd_vel` (velocity commands)
- `/joint_command` (joint position/velocity control)

**`GZ_TO_ROS` (or `[` in CLI)**: Use for sensor data from Gazebo to ROS
- `/odom` (odometry)
- `/scan` (LIDAR)
- `/camera/image_raw`
- `/imu`
- `/clock`

**`BIDIRECTIONAL` (or `@` in CLI)**: Use when data flows both ways
- `/tf` (transforms can originate from either side)
- Any topic where you need to both publish and subscribe

---

## Common Robot Topic Mappings

### Typical Gazebo SDF → ROS 2 topic name patterns

Gazebo topics in SDF are often namespaced under `/model/<model_name>/`. You can verify by
checking available Gazebo topics:

```bash
gz topic --list
```

### Generic mobile robot

```yaml
- ros_topic_name: /cmd_vel
  gz_topic_name: /model/<robot_name>/cmd_vel
  ros_type_name: geometry_msgs/msg/Twist
  gz_type_name: gz.msgs.Twist
  direction: ROS_TO_GZ

- ros_topic_name: /odom
  gz_topic_name: /model/<robot_name>/odometry
  ros_type_name: nav_msgs/msg/Odometry
  gz_type_name: gz.msgs.Odometry
  direction: GZ_TO_ROS
```

### TF bridge (sim time + transforms)

```bash
ros2 run ros_gz_bridge parameter_bridge \
  "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock" \
  "/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V"
```

### Use sim time in ROS nodes

```bash
ros2 run my_node my_node --ros-args -p use_sim_time:=true
```

---

## Advanced Options

### Lazy bridging

With `lazy: true` (default), the bridge only subscribes to the Gazebo side when there is an
active ROS subscriber. This saves bandwidth and CPU:

```yaml
- ros_topic_name: /camera/image_raw
  gz_topic_name: /camera
  ros_type_name: sensor_msgs/msg/Image
  gz_type_name: gz.msgs.Image
  direction: GZ_TO_ROS
  lazy: true    # Only bridges when someone subscribes on the ROS side
```

### QoS overrides

For topics that need specific QoS (like `/tf_static` which needs transient local):

```python
Node(
    package='ros_gz_bridge',
    executable='parameter_bridge',
    parameters=[{
        'qos_overrides./tf_static.publisher.durability': 'transient_local',
    }]
)
```

### Override frame IDs

If the Gazebo frame IDs differ from what your ROS stack expects:

```yaml
- ros_topic_name: /scan
  gz_topic_name: /lidar
  ros_type_name: sensor_msgs/msg/LaserScan
  gz_type_name: gz.msgs.LaserScan
  direction: GZ_TO_ROS
  override_frame_id: 'lidar_link'   # Replace whatever Gazebo sends
```

### Use wall clock instead of sim time

```yaml
- ros_topic_name: /imu
  gz_topic_name: /imu
  ros_type_name: sensor_msgs/msg/Imu
  gz_type_name: gz.msgs.IMU
  direction: GZ_TO_ROS
  override_timestamps_with_wall_time: true
```

---

## Debugging the Bridge

### List all Gazebo topics (to find the correct gz_topic_name)

```bash
gz topic --list

# Echo a specific Gazebo topic to see what it publishes
gz topic --echo --topic /model/my_robot/cmd_vel
```

### List ROS 2 topics (after bridge is running)

```bash
ros2 topic list
ros2 topic echo /cmd_vel
```

### Check bridge node parameters

```bash
ros2 node list          # Find the ros_gz_bridge node name
ros2 node info /ros_gz_bridge
ros2 param list /ros_gz_bridge
```

### Monitor bridge with ros-mcp

```
get_nodes()             # Verify ros_gz_bridge node is listed
get_topics()            # Verify bridged topics appear
subscribe_once(topic="/odom", msg_type="nav_msgs/msg/Odometry")  # Test data flow
```
