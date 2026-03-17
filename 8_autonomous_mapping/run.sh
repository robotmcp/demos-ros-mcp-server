#!/bin/bash
# ============================================================================
# Autonomous SLAM Mapping - One-command launcher
# ============================================================================
# Starts: Ignition Gazebo + TurtleBot3 + SLAM + Nav2 + Frontier Explorer + RViz
#
# Usage:
#   ./run.sh                                    # Full autonomous mapping
#   ./run.sh --no-rviz                          # Without RViz
#   ./run.sh --no-explore                       # Manual driving only
#   ./run.sh --world /path/to/world.sdf         # Different environment
#   ./run.sh --duration 300                     # 5 min timeout (0=unlimited)
#   ./run.sh --speed 0.15                       # Slower exploration
#   ./run.sh --spawn -1.0 2.0                   # Custom spawn position (x y)
#
# Save the map when done:
#   ros2 run nav2_map_server map_saver_cli -f my_map --ros-args -p use_sim_time:=true
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCH_FILE="$SCRIPT_DIR/launch/autonomous_mapping.launch.py"
TB3_WS="$SCRIPT_DIR/../4_turtlebot_ignition"

# Source ROS 2
source /opt/ros/humble/setup.bash

# Source TurtleBot3 workspace
if [ -f "$TB3_WS/install/setup.bash" ]; then
    source "$TB3_WS/install/setup.bash"
else
    echo "Warning: TurtleBot3 workspace not found at $TB3_WS/install/setup.bash"
    echo "Trying system packages..."
fi

export TURTLEBOT3_MODEL=burger

# Defaults
RVIZ="true"
EXPLORE="true"
WORLD=""
DURATION="600"
SPEED="0.18"
X_POSE=""
Y_POSE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-rviz)      RVIZ="false"; shift ;;
        --no-explore)   EXPLORE="false"; shift ;;
        --world)        WORLD="$2"; shift 2 ;;
        --duration)     DURATION="$2"; shift 2 ;;
        --speed)        SPEED="$2"; shift 2 ;;
        --spawn)        X_POSE="$2"; Y_POSE="$3"; shift 3 ;;
        -h|--help)
            echo "Usage: ./run.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-rviz              Disable RViz visualization"
            echo "  --no-explore           Disable autonomous exploration"
            echo "  --world PATH           Path to Ignition SDF world file"
            echo "  --duration SECS        Exploration timeout (0=unlimited, default: 600)"
            echo "  --speed M/S            Explorer speed (default: 0.18)"
            echo "  --spawn X Y            Robot spawn position (default: -2.5 2.5)"
            echo "  -h, --help             Show this help"
            exit 0
            ;;
        *)              echo "Unknown arg: $1. Use --help for usage."; exit 1 ;;
    esac
done

# Build world display name
if [ -n "$WORLD" ]; then
    WORLD_NAME="$(basename "$WORLD")"
else
    WORLD_NAME="mapping_world.sdf (default)"
fi

echo "============================================"
echo "  Autonomous SLAM Mapping"
echo "============================================"
echo "  Robot:     TurtleBot3 Burger"
echo "  World:     $WORLD_NAME"
echo "  SLAM:      slam_toolbox (async)"
echo "  Nav2:      enabled"
echo "  Explorer:  $EXPLORE (speed=${SPEED} m/s)"
echo "  Timeout:   ${DURATION}s (0=unlimited)"
echo "  RViz:      $RVIZ"
echo "============================================"
echo ""
echo "Startup sequence:"
echo "  0s  - Ignition Gazebo + Robot + Bridge + TF"
echo "  5s  - SLAM Toolbox"
echo "  10s - Nav2 Navigation Stack"
echo "  12s - RViz2"
echo "  15s - Frontier Explorer"
echo ""
echo "Press Ctrl+C to stop all nodes."
echo "============================================"
echo ""

# Build launch command
CMD="ros2 launch $LAUNCH_FILE rviz:=$RVIZ explore:=$EXPLORE speed:=$SPEED duration:=$DURATION"
[ -n "$WORLD" ]  && CMD="$CMD world:=$WORLD"
[ -n "$X_POSE" ] && CMD="$CMD x_pose:=$X_POSE"
[ -n "$Y_POSE" ] && CMD="$CMD y_pose:=$Y_POSE"

exec $CMD
