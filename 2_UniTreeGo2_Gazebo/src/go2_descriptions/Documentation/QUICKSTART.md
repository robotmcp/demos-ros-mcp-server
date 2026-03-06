# Quick Start Guide - Go2 Gazebo Simulation

## 60-Second Setup

### 1. Build (1 minute)
```bash
cd ~/go2_ws
colcon build --symlink-install
source install/setup.bash
```

### 2. Launch (10 seconds)
```bash
ros2 launch go2_description gazebo.launch.py world:=simple_flat.sdf
```

You should see:
- Ignition Gazebo window opens
- Go2 robot appears in the center
- Ground plane visible

## What You Can Do Now

### Test 1: Visualize Robot
```bash
ros2 run rviz2 rviz2
# Add "Robot Model" display, set Fixed Frame to "base"
```

### Test 2: Check Joint States
```bash
# In new terminal
ros2 topic echo /joint_states | head -20
```

### Test 3: Move a Joint
```bash
# Move front-left hip joint to 0.5 radians
ros2 service call /FL_hip_joint_controller/set_parameters rcl_interfaces/srv/SetParameters \
  "{parameters: [{name: 'P', value: {type: 3, double_value: 0.5}}]}"
```

### Test 4: Try Different World
```bash
ros2 launch go2_description gazebo.launch.py world:=obstacle_world.sdf
```

## Expected Behavior

### Initial State
- Robot spawns 30cm above ground
- Legs hang naturally
- Robot settles due to gravity

### Physics
- Gravity: 9.81 m/s² (downward)
- Time step: 0.001s
- Real-time factor: 1.0 (1 second sim = 1 second real)

## Keyboard Controls in Gazebo

- **Scroll wheel**: Zoom camera
- **Right-click + drag**: Rotate view
- **Middle-click + drag**: Pan view
- **V**: Toggle vertex visualization
- **Space**: Pause/resume simulation

## Keyboard Shortcuts

| Action | Command |
|--------|---------|
| Pause simulation | `Space` |
| Step simulation | `S` |
| Reset simulation | `R` |
| Wireframe mode | `W` |
| Toggle grid | `G` |

## Next Steps

1. **Learn URDF**: Understand robot structure in `urdf/go2.urdf`
2. **Create Gait Controller**: Develop locomotion controller node
3. **Add Sensors**: Include camera/lidar for perception
4. **Implement Navigation**: Use ROS2 Nav2 stack
5. **Optimization**: Tune physics and controller parameters

## Useful Commands

### List all topics
```bash
ros2 topic list
```

### List all services
```bash
ros2 service list
```

### List all nodes
```bash
ros2 node list
```

### Record simulation
```bash
ros2 bag record -a
```

### Play recorded data
```bash
ros2 bag play rosbag2_<timestamp>
```

## Common Issues

| Issue | Solution |
|-------|----------|
| "World not found" | Use full path: `/full/path/to/simple_flat.sdf` |
| Robot not visible | Check spawn messages in terminal |
| Simulation too slow | Reduce world complexity or use headless rendering |
| High CPU usage | Lower max_step_size or reduce model complexity |

## File Locations

```
go2_description/
├── urdf/go2.urdf           ← Robot definition
├── worlds/simple_flat.sdf  ← Default world
├── launch/gazebo.launch.py ← Main launch script
└── config/                 ← Controller config
```

## Performance Tips

1. **Headless Rendering**: Disable GUI for faster simulation
   ```bash
   export IGN_HEADLESS=1
   ```

2. **Reduce Physics Update Rate**: Edit world SDF
   ```xml
   <max_step_size>0.01</max_step_size>  <!-- 10ms instead of 1ms -->
   ```

3. **Disable Rendering**: Launch without GUI
   ```bash
   ros2 launch go2_description gazebo.launch.py --headless
   ```

## Getting Help

1. Check console output for error messages
2. Verify all dependencies are installed
3. Review ROS2 and Gazebo documentation
4. Check package.xml for missing dependencies

---

**Ready to start?** Run: `ros2 launch go2_description gazebo.launch.py world:=simple_flat.sdf`
