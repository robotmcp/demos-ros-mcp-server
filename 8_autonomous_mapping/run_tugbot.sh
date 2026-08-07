#!/bin/bash
# ============================================================================
# Autonomous SLAM Mapping with TugBot - One-command launcher
# ============================================================================
# Same frontier exploration algorithm as TurtleBot3, but with the TugBot robot.
#
# Usage:
#   ./run_tugbot.sh                          # Full autonomous mapping
#   ./run_tugbot.sh --no-rviz                # Without RViz
#   ./run_tugbot.sh --no-explore             # Manual driving only
#   ./run_tugbot.sh --duration 300           # 5 min timeout (0=unlimited)
#   ./run_tugbot.sh --speed 0.15             # Slower exploration
#   ./run_tugbot.sh --world /path/to/world.sdf  # Different world (must include TugBot)
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCH_FILE="$SCRIPT_DIR/launch/tugbot_mapping.launch.py"

# Source ROS 2
source /opt/ros/humble/setup.bash

# Defaults
RVIZ="true"
EXPLORE="true"
WORLD=""
DURATION="0"
SPEED="0.18"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-rviz)      RVIZ="false"; shift ;;
        --no-explore)   EXPLORE="false"; shift ;;
        --world)        WORLD="$2"; shift 2 ;;
        --duration)     DURATION="$2"; shift 2 ;;
        --speed)        SPEED="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: ./run_tugbot.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-rviz              Disable RViz visualization"
            echo "  --no-explore           Disable autonomous exploration"
            echo "  --world PATH           Path to SDF world file (must include TugBot)"
            echo "  --duration SECS        Exploration timeout (0=unlimited, default: 0)"
            echo "  --speed M/S            Explorer speed (default: 0.18)"
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
    WORLD_NAME="simple_room_tugbot.sdf (default)"
fi

echo "============================================"
echo "  Autonomous SLAM Mapping (TugBot)"
echo "============================================"
echo "  Robot:     TugBot"
echo "  World:     $WORLD_NAME"
echo "  SLAM:      slam_toolbox (async)"
echo "  Nav2:      enabled"
echo "  Explorer:  $EXPLORE (speed=${SPEED} m/s)"
echo "  Timeout:   ${DURATION}s (0=unlimited)"
echo "  RViz:      $RVIZ"
echo "============================================"
echo ""
echo "Startup sequence:"
echo "  0s  - Ignition Gazebo + Bridge + TF"
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
[ -n "$WORLD" ] && CMD="$CMD world:=$WORLD"

exec $CMD
