# Go2 Gazebo Simulation - Complete File Structure & Setup Guide

## 📁 Complete Package Structure

```
go2_complete/
│
├── README.md                                    # Main documentation
├── QUICKSTART.md                               # Quick start guide
├── FILE_STRUCTURE.md                           # This file
│
└── go2_description/                            # ROS2 Package
    ├── package.xml                             # ROS2 package metadata
    ├── CMakeLists.txt                          # Build configuration
    │
    ├── urdf/
    │   └── go2.urdf                            # Robot URDF description (simplified)
    │                                           # Note: Mesh files (.dae) should be placed in meshes/
    │
    ├── worlds/
    │   ├── simple_flat.sdf                     # ✅ Basic flat terrain
    │   ├── obstacle_world.sdf                  # ✅ Obstacle course with boxes/cylinders
    │   └── terrain_world.sdf                   # ✅ Advanced terrain with ramps & stepping stones
    │
    ├── launch/
    │   └── gazebo.launch.py                    # ✅ Main launch file for Ignition Gazebo
    │
    ├── config/
    │   └── go2_controllers.yaml                # ✅ ROS2 controller configuration
    │
    ├── scripts/
    │   └── go2_controller_example.py           # ✅ Example control script
    │
    └── meshes/                                 # ⚠️ Mesh directory (add your .dae files here)
        ├── base.dae
        ├── hip.dae
        ├── thigh.dae
        ├── calf.dae
        ├── foot.dae
        ├── thigh_mirror.dae
        └── calf_mirror.dae
```

## ✅ Files Provided

### Core Files
1. **package.xml** - ROS2 package manifest with dependencies
2. **CMakeLists.txt** - Build configuration for catkin/colcon
3. **go2.urdf** - Complete robot URDF with all joints and links
4. **gazebo.launch.py** - Launch file compatible with Ignition Gazebo

### World Files (3 environments)
1. **simple_flat.sdf** - Flat ground for basic testing
2. **obstacle_world.sdf** - Obstacles for navigation testing
3. **terrain_world.sdf** - Complex terrain with ramps, slopes, stepping stones

### Configuration
1. **go2_controllers.yaml** - Joint controllers for ROS2 control

### Documentation
1. **README.md** - Comprehensive guide with troubleshooting
2. **QUICKSTART.md** - 60-second quick start
3. **go2_controller_example.py** - Example Python control script

## ⚠️ Files You Need to Add

### Mesh Files (Visual Models)
The URDF references mesh files that you need to obtain:

```
meshes/
├── base.dae           # Main body
├── hip.dae            # Hip joint mechanism
├── thigh.dae          # Thigh link
├── calf.dae           # Calf link
├── foot.dae           # Foot link
├── thigh_mirror.dae   # Right-side thigh
└── calf_mirror.dae    # Right-side calf
```

**Options to get mesh files:**
1. Extract from original SolidWorks package if available
2. Use DAE files from Go2 official repository (if public)
3. Create simplified geometry (current URDF uses basic shapes as fallback)
4. Download from https://github.com/unitreerobotics/unitree_ros (if Go2 available)

**Current Implementation:**
The provided URDF uses simple geometric shapes (boxes, cylinders, spheres) instead of mesh files for collision and visuals. This allows the simulation to work immediately without mesh files.

## 🚀 Quick Setup Instructions

### Step 1: Create Workspace
```bash
mkdir -p ~/go2_ws/src
cd ~/go2_ws/src
```

### Step 2: Place Package
Copy the `go2_description` folder to `~/go2_ws/src/`

### Step 3: Install Dependencies
```bash
cd ~/go2_ws
rosdep install --from-paths src --ignore-src -r -y
```

### Step 4: Build
```bash
cd ~/go2_ws
colcon build --symlink-install
source install/setup.bash
```

### Step 5: Launch
```bash
ros2 launch go2_description gazebo.launch.py world:=simple_flat.sdf
```

## 📋 Dependency Checklist

### System Package
- `ros-humble-ignition-gazebo*`
- `ros-humble-ros-gz-sim`
- `ros-humble-ros-gz-bridge`
- `ros-humble-robot-state-publisher`
- `ros-humble-joint-state-publisher-gui`
- `ros-humble-position-controllers`

Install all at once:
```bash
sudo apt install ros-humble-ignition-gazebo* ros-humble-ros-gz-sim \
  ros-humble-ros-gz-bridge ros-humble-robot-state-publisher \
  ros-humble-joint-state-publisher-gui ros-humble-position-controllers
```

## 🌍 Available Test Worlds

