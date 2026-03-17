"""
Autonomous SLAM Mapping Launch File for TurtleBot3 Burger (Ignition Gazebo)
============================================================================
Launches the full autonomous SLAM mapping pipeline:
  1. Ignition Gazebo with a world (default: mapping_world with 4 rooms)
  2. Spawn TurtleBot3 Burger (Ignition-compatible model)
  3. ros_gz_bridge (LiDAR, odometry, cmd_vel, TF, clock, joint_states, IMU)
  4. Robot State Publisher (URDF -> TF)
  5. slam_toolbox (online async SLAM)
  6. Nav2 navigation stack (path planning + obstacle avoidance)
  7. Frontier explorer (autonomous exploration)
  8. RViz2 (visualization)

Usage:
  source /opt/ros/humble/setup.bash
  source <turtlebot3_ws>/install/setup.bash
  ros2 launch autonomous_mapping.launch.py

  # Swap to a different world:
  ros2 launch autonomous_mapping.launch.py world:=/path/to/your_world.sdf x_pose:=0.0 y_pose:=0.0

  # Change exploration timeout (0=unlimited):
  ros2 launch autonomous_mapping.launch.py duration:=300

  # Disable components:
  ros2 launch autonomous_mapping.launch.py rviz:=false
  ros2 launch autonomous_mapping.launch.py explore:=false   # manual driving only

  # Change robot speed:
  ros2 launch autonomous_mapping.launch.py speed:=0.15

Save the map when done:
  ros2 run nav2_map_server map_saver_cli -f my_map --ros-args -p use_sim_time:=true
"""

import os
import sys

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # -- Paths --
    this_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(this_dir)
    default_world = os.path.join(base_dir, 'worlds', 'mapping_world.sdf')
    slam_params = os.path.join(base_dir, 'config', 'slam_params.yaml')
    nav2_params = os.path.join(base_dir, 'config', 'nav2_params.yaml')
    frontier_script = os.path.join(base_dir, 'scripts', 'frontier_explorer.py')
    rviz_config = os.path.join(base_dir, 'config', 'slam_nav2.rviz')

    pkg_turtlebot3_gazebo = get_package_share_directory('turtlebot3_gazebo')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    nav2_launch_dir = os.path.join(nav2_bringup_dir, 'launch')

    models_path = os.path.join(pkg_turtlebot3_gazebo, 'models')

    # -- Launch Arguments --
    declare_world = DeclareLaunchArgument(
        'world', default_value=default_world,
        description='Path to Ignition SDF world file')

    declare_rviz = DeclareLaunchArgument(
        'rviz', default_value='true',
        description='Launch RViz2 for visualization')

    declare_explore = DeclareLaunchArgument(
        'explore', default_value='true',
        description='Launch frontier explorer for autonomous exploration')

    declare_x = DeclareLaunchArgument(
        'x_pose', default_value='-2.5',
        description='Robot X spawn position')

    declare_y = DeclareLaunchArgument(
        'y_pose', default_value='2.5',
        description='Robot Y spawn position')

    declare_speed = DeclareLaunchArgument(
        'speed', default_value='0.18',
        description='Explorer forward speed in m/s')

    declare_duration = DeclareLaunchArgument(
        'duration', default_value='600',
        description='Explorer timeout in seconds (0=unlimited)')

    # -- Environment --
    turtlebot3_model_env = SetEnvironmentVariable(
        name='TURTLEBOT3_MODEL',
        value='burger')

    resource_env = SetEnvironmentVariable(
        name='IGN_GAZEBO_RESOURCE_PATH',
        value=[models_path])

    # -- 1. Ignition Gazebo --
    ignition_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': [LaunchConfiguration('world'), ' -r']
        }.items(),
    )

    # -- 2. Spawn TurtleBot3 Burger --
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-file', os.path.join(
                pkg_turtlebot3_gazebo, 'models',
                'turtlebot3_burger', 'model_ignition.sdf'),
            '-x', LaunchConfiguration('x_pose'),
            '-y', LaunchConfiguration('y_pose'),
            '-z', '0.01',
        ],
        output='screen',
    )

    # -- 3. ros_gz_bridge --
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist@ignition.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry@ignition.msgs.Odometry',
            '/scan@sensor_msgs/msg/LaserScan@ignition.msgs.LaserScan',
            '/imu@sensor_msgs/msg/Imu@ignition.msgs.IMU',
            '/tf@tf2_msgs/msg/TFMessage@ignition.msgs.Pose_V',
            '/joint_states@sensor_msgs/msg/JointState@ignition.msgs.Model',
            '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock',
        ],
        output='screen',
    )

    # -- 4. Robot State Publisher --
    robot_state_publisher = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_turtlebot3_gazebo, 'launch',
                         'robot_state_publisher.launch.py')
        ),
        launch_arguments={'use_sim_time': 'true'}.items(),
    )

    # -- 4b. Static TF: base_scan -> Ignition LiDAR frame --
    # Ignition Gazebo names sensor frames as model_name/link/sensor_name
    # We need to link it to the URDF's base_scan frame
    scan_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=[
            '0', '0', '0', '0', '0', '0',
            'base_scan', 'turtlebot3_burger/base_scan/hls_lfcd_lds',
        ],
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    # -- 5. SLAM Toolbox (online async) --
    slam_toolbox = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='slam_toolbox',
                executable='async_slam_toolbox_node',
                name='slam_toolbox',
                parameters=[slam_params, {'use_sim_time': True}],
                output='screen',
            ),
        ],
    )

    # -- 6. Nav2 Navigation Stack --
    nav2_navigation = TimerAction(
        period=10.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(nav2_launch_dir, 'navigation_launch.py')
                ),
                launch_arguments={
                    'use_sim_time': 'true',
                    'params_file': nav2_params,
                    'autostart': 'true',
                }.items(),
            ),
        ],
    )

    # -- 7. Frontier Explorer --
    frontier_explorer = TimerAction(
        period=15.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    sys.executable, frontier_script,
                    '--speed', LaunchConfiguration('speed'),
                    '--duration', LaunchConfiguration('duration'),
                ],
                output='screen',
                condition=IfCondition(LaunchConfiguration('explore')),
            ),
        ],
    )

    # -- 8. RViz2 --
    rviz_node = TimerAction(
        period=12.0,
        actions=[
            Node(
                package='rviz2',
                executable='rviz2',
                name='rviz2',
                arguments=['-d', rviz_config] if os.path.exists(rviz_config)
                           else [],
                parameters=[{'use_sim_time': True}],
                output='screen',
                condition=IfCondition(LaunchConfiguration('rviz')),
            ),
        ],
    )

    # -- LAUNCH --
    return LaunchDescription([
        # Arguments
        declare_world,
        declare_rviz,
        declare_explore,
        declare_x,
        declare_y,
        declare_speed,
        declare_duration,
        # Environment
        turtlebot3_model_env,
        resource_env,
        # Nodes (in startup order)
        ignition_launch,
        spawn_robot,
        bridge,
        robot_state_publisher,
        scan_tf,
        slam_toolbox,          # +5s
        nav2_navigation,       # +10s
        rviz_node,             # +12s
        frontier_explorer,     # +15s
    ])
