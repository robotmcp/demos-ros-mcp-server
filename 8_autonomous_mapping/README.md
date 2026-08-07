# Autonomous SLAM Mapping

Autonomous frontier-based exploration and SLAM mapping for ROS 2 Humble + Ignition Gazebo (Fortress). Supports **TurtleBot3 Burger** and **TugBot** robots out of the box.

The robot autonomously explores an unknown environment by detecting frontiers (boundaries between explored and unexplored space) in the occupancy grid, driving toward the largest/closest frontier, and repeating until the entire map is built.

---

## Quick Start

### TurtleBot3 Burger

```bash
# Prerequisites: TurtleBot3 Ignition workspace built at ../4_turtlebot_ignition/
cd 8_autonomous_mapping
./run.sh
```

### TugBot

```bash
cd 8_autonomous_mapping
./run_tugbot.sh
```

Both launch Ignition Gazebo, SLAM Toolbox, Nav2, RViz, and the frontier explorer in a single command.

---

## Prerequisites

```bash
# ROS 2 Humble
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup \
                 ros-humble-slam-toolbox ros-humble-ros-gz
```

**TurtleBot3 only:** The TurtleBot3 Ignition workspace must be built at `../4_turtlebot_ignition/`. The TugBot model is downloaded automatically from [Ignition Fuel](https://fuel.ignitionrobotics.org/1.0/MovAi/models/Tugbot).

---

## Usage

### run.sh (TurtleBot3)

```bash
./run.sh                                    # Full autonomous mapping (default world)
./run.sh --no-rviz                          # Without RViz
./run.sh --no-explore                       # Manual driving only (teleop)
./run.sh --world /path/to/world.sdf         # Different environment
./run.sh --duration 300                     # 5 min timeout (0=unlimited)
./run.sh --speed 0.15                       # Slower exploration
./run.sh --spawn -1.0 2.0                   # Custom spawn position (x y)
```

### run_tugbot.sh (TugBot)

```bash
./run_tugbot.sh                             # Full autonomous mapping
./run_tugbot.sh --no-rviz                   # Without RViz
./run_tugbot.sh --no-explore                # Manual driving only
./run_tugbot.sh --world /path/to/world.sdf  # Different world (must include TugBot model)
./run_tugbot.sh --duration 300              # 5 min timeout
./run_tugbot.sh --speed 0.15               # Slower exploration
```

### Using launch files directly

```bash
source /opt/ros/humble/setup.bash
source ../4_turtlebot_ignition/install/setup.bash  # TurtleBot3 only

# TurtleBot3
ros2 launch launch/autonomous_mapping.launch.py world:=worlds/simple_room.sdf x_pose:=-1.5 y_pose:=1.5

# TugBot
ros2 launch launch/tugbot_mapping.launch.py
```

### Save the map

Once exploration completes (or anytime during mapping):

```bash
ros2 run nav2_map_server map_saver_cli -f my_map --ros-args -p use_sim_time:=true
```

This saves `my_map.pgm` (image) and `my_map.yaml` (metadata).

---

## Algorithm Overview

### Frontier-Based Exploration

The core algorithm in `scripts/frontier_explorer.py` implements autonomous exploration using **frontier detection** on the SLAM occupancy grid:

```
                    ┌──────────────────┐
                    │  SEEK_FRONTIER   │◄─── no frontiers for 30s ──► COMPLETE
                    │                  │
                    │ 1. Get /map from │
                    │    SLAM Toolbox  │
                    │ 2. Find frontier │
                    │    cells         │
                    │ 3. Cluster them  │
                    │ 4. Pick best     │
                    └────────┬─────────┘
                             │ target found
                             ▼
                    ┌──────────────────┐
               ┌───►│    DRIVE_TO      │
               │    │                  │
               │    │ Heading control  │──── reached (< 0.8m) ──► SEEK_FRONTIER
               │    │ + LiDAR obstacle │
               │    │   avoidance      │
               │    └──────┬───────────┘
               │           │ obstacle < 0.4m
               │           ▼
               │    ┌──────────────────┐
               │    │    TURNING /     │
               └────│    REVERSING     │──── stuck 3s ──► blacklist target
                    │                  │                   + SEEK_FRONTIER
                    └──────────────────┘
```

#### Step-by-step:

1. **Frontier Detection**: A frontier cell is a FREE cell (value=0) adjacent to an UNKNOWN cell (value=-1) in the occupancy grid. Wall-adjacent frontiers are filtered out using dilation.

2. **Clustering**: Adjacent frontier cells are grouped using BFS connected components. Clusters smaller than `min_frontier_size` are discarded.

3. **Target Selection**: Clusters are sorted by size (largest first), then distance (closest first). The target point is the cluster cell furthest from the robot (deepest into unknown space). Previously visited and blacklisted targets are skipped.

4. **Driving**: A proportional heading controller steers toward the target. LiDAR sectors (front, front-left, front-right, left, right) provide obstacle avoidance that overrides the heading controller.

5. **Stuck Recovery**: If the front sector is blocked for 3+ seconds, the target is blacklisted and the robot reverses then turns toward the clearer side.

6. **Re-evaluation**: Every ~5 seconds, the current target is re-evaluated. If a significantly closer frontier appears (< 50% of current distance), the robot switches targets.

7. **Completion**: If no frontiers are found for 300 consecutive ticks (~30 seconds of spinning), the exploration is declared complete.

---

## Hyperparameters

### Frontier Explorer (`scripts/frontier_explorer.py`)

#### Navigation Constants (hardcoded)

| Parameter | Value | Description |
|---|---|---|
| `OBSTACLE_STOP` | 0.4 m | Stop and turn when obstacle is this close |
| `OBSTACLE_SLOW` | 1.0 m | Begin slowing down at this distance |
| `TURN_SPEED` | 0.5 rad/s | Rotation speed during turns (kept slow for SLAM quality) |
| `FRONTIER_REACHED` | 0.8 m | Distance threshold to consider a frontier reached |
| `HEADING_TOLERANCE` | 0.2 rad | Angular error tolerance before correcting heading |

#### Command-Line Arguments

| Argument | Default | Description |
|---|---|---|
| `--speed` | 0.18 m/s | Forward driving speed |
| `--duration` | 0 | Exploration timeout in seconds (0 = unlimited) |
| `--min-frontier-size` | 0.3 m | Minimum frontier cluster size to consider |

#### Internal Thresholds

| Parameter | Value | Description |
|---|---|---|
| Wall dilation radius | 0.15 m | Buffer around walls when filtering frontiers |
| Visited filter distance | 1.0 m | Skip frontiers within this distance of visited targets |
| Blacklist proximity | 0.5 m | Skip frontiers near blacklisted locations |
| Blacklist max size | 30 | Oldest entries are dropped when full |
| No-frontier timeout | 300 ticks (30s) | Ticks with no frontiers before declaring complete |
| Stuck timeout | 30 ticks (3s) | Ticks blocked before blacklisting target |
| Re-evaluation interval | ~5 s | How often to check for closer frontiers |
| Control loop rate | 10 Hz | Main control loop frequency |

### SLAM Toolbox

| Parameter | TurtleBot3 | TugBot | Description |
|---|---|---|---|
| `base_frame` | `base_footprint` | `base_link` | Robot base TF frame |
| `max_laser_range` | 3.5 m | 8.0 m | Maximum usable LiDAR range |
| `resolution` | 0.05 m | 0.05 m | Map cell size |
| `minimum_travel_distance` | 0.15 m | 0.15 m | Min distance before new scan is processed |
| `minimum_travel_heading` | 0.15 rad | 0.15 rad | Min rotation before new scan is processed |
| `map_update_interval` | 2.0 s | 2.0 s | How often the map is republished |
| `scan_buffer_size` | 15 | 15 | Number of scans kept for matching |
| `do_loop_closing` | true | true | Enable loop closure detection |
| `correlation_search_space_dimension` | 0.3 m | 0.3 m | Search window for scan matching |
| `correlation_search_space_resolution` | 0.008 m | 0.008 m | Search resolution (smaller = more precise) |

### Nav2 Navigation Stack

| Parameter | TurtleBot3 | TugBot | Description |
|---|---|---|---|
| `robot_radius` | 0.105 m | 0.35 m | Robot footprint radius |
| `max_vel_x` | 0.22 m/s | 0.26 m/s | Maximum forward velocity |
| `max_vel_theta` | 1.82 rad/s | 0.8 rad/s | Maximum rotation velocity |
| `inflation_radius` | 0.3 m | 0.55 m | Costmap inflation around obstacles |
| `robot_base_frame` | `base_footprint` | `base_link` | Base frame for costmaps |

---

## Startup Sequence

All components are launched with staggered delays to ensure dependencies are ready:

| Time | Component | Purpose |
|---|---|---|
| 0 s | Ignition Gazebo | Physics simulation + robot |
| 0 s | ros_gz_bridge | Bridge Ignition topics to ROS 2 |
| 0 s | Static TF publisher | Link LiDAR frame to robot base |
| 0 s | Robot state publisher | URDF → TF (TurtleBot3 only) |
| +5 s | SLAM Toolbox | Online async SLAM (builds the map) |
| +10 s | Nav2 stack | Path planning + costmaps |
| +12 s | RViz2 | Visualization |
| +15 s | Frontier Explorer | Autonomous exploration |

---

## Project Structure

```
8_autonomous_mapping/
├── config/
│   ├── nav2_params.yaml          # Nav2 config for TurtleBot3 Burger
│   ├── tugbot_nav2_params.yaml   # Nav2 config for TugBot
│   ├── slam_params.yaml          # SLAM Toolbox config for TurtleBot3
│   ├── tugbot_slam_params.yaml   # SLAM Toolbox config for TugBot
│   └── slam_nav2.rviz            # RViz layout (shared)
├── launch/
│   ├── autonomous_mapping.launch.py   # TurtleBot3 launch file
│   └── tugbot_mapping.launch.py       # TugBot launch file
├── scripts/
│   └── frontier_explorer.py      # Frontier exploration algorithm (shared)
├── worlds/
│   ├── mapping_world.sdf         # 10×10m, 4 rooms with corridors
│   ├── simple_room.sdf           # 6×6m, 4 walls + center box (TurtleBot3)
│   └── simple_room_tugbot.sdf    # 6×6m, 4 walls + center box (TugBot)
├── run.sh                        # One-command launcher (TurtleBot3)
├── run_tugbot.sh                 # One-command launcher (TugBot)
└── README.md
```

---

## Swapping Environments

### TurtleBot3

Create a new SDF world file and pass it:

```bash
./run.sh --world /path/to/my_world.sdf --spawn 0.0 0.0
```

The world must include the standard Ignition plugins (Physics, Sensors, SceneBroadcaster, UserCommands). The robot is spawned separately by the launch file.

### TugBot

The TugBot model must be **included in the world SDF** (loaded from Ignition Fuel):

```xml
<include>
  <uri>https://fuel.ignitionrobotics.org/1.0/MovAi/models/Tugbot</uri>
  <name>tugbot</name>
  <pose>0 0 0.132279 0 0 0</pose>
</include>
```

The world name **must be `world_demo`** (required by the Ignition scan topic path).

```bash
./run_tugbot.sh --world /path/to/my_tugbot_world.sdf
```

---

## Tuning Tips

- **Map quality is bad (ghost walls, duplicated rooms):** Reduce `--speed`. The default 0.18 m/s is tuned for good SLAM quality. Going above 0.22 m/s causes scan misalignment.
- **Robot gets stuck in narrow passages:** The wall dilation radius (0.15m) filters frontiers near walls. For very tight spaces, reduce it in `frontier_explorer.py` (`dilate_r` calculation).
- **Robot keeps revisiting the same area:** Increase the visited filter distance (currently 1.0m) in `find_best_frontier()`.
- **Exploration takes too long:** Increase `--speed` (up to 0.22 m/s is safe) or reduce `--min-frontier-size` to explore smaller gaps.
- **Robot won't enter corridors:** Check that corridor width > 2× wall dilation radius (currently 2 × 0.15m = 0.30m). Also check Nav2's `inflation_radius` in the costmap config.