| World | Complexity | Best For | Launch |
|-------|-----------|----------|--------|
| simple_flat.sdf | Low | Gait testing, basic locomotion | `world:=simple_flat.sdf` |
| obstacle_world.sdf | Medium | Navigation, obstacle avoidance | `world:=obstacle_world.sdf` |
| terrain_world.sdf | High | Advanced locomotion, terrain variation | `world:=terrain_world.sdf` |

## 🔧 Configuration Guide

### Modify Physics (in SDF world files)
```xml
<physics name="default_physics" type="ode">
  <max_step_size>0.001</max_step_size>        <!-- Smaller = more accurate, slower -->
  <real_time_factor>1.0</real_time_factor>    <!-- 1.0 = real-time, >1.0 = faster -->
</physics>
```

### Modify Controller Gains (in YAML config)
```yaml
fl_hip_position_controller:
  pid: {p: 100.0, i: 0.0, d: 10.0}  # Adjust these values
```

### Modify Robot Initial Position (in launch file)
```python
args=[
    '-name', 'go2',
    '-topic', 'robot_description',
    '-x', '0.0',      # X position
    '-y', '0.0',      # Y position
    '-z', '0.3'       # Z position (height above ground)
]
```

## 🎮 Usage Examples

### 1. Launch with Flat World
```bash
ros2 launch go2_description gazebo.launch.py world:=simple_flat.sdf
```

### 2. Launch with Obstacles
```bash
ros2 launch go2_description gazebo.launch.py world:=obstacle_world.sdf
```

### 3. Launch with Terrain
```bash
ros2 launch go2_description gazebo.launch.py world:=terrain_world.sdf
```

### 4. Run Control Example
```bash
python3 ~/go2_ws/src/go2_description/scripts/go2_controller_example.py
```

## 📊 Robot Specifications

### Dimensions
- Length: 0.3762 m
- Width: 0.0935 m
- Height (with legs extended): ~0.5 m
- Total Mass: ~10 kg

### Joint Capabilities
- **12 revolute joints** (3 per leg)
- Max velocity: 20-30 rad/s (joint dependent)
- Max effort: 23.7-35.55 Nm (joint dependent)

### Actuators
- 3 joints per leg (hip, thigh, calf)
- Position and velocity control capable

## 🔍 Verification Steps

After setup, verify everything works:

```bash
# 1. Check if package is found
ros2 pkg list | grep go2_description

# 2. Check launch file
ros2 launch go2_description gazebo.launch.py --show-args

# 3. Launch gazebo and see robot
ros2 launch go2_description gazebo.launch.py world:=simple_flat.sdf

# 4. In new terminal, check joint states
ros2 topic echo /joint_states | head -20

# 5. List available services and actions
ros2 service list
ros2 action list
```

## 🐛 Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "Command not found: ros2" | ROS2 not sourced | `source /opt/ros/humble/setup.bash` |
| "Package not found" | Package not built | `colcon build --symlink-install` |
| Robot not visible | Spawn failed | Check terminal output for errors |
| No sensor data | Bridge not configured | Check gazebo.launch.py ros_gz_bridge |
| Slow simulation | Too many physics updates | Increase `max_step_size` in SDF |

## 📚 Additional Resources

### Official Documentation
- ROS2: https://docs.ros.org/
- Ignition Gazebo: https://ignitionrobotics.org/
- URDF: http://wiki.ros.org/urdf
- SDF Format: http://sdformat.org/

### Repositories
- Unitree Go2 (if public): https://github.com/unitreerobotics
- ROS2 Control: https://control.ros.org/

### Learning Resources
- ROS2 Tutorials: https://docs.ros.org/en/humble/Tutorials.html
- Gazebo Simulation: https://gazebosim.org/docs

## 📝 Next Steps

1. ✅ Build and launch the basic simulation
2. ✅ Verify robot appears in Gazebo
3. ✅ Test with different worlds
4. ✅ Run control example script
5. ⬜ Add your own mesh files (DAE format)
6. ⬜ Implement custom gait controller
7. ⬜ Add sensors (camera, lidar, etc.)
8. ⬜ Integrate with Nav2 for autonomous navigation

## 📞 Support

If you encounter issues:

1. Check the README.md troubleshooting section
2. Review Ignition Gazebo logs: `~/.ignition/`
3. Check ROS2 topics: `ros2 topic list`
4. Post on ROS Answers: https://answers.ros.org/

---

**Last Updated:** 2024
**Compatible With:** ROS2 Humble, Ignition Gazebo Garden/Fortress
**Status:** ✅ Ready for Use
