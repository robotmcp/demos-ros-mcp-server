# Go2 Robot Gazebo Simulation

Complete ROS2 package for simulating the Go2 quadruped robot in Ignition Gazebo (latest version).

## Package Contents

```
go2_description/
├── urdf/
│   └── go2.urdf                 # Robot URDF description
├── worlds/
│   ├── simple_flat.sdf          # Flat terrain for basic testing
│   └── obstacle_world.sdf       # Obstacle course for navigation testing
├── launch/
│   └── gazebo.launch.py         # Main launch file for Ignition Gazebo
├── config/
│   └── go2_controllers.yaml     # ROS2 Control configuration
├── meshes/                      # (Add your .dae mesh files here)
├── CMakeLists.txt
└── package.xml
```

## Prerequisites

### System Requirements
- Ubuntu 20.04 LTS or 22.04 LTS
- ROS2 Humble or Jazzy
- Ignition Gazebo (latest: Garden or Fortress)

### Installation Steps

1. **Install ROS2** (if not already installed):
```bash
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
sudo apt update
sudo apt install ros-humble-desktop
source /opt/ros/humble/setup.bash
```

2. **Install Ignition Gazebo and related packages**:
```bash
sudo apt install ros-humble-ignition-gazebo* \
  ros-humble-ros-gz-sim \
  ros-humble-ros-gz-bridge \
  ros-humble-robot-state-publisher \
  ros-humble-joint-state-publisher-gui \
  ros-humble-diff-drive-controller \
  ros-humble-position-controllers \
  ros-humble-rqt-joint-trajectory-controller
```

3. **Create ROS2 workspace**:
```bash
mkdir -p ~/go2_ws/src
cd ~/go2_ws
```

4. **Clone or copy the go2_description package**:
```bash
cd ~/go2_ws/src
# Copy the go2_description folder here
```

5. **Build the package**:
```bash
cd ~/go2_ws
colcon build --symlink-install
source install/setup.bash
```

## Usage

### 1. Simple Flat World (Recommended for First Test)

```bash
source ~/go2_ws/install/setup.bash
ros2 launch go2_description gazebo.launch.py world:=simple_flat.sdf
```

### 2. Obstacle Course World

```bash
ros2 launch go2_description gazebo.launch.py world:=obstacle_world.sdf
```

### 3. Custom World

To use a custom SDF world file:
```bash
ros2 launch go2_description gazebo.launch.py world:=/path/to/custom_world.sdf
```

## Controlling the Robot

### Using RViz for Visualization

In a new terminal:
```bash
source ~/go2_ws/install/setup.bash
ros2 run rviz2 rviz2 -d $(ros2 pkg prefix go2_description)/share/go2_description/rviz/go2.rviz
```

### Publishing Joint Commands

Example: Move the front-left hip joint
```bash
ros2 topic pub /FL_hip_joint_controller/command std_msgs/Float64 "{data: 0.5}"
```

### Using Joint Trajectory Controller

```python
import rclpy
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from datetime import datetime

rclpy.init()
node = rclpy.create_node('go2_controller')
publisher = node.create_publisher(JointTrajectory, '/joint_trajectory_controller/joint_trajectory', 10)

trajectory = JointTrajectory()
trajectory.header.stamp = node.get_clock().now().to_msg()
trajectory.joint_names = [
    'FL_hip_joint', 'FL_thigh_joint', 'FL_calf_joint',
    'FR_hip_joint', 'FR_thigh_joint', 'FR_calf_joint',
    'RL_hip_joint', 'RL_thigh_joint', 'RL_calf_joint',
    'RR_hip_joint', 'RR_thigh_joint', 'RR_calf_joint'
]

point = JointTrajectoryPoint()
point.positions = [0.0] * 12
point.velocities = [0.0] * 12
point.time_from_start.sec = 1

trajectory.points.append(point)
publisher.publish(trajectory)
```

## Available Test Environments

### 1. Simple Flat World
- **Use Case**: Basic locomotion testing, gait development
- **Terrain**: Flat ground
- **Features**: Simple, fast simulation
- **File**: `worlds/simple_flat.sdf`

