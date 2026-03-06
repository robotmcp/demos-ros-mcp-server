# ROS-MCP Server Tool Reference

Complete documentation for all available MCP tools with examples.

---

## Table of Contents

1. [Connection Tools](#connection-tools)
2. [Node Tools](#node-tools)
3. [Topic Tools](#topic-tools)
4. [Service Tools](#service-tools)
5. [Action Tools (ROS 2 Only)](#action-tools-ros-2-only)
6. [Parameter Tools (ROS 2 Only)](#parameter-tools-ros-2-only)
7. [Vision Tools](#vision-tools)

---

## Connection Tools

### connect_to_robot

**Purpose**: Connect to a robot by setting the IP/port. Tests connectivity to confirm reachability.

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `ip` | string | `"127.0.0.1"` | Robot's IP address |
| `port` | int/string | `9090` | rosbridge port |
| `ping_timeout` | number | `2` | Timeout for ping test (seconds) |
| `port_timeout` | number | `2` | Timeout for port check (seconds) |

**Examples:**

```python
# Connect to localhost (default)
connect_to_robot()

# Connect to remote robot
connect_to_robot(ip="192.168.1.100", port=9090)

# With longer timeouts for slow networks
connect_to_robot(ip="10.0.0.50", port=9090, ping_timeout=5, port_timeout=5)
```

**Returns**: Connection status with ping result, port status, and WebSocket connection state.

---

### ping_robot

**Purpose**: Test if a robot's IP is reachable and if rosbridge port is open.

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `ip` | string | required | Robot's IP address |
| `port` | int | required | rosbridge port |
| `ping_timeout` | number | `2` | Ping timeout (seconds) |
| `port_timeout` | number | `2` | Port check timeout (seconds) |

**Example:**
```python
ping_robot(ip="192.168.1.100", port=9090)
```

**Returns**: 
- IP reachability status
- Port open status
- Diagnostic info (if ping succeeds but port fails, rosbridge likely not running)

---

### detect_ros_version

**Purpose**: Detect the ROS version and distribution via rosbridge.

**Parameters**: None

**Example:**
```python
detect_ros_version()
```

**Returns**: ROS version and distribution name (e.g., "2", "humble")

---

### get_verified_robots_list

**Purpose**: List pre-verified robot models that have specification files.

**Parameters**: None

**Example:**
```python
get_verified_robots_list()
```

**Returns**: List of robot models with available spec files. If your robot isn't listed, you can still connect directly.

---

### get_verified_robot_spec

**Purpose**: Load specifications and usage context for a verified robot model.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `name` | string | Robot model name from verified list |

**Example:**
```python
get_verified_robot_spec(name="unitree_go2")
```

**Returns**: Robot specifications including topics, services, and usage guidance.

---

## Node Tools

### get_nodes

**Purpose**: List all currently running ROS nodes.

**Parameters**: None

**Example:**
```python
get_nodes()
```

**Returns**: List of active node names (e.g., `/turtlesim`, `/rosbridge_websocket`)

---

### get_node_details

**Purpose**: Get detailed information about a specific node.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `node` | string | Node name (e.g., `/turtlesim`) |

**Example:**
```python
get_node_details(node="/turtlesim")
```

**Returns**: 
- Publishers (topics this node publishes to)
- Subscribers (topics this node subscribes to)
- Services (services this node provides)

---

## Topic Tools

### get_topics

**Purpose**: List all available ROS topics.

**Parameters**: None

**Example:**
```python
get_topics()
```

**Returns**: List of all topic names in the ROS system.

**Sample Output:**
```
["/rosout", "/turtle1/cmd_vel", "/turtle1/pose", "/parameter_events"]
```

---

### get_topic_type

**Purpose**: Get the message type for a specific topic.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `topic` | string | Topic name |

**Example:**
```python
get_topic_type(topic="/cmd_vel")
```

**Returns**: Message type string (e.g., `geometry_msgs/Twist` or `geometry_msgs/msg/Twist`)

---

### get_topic_details

**Purpose**: Get detailed information about a topic.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `topic` | string | Topic name |

**Example:**
```python
get_topic_details(topic="/turtle1/cmd_vel")
```

**Returns**:
- Message type
- List of publishers
- List of subscribers

---

### get_message_details

**Purpose**: Get the complete structure/definition of a message type.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `message_type` | string | Message type (e.g., `geometry_msgs/Twist`) |

**Example:**
```python
get_message_details(message_type="geometry_msgs/Twist")
```

**Returns**: Full message definition including all fields and nested types.

**Sample Output:**
```
geometry_msgs/Twist:
  geometry_msgs/Vector3 linear
    float64 x
    float64 y
    float64 z
  geometry_msgs/Vector3 angular
    float64 x
    float64 y
    float64 z
```

---

### subscribe_once

**Purpose**: Subscribe to a topic and return the first message received.

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `topic` | string | required | Topic name |
| `msg_type` | string | `""` | Message type (auto-detected if empty) |
| `timeout` | number | `null` | Timeout in seconds |
| `queue_length` | int | `null` | Message buffer size |
| `throttle_rate_ms` | int | `null` | Rate limiting in milliseconds |
| `expects_image` | string | `"auto"` | `"true"`, `"false"`, or `"auto"` |

**Examples:**

```python
# Basic subscription
subscribe_once(topic="/turtle1/pose", msg_type="turtlesim/Pose")

# With timeout for slow topics
subscribe_once(
  topic="/camera/image_raw",
  msg_type="sensor_msgs/Image",
  timeout=10.0
)

# High-rate topic with throttling
subscribe_once(
  topic="/imu/data",
  msg_type="sensor_msgs/Imu",
  throttle_rate_ms=100
)

# Image topic with hint
subscribe_once(
  topic="/camera/image_raw",
  msg_type="sensor_msgs/Image",
  expects_image="true"
)
```

**Returns**: The first message received, or timeout error.

---

### subscribe_for_duration

**Purpose**: Subscribe to a topic for a specified duration and collect messages.

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `topic` | string | required | Topic name |
| `msg_type` | string | `""` | Message type |
| `duration` | number | `5` | Collection duration (seconds) |
| `max_messages` | int | `100` | Maximum messages to collect |
| `queue_length` | int | `null` | Message buffer size |
| `throttle_rate_ms` | int | `null` | Rate limiting |
| `expects_image` | string | `"auto"` | Image hint |

**Example:**
```python
# Collect odometry for 5 seconds
subscribe_for_duration(
  topic="/odom",
  msg_type="nav_msgs/Odometry",
  duration=5,
  max_messages=50
)

# Monitor sensor at controlled rate
subscribe_for_duration(
  topic="/scan",
  msg_type="sensor_msgs/LaserScan",
  duration=10,
  throttle_rate_ms=500
)
```

**Returns**: Array of collected messages with timestamps.

---

### publish_once

**Purpose**: Publish a single message to a ROS topic.

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `topic` | string | required | Topic name |
| `msg_type` | string | required | Message type |
| `msg` | object | `{}` | Message content |

**Examples:**

```python
# Move robot forward
publish_once(
  topic="/cmd_vel",
  msg_type="geometry_msgs/Twist",
  msg={
    "linear": {"x": 0.5, "y": 0.0, "z": 0.0},
    "angular": {"x": 0.0, "y": 0.0, "z": 0.0}
  }
)

# Shorter form (unspecified fields default to 0)
publish_once(
  topic="/cmd_vel",
  msg_type="geometry_msgs/Twist",
  msg={"linear": {"x": 0.5}}
)

# Rotate robot
publish_once(
  topic="/cmd_vel",
  msg_type="geometry_msgs/Twist",
  msg={"angular": {"z": 1.0}}
)

# Stop robot
publish_once(
  topic="/cmd_vel",
  msg_type="geometry_msgs/Twist",
  msg={}
)

# Publish string message
publish_once(
  topic="/chatter",
  msg_type="std_msgs/String",
  msg={"data": "Hello from MCP!"}
)
```

**Returns**: Confirmation of publish success.

---

### publish_for_durations

**Purpose**: Publish a sequence of messages with specified delays between them.

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `topic` | string | required | Topic name |
| `msg_type` | string | required | Message type |
| `messages` | array | `[]` | Array of message objects |
| `durations` | array | `[]` | Array of durations (seconds) for each message |

**Example:**
```python
# Drive pattern: forward, turn, forward, stop
publish_for_durations(
  topic="/cmd_vel",
  msg_type="geometry_msgs/Twist",
  messages=[
    {"linear": {"x": 1.0}},           # Forward
    {"angular": {"z": 1.57}},         # Turn 90 degrees
    {"linear": {"x": 1.0}},           # Forward
    {"linear": {"x": 0.0}}            # Stop
  ],
  durations=[2.0, 1.0, 2.0, 0.5]      # Duration for each
)
```

**Returns**: Confirmation of sequence completion.

---

## Service Tools

### get_services

**Purpose**: List all available ROS services.

**Parameters**: None

**Example:**
```python
get_services()
```

**Returns**: List of all service names.

---

### get_service_type

**Purpose**: Get the service type for a specific service.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `service` | string | Service name |

**Example:**
```python
get_service_type(service="/spawn")
```

**Returns**: Service type string (e.g., `turtlesim/Spawn`)

---

### get_service_details

**Purpose**: Get complete service details including request/response structures.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `service` | string | Service name |

**Example:**
```python
get_service_details(service="/spawn")
```

**Returns**:
- Service type
- Request fields and types
- Response fields and types
- Provider nodes

---

### call_service

**Purpose**: Call a ROS service with specified request data.

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `service_name` | string | required | Service name |
| `service_type` | string | required | Service type |
| `request` | object | required | Request data |
| `timeout` | number | `null` | Timeout for slow services |

**Examples:**

```python
# Spawn a turtle
call_service(
  service_name="/spawn",
  service_type="turtlesim/Spawn",
  request={
    "x": 5.0,
    "y": 5.0,
    "theta": 0.0,
    "name": "turtle2"
  }
)

# Clear turtlesim canvas
call_service(
  service_name="/clear",
  service_type="std_srvs/Empty",
  request={}
)

# Kill a turtle
call_service(
  service_name="/kill",
  service_type="turtlesim/Kill",
  request={"name": "turtle2"}
)

# Reset turtlesim
call_service(
  service_name="/reset",
  service_type="std_srvs/Empty",
  request={}
)

# Set pen properties (turtlesim)
call_service(
  service_name="/turtle1/set_pen",
  service_type="turtlesim/SetPen",
  request={
    "r": 255,
    "g": 0,
    "b": 0,
    "width": 3,
    "off": 0
  }
)

# With timeout for slow services
call_service(
  service_name="/slow_service",
  service_type="my_package/SlowService",
  request={"data": "value"},
  timeout=30.0
)
```

**Returns**: Service response data.

**Important**: Field names in the request should match what `get_service_details()` returns. Don't add leading underscores.

---

## Action Tools (ROS 2 Only)

### get_actions

**Purpose**: List all available ROS 2 actions.

**Parameters**: None

**Example:**
```python
get_actions()
```

**Returns**: List of action names.

---

### get_action_details

**Purpose**: Get complete action details including goal, result, and feedback structures.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `action` | string | Action name |

**Example:**
```python
get_action_details(action="/turtle1/rotate_absolute")
```

**Returns**:
- Action type
- Goal structure
- Result structure
- Feedback structure

---

### get_action_status

**Purpose**: Get the status of a specific action.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `action_name` | string | Action name |

**Example:**
```python
get_action_status(action_name="/navigate_to_pose")
```

**Returns**: Current action status (idle, executing, succeeded, etc.)

---

### send_action_goal

**Purpose**: Send a goal to a ROS 2 action server.

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `action_name` | string | required | Action name |
| `action_type` | string | required | Action type |
| `goal` | object | required | Goal data |
| `timeout` | number | `null` | Timeout for action completion |

**Examples:**

```python
# Rotate turtle to absolute angle
send_action_goal(
  action_name="/turtle1/rotate_absolute",
  action_type="turtlesim/action/RotateAbsolute",
  goal={"theta": 1.57}
)

# Navigate to pose (Nav2)
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
  timeout=60.0
)

# Fibonacci example
send_action_goal(
  action_name="/fibonacci",
  action_type="example_interfaces/action/Fibonacci",
  goal={"order": 10}
)
```

**Returns**: Goal ID and initial status.

---

### cancel_action_goal

**Purpose**: Cancel a running action goal.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `action_name` | string | Action name |
| `goal_id` | string | Goal ID from send_action_goal |

**Example:**
```python
cancel_action_goal(
  action_name="/navigate_to_pose",
  goal_id="goal_1234567890_abc123"
)
```

**Returns**: Cancellation confirmation.

---

## Parameter Tools (ROS 2 Only)

### get_parameters

**Purpose**: List all parameter names for a specific node.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `node_name` | string | Node name (with or without leading `/`) |

**Example:**
```python
get_parameters(node_name="/turtlesim")
# or
get_parameters(node_name="turtlesim")
```

**Returns**: List of parameter names for the node.

---

### get_parameter

**Purpose**: Get a single parameter value.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `name` | string | Parameter in format `node:param` |

**Example:**
```python
get_parameter(name="/turtlesim:background_r")
```

**Returns**: Parameter value.

---

### get_parameter_details

**Purpose**: Get comprehensive parameter details including value, type, and metadata.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `name` | string | Parameter in format `node:param` |

**Example:**
```python
get_parameter_details(name="/turtlesim:background_r")
```

**Returns**: Value, type, and any additional metadata.

---

### set_parameter

**Purpose**: Set a parameter value.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `name` | string | Parameter in format `node:param` |
| `value` | string | New value (as string) |

**Example:**
```python
# Change turtlesim background color
set_parameter(name="/turtlesim:background_r", value="255")
set_parameter(name="/turtlesim:background_g", value="0")
set_parameter(name="/turtlesim:background_b", value="0")
```

**Returns**: Confirmation of parameter change.

---

### has_parameter

**Purpose**: Check if a parameter exists.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `name` | string | Parameter in format `node:param` |

**Example:**
```python
has_parameter(name="/turtlesim:background_r")
```

**Returns**: Boolean indicating existence.

---

### delete_parameter

**Purpose**: Delete a parameter.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `name` | string | Parameter in format `node:param` |

**Example:**
```python
delete_parameter(name="/my_node:temp_param")
```

**Returns**: Confirmation of deletion.

---

## Vision Tools

### analyze_previously_received_image

**Purpose**: Analyze an image that was saved by any ROS operation (topic subscription, service response, etc.).

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `image_path` | string | `"./camera/received_image.jpeg"` | Path to saved image |

**Example:**
```python
# First, subscribe to camera topic (image is auto-saved)
subscribe_once(
  topic="/camera/image_raw",
  msg_type="sensor_msgs/Image",
  expects_image="true"
)

# Then analyze the saved image
analyze_previously_received_image(image_path="./camera/received_image.jpeg")
```

**Returns**: Analysis of the image content.

---

## Message Type Quick Reference

### geometry_msgs/Twist
```json
{
  "linear": {"x": 0.0, "y": 0.0, "z": 0.0},
  "angular": {"x": 0.0, "y": 0.0, "z": 0.0}
}
```

### geometry_msgs/Pose
```json
{
  "position": {"x": 0.0, "y": 0.0, "z": 0.0},
  "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
}
```

### geometry_msgs/PoseStamped
```json
{
  "header": {
    "stamp": {"sec": 0, "nanosec": 0},
    "frame_id": "map"
  },
  "pose": {
    "position": {"x": 0.0, "y": 0.0, "z": 0.0},
    "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
  }
}
```

### std_msgs/String
```json
{"data": "your string here"}
```

### std_msgs/Bool
```json
{"data": true}
```

### std_msgs/Int32
```json
{"data": 42}
```

### std_msgs/Float64
```json
{"data": 3.14159}
```
