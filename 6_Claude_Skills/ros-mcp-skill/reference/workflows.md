# ROS-MCP Server Common Workflows

Step-by-step guides for common robot control scenarios.

---

## Table of Contents

1. [Initial Connection Workflow](#initial-connection-workflow)
2. [System Discovery Workflow](#system-discovery-workflow)
3. [Mobile Robot Control](#mobile-robot-control)
4. [Sensor Data Collection](#sensor-data-collection)
5. [Camera/Vision Workflow](#cameravision-workflow)
6. [Navigation (Nav2)](#navigation-nav2)
7. [Parameter Configuration](#parameter-configuration)
8. [Turtlesim Complete Demo](#turtlesim-complete-demo)
9. [Multi-Robot Setup](#multi-robot-setup)

---

## Initial Connection Workflow

**When to use**: Starting a new session with any robot.

### Step 1: Test Connectivity

```python
# First, check if the robot is reachable
ping_robot(ip="192.168.1.100", port=9090)
```

**Expected output**: IP reachable, port 9090 open.

**If ping succeeds but port fails**: rosbridge is not running on the robot.

### Step 2: Connect

```python
# Connect to the robot
connect_to_robot(ip="192.168.1.100", port=9090)
```

### Step 3: Verify ROS Environment

```python
# Check what ROS version is running
detect_ros_version()
```

### Step 4: Check for Verified Robot Specs (Optional)

```python
# See if your robot has a pre-defined spec
get_verified_robots_list()

# If your robot is listed, load its spec
get_verified_robot_spec(name="your_robot_name")
```

---

## System Discovery Workflow

**When to use**: Understanding what a robot can do.

### Step 1: Discover All Interfaces

```python
# List all topics
get_topics()

# List all services  
get_services()

# List all nodes
get_nodes()

# ROS 2 only: List actions
get_actions()
```

### Step 2: Explore Specific Topics

```python
# Find interesting topic from the list, e.g., /cmd_vel
get_topic_type(topic="/cmd_vel")
# Returns: geometry_msgs/Twist

# Understand the message structure
get_message_details(message_type="geometry_msgs/Twist")
```

### Step 3: Explore Services

```python
# Get service type
get_service_type(service="/spawn")

# Get full service interface
get_service_details(service="/spawn")
```

### Step 4: Understand Node Capabilities

```python
# See what a specific node provides
get_node_details(node="/turtlesim")
```

---

## Mobile Robot Control

**When to use**: Controlling wheeled robots via velocity commands.

### Basic Movement Commands

```python
# Move forward at 0.5 m/s
publish_once(
  topic="/cmd_vel",
  msg_type="geometry_msgs/Twist",
  msg={"linear": {"x": 0.5}}
)

# Move backward
publish_once(
  topic="/cmd_vel",
  msg_type="geometry_msgs/Twist",
  msg={"linear": {"x": -0.5}}
)

# Rotate left (counter-clockwise)
publish_once(
  topic="/cmd_vel",
  msg_type="geometry_msgs/Twist",
  msg={"angular": {"z": 0.5}}
)

# Rotate right (clockwise)
publish_once(
  topic="/cmd_vel",
  msg_type="geometry_msgs/Twist",
  msg={"angular": {"z": -0.5}}
)

# Stop
publish_once(
  topic="/cmd_vel",
  msg_type="geometry_msgs/Twist",
  msg={}
)
```

### Drive a Pattern

```python
# Drive a square: forward, turn, forward, turn, forward, turn, forward, stop
publish_for_durations(
  topic="/cmd_vel",
  msg_type="geometry_msgs/Twist",
  messages=[
    {"linear": {"x": 0.5}},      # Forward
    {"angular": {"z": 1.57}},    # Turn 90°
    {"linear": {"x": 0.5}},      # Forward
    {"angular": {"z": 1.57}},    # Turn 90°
    {"linear": {"x": 0.5}},      # Forward
    {"angular": {"z": 1.57}},    # Turn 90°
    {"linear": {"x": 0.5}},      # Forward
    {}                           # Stop
  ],
  durations=[2.0, 1.0, 2.0, 1.0, 2.0, 1.0, 2.0, 0.5]
)
```

### Monitor Position While Moving

```python
# Subscribe to odometry to track position
subscribe_for_duration(
  topic="/odom",
  msg_type="nav_msgs/Odometry",
  duration=5,
  max_messages=10
)
```

---

## Sensor Data Collection

**When to use**: Reading sensor values from the robot.

### LIDAR/LaserScan

```python
# Get a single scan
subscribe_once(
  topic="/scan",
  msg_type="sensor_msgs/LaserScan",
  timeout=5.0
)

# Collect scans over time
subscribe_for_duration(
  topic="/scan",
  msg_type="sensor_msgs/LaserScan",
  duration=10,
  throttle_rate_ms=500  # One scan per 500ms
)
```

### IMU Data

```python
# Get current IMU reading
subscribe_once(
  topic="/imu/data",
  msg_type="sensor_msgs/Imu"
)

# Monitor IMU for 5 seconds
subscribe_for_duration(
  topic="/imu/data",
  msg_type="sensor_msgs/Imu",
  duration=5,
  max_messages=100
)
```

### Joint States

```python
# Get current joint positions
subscribe_once(
  topic="/joint_states",
  msg_type="sensor_msgs/JointState"
)
```

### Battery State

```python
subscribe_once(
  topic="/battery_state",
  msg_type="sensor_msgs/BatteryState"
)
```

### Transform Data

```python
# Get TF transforms
subscribe_once(
  topic="/tf",
  msg_type="tf2_msgs/TFMessage"
)

# Static transforms
subscribe_once(
  topic="/tf_static",
  msg_type="tf2_msgs/TFMessage"
)
```

---

## Camera/Vision Workflow

**When to use**: Getting and analyzing camera images.

### Step 1: Find Camera Topics

```python
get_topics()
# Look for topics like:
# /camera/image_raw
# /camera/rgb/image_raw
# /camera/depth/image_raw
# /camera/color/image_raw
```

### Step 2: Capture Image

```python
# Capture a single frame
subscribe_once(
  topic="/camera/image_raw",
  msg_type="sensor_msgs/Image",
  timeout=10.0,
  expects_image="true"  # Hint for faster processing
)
```

### Step 3: Analyze the Image

```python
# Analyze the captured image
analyze_previously_received_image(
  image_path="./camera/received_image.jpeg"
)
```

### Compressed Images

```python
# For compressed image topics
subscribe_once(
  topic="/camera/image_raw/compressed",
  msg_type="sensor_msgs/CompressedImage",
  expects_image="true"
)
```

### Depth Images

```python
# Depth cameras
subscribe_once(
  topic="/camera/depth/image_raw",
  msg_type="sensor_msgs/Image",
  timeout=10.0
)
```

---

## Navigation (Nav2)

**When to use**: Autonomous navigation with ROS 2 Nav2 stack.

### Check Nav2 is Running

```python
# List actions - should see navigation actions
get_actions()
# Look for: /navigate_to_pose, /navigate_through_poses, /follow_path

# List topics - should see costmap and plan topics
get_topics()
# Look for: /map, /global_costmap, /local_costmap, /plan
```

### Send Navigation Goal

```python
# Navigate to a specific pose
send_action_goal(
  action_name="/navigate_to_pose",
  action_type="nav2_msgs/action/NavigateToPose",
  goal={
    "pose": {
      "header": {
        "frame_id": "map"
      },
      "pose": {
        "position": {"x": 2.0, "y": 1.0, "z": 0.0},
        "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
      }
    }
  },
  timeout=120.0
)
```

### Monitor Navigation Status

```python
# Check action status
get_action_status(action_name="/navigate_to_pose")
```

### Cancel Navigation

```python
# Cancel current navigation goal
cancel_action_goal(
  action_name="/navigate_to_pose",
  goal_id="<goal_id_from_send_action_goal>"
)
```

### Navigate Through Multiple Poses

```python
send_action_goal(
  action_name="/navigate_through_poses",
  action_type="nav2_msgs/action/NavigateThroughPoses",
  goal={
    "poses": [
      {
        "header": {"frame_id": "map"},
        "pose": {
          "position": {"x": 1.0, "y": 0.0, "z": 0.0},
          "orientation": {"w": 1.0}
        }
      },
      {
        "header": {"frame_id": "map"},
        "pose": {
          "position": {"x": 2.0, "y": 1.0, "z": 0.0},
          "orientation": {"w": 1.0}
        }
      },
      {
        "header": {"frame_id": "map"},
        "pose": {
          "position": {"x": 0.0, "y": 0.0, "z": 0.0},
          "orientation": {"w": 1.0}
        }
      }
    ]
  },
  timeout=300.0
)
```

---

## Parameter Configuration

**When to use**: Adjusting robot behavior via ROS 2 parameters.

### Discover Parameters

```python
# List all parameters for a node
get_parameters(node_name="/turtlesim")

# Get details about a specific parameter
get_parameter_details(name="/turtlesim:background_r")
```

### Modify Parameters

```python
# Change turtlesim background to red
set_parameter(name="/turtlesim:background_r", value="255")
set_parameter(name="/turtlesim:background_g", value="0")
set_parameter(name="/turtlesim:background_b", value="0")

# Note: Some changes require service call to take effect
call_service(
  service_name="/clear",
  service_type="std_srvs/Empty",
  request={}
)
```

### Save/Check Parameters

```python
# Check if parameter exists
has_parameter(name="/my_node:my_param")

# Delete temporary parameter
delete_parameter(name="/my_node:temp_config")
```

---

## Turtlesim Complete Demo

**When to use**: Testing your setup or learning ROS-MCP.

### Setup

```bash
# Terminal 1: Start turtlesim (ensure ROS 2 is sourced first)
ros2 run turtlesim turtlesim_node

# Terminal 2: Start rosbridge
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

> If `ros2` is not found, run: `source /opt/ros/$ROS_DISTRO/setup.bash`

### Complete Workflow

```python
# 1. Connect
connect_to_robot()

# 2. Discover the system
get_topics()
get_services()
get_nodes()

# 3. Get turtle's current position
subscribe_once(topic="/turtle1/pose", msg_type="turtlesim/Pose")

# 4. Move the turtle
publish_once(
  topic="/turtle1/cmd_vel",
  msg_type="geometry_msgs/Twist",
  msg={"linear": {"x": 2.0}}
)

# 5. Change pen color to red
call_service(
  service_name="/turtle1/set_pen",
  service_type="turtlesim/SetPen",
  request={"r": 255, "g": 0, "b": 0, "width": 3, "off": 0}
)

# 6. Draw a pattern
publish_for_durations(
  topic="/turtle1/cmd_vel",
  msg_type="geometry_msgs/Twist",
  messages=[
    {"linear": {"x": 2.0}},
    {"angular": {"z": 1.57}},
    {"linear": {"x": 2.0}},
    {"angular": {"z": 1.57}},
    {"linear": {"x": 2.0}},
    {"angular": {"z": 1.57}},
    {"linear": {"x": 2.0}},
    {}
  ],
  durations=[1.0, 0.5, 1.0, 0.5, 1.0, 0.5, 1.0, 0.1]
)

# 7. Spawn a second turtle
call_service(
  service_name="/spawn",
  service_type="turtlesim/Spawn",
  request={"x": 2.0, "y": 2.0, "theta": 0.0, "name": "turtle2"}
)

# 8. Control second turtle
publish_once(
  topic="/turtle2/cmd_vel",
  msg_type="geometry_msgs/Twist",
  msg={"linear": {"x": 1.0}, "angular": {"z": 0.5}}
)

# 9. Change background color (ROS 2)
set_parameter(name="/turtlesim:background_r", value="50")
set_parameter(name="/turtlesim:background_g", value="50")
set_parameter(name="/turtlesim:background_b", value="100")
call_service(service_name="/clear", service_type="std_srvs/Empty", request={})

# 10. Use rotate_absolute action (ROS 2)
send_action_goal(
  action_name="/turtle1/rotate_absolute",
  action_type="turtlesim/action/RotateAbsolute",
  goal={"theta": 0.0}
)

# 11. Reset everything
call_service(
  service_name="/reset",
  service_type="std_srvs/Empty",
  request={}
)
```

---

## Multi-Robot Setup

**When to use**: Controlling multiple robots or namespaced robots.

### Understanding Namespaces

Robots often use namespaces to avoid topic collisions:
- Robot 1: `/robot1/cmd_vel`, `/robot1/odom`
- Robot 2: `/robot2/cmd_vel`, `/robot2/odom`

### Control Multiple Robots

```python
# Connect to the rosbridge that sees all robots
connect_to_robot(ip="192.168.1.1", port=9090)

# List all topics to see namespaces
get_topics()

# Control robot 1
publish_once(
  topic="/robot1/cmd_vel",
  msg_type="geometry_msgs/Twist",
  msg={"linear": {"x": 0.5}}
)

# Control robot 2
publish_once(
  topic="/robot2/cmd_vel",
  msg_type="geometry_msgs/Twist",
  msg={"linear": {"x": 0.3}}
)

# Monitor both robots
subscribe_once(topic="/robot1/odom", msg_type="nav_msgs/Odometry")
subscribe_once(topic="/robot2/odom", msg_type="nav_msgs/Odometry")
```

### Multiple rosbridge Connections

If robots have separate rosbridge servers:

```python
# Connect to robot 1
connect_to_robot(ip="192.168.1.100", port=9090)
# ... control robot 1 ...

# Reconnect to robot 2
connect_to_robot(ip="192.168.1.101", port=9090)
# ... control robot 2 ...
```

---

## Workflow Templates

### Safety Check Before Motion

```python
# 1. Verify connection
ping_robot(ip="192.168.1.100", port=9090)
connect_to_robot(ip="192.168.1.100", port=9090)

# 2. Check emergency stop status (robot-specific)
subscribe_once(topic="/emergency_stop", msg_type="std_msgs/Bool")

# 3. Check battery level
subscribe_once(topic="/battery_state", msg_type="sensor_msgs/BatteryState")

# 4. Verify sensors are working
subscribe_once(topic="/scan", msg_type="sensor_msgs/LaserScan", timeout=5.0)

# 5. Only then send motion commands
publish_once(
  topic="/cmd_vel",
  msg_type="geometry_msgs/Twist",
  msg={"linear": {"x": 0.2}}  # Start slow
)
```

### Continuous Monitoring

```python
# Monitor robot state while operating
subscribe_for_duration(
  topic="/diagnostics",
  msg_type="diagnostic_msgs/DiagnosticArray",
  duration=60,
  throttle_rate_ms=1000
)
```