### 2. Obstacle Course
- **Use Case**: Navigation, obstacle avoidance, path planning
- **Terrain**: Flat with boxes and cylinders
- **Features**: Multiple obstacles at various heights
- **File**: `worlds/obstacle_world.sdf`

### 3. Custom Worlds
You can create your own SDF worlds by:
1. Creating a new `.sdf` file in `worlds/` directory
2. Following the SDF 1.9 format
3. Including necessary Gazebo plugins
4. Launching with: `ros2 launch go2_description gazebo.launch.py world:=your_world.sdf`

## Robot Specifications

### Physical Dimensions
- Length: 0.3762 m
- Width: 0.0935 m
- Height: 0.114 m (base)
- Total Height with legs extended: ~0.5 m

### Mass Distribution
- Base: 6.921 kg
- Each hip: 0.678 kg
- Each thigh: 1.152 kg
- Each calf: 0.154 kg
- Each foot: 0.04 kg

### Joint Limits
- Hip joints: ±60° (±1.0472 rad)
- Thigh joints: Front legs -90° to +200°, Rear legs -30° to +260°
- Calf joints: -156° to -48°

## URDF Structure

The Go2 URDF includes:
- **Base Link**: Main body with inertial properties
- **Head Assembly**: Two fixed links for sensor mounting
- **Four Legs**: Each with 3 revolute joints (hip, thigh, calf) and 1 fixed foot
- **Sensors**: IMU and Radar links (fixed to base)
- **Gazebo Plugins**: Surface friction configuration for realistic foot contact

## Troubleshooting

### Issue: "Model not found" or mesh file errors
**Solution**: Ensure mesh files (.dae) are in `meshes/` directory and paths in URDF are correct.

### Issue: Robot falls through ground
**Solution**: Check world SDF has proper friction coefficients (mu, mu2 ≥ 1.0)

### Issue: Gazebo doesn't load
**Solution**: 
```bash
# Check Ignition Gazebo installation
which ign
ign gazebo --version

# Reinstall if needed
sudo apt reinstall ros-humble-ignition-gazebo*
```

### Issue: No robot appears in Gazebo
**Solution**: Check the spawn command is being executed and URDF paths are correct

### Issue: Joint commands not working
**Solution**: 
1. Verify controller is loaded: `ros2 control list_controllers`
2. Check joint names in command match URDF
3. Ensure controller plugin is properly configured

## Monitoring and Debugging

### Check Active Controllers
```bash
ros2 control list_controllers
ros2 control list_hardware_interfaces
```

### Monitor Joint States
```bash
ros2 topic echo /joint_states
```

### Record Rosbag Data
```bash
ros2 bag record /joint_states /tf /cmd_vel
```

### View TF Tree
```bash
ros2 run tf2_tools view_frames
```

## Advanced Configuration

### Modify Physics Parameters
Edit the world SDF file to change:
- `max_step_size`: Simulation time step (default: 0.001s)
- `real_time_factor`: Simulation speed relative to real time
- Friction coefficients for ground and feet

### Add Sensors
To add sensors (camera, lidar, etc.):
1. Add sensor link to URDF
2. Add Gazebo plugin configuration
3. Add ROS bridge in launch file

### Custom Locomotion Controllers
Implement custom gait patterns by:
1. Creating a ROS2 node that publishes joint trajectories
2. Publishing to `/joint_trajectory_controller/joint_trajectory`
3. Implementing desired gait algorithm (trotting, bounding, etc.)

## Resources

- **ROS2 Documentation**: https://docs.ros.org/
- **Ignition Gazebo Docs**: https://ignitionrobotics.org/
- **URDF Specification**: http://wiki.ros.org/urdf
- **SDF Format**: http://sdformat.org/

## License

BSD 3-Clause License

## Author

Go2 Description Package Contributors

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Ignition Gazebo documentation
3. Check ROS2 Answers: https://answers.ros.org/

---

**Last Updated**: 2024
**Compatible with**: ROS2 Humble, Ignition Gazebo Garden/Fortress
