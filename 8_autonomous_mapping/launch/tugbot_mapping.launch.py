"""
Autonomous SLAM Mapping Launch File for TugBot (Ignition Gazebo)
=================================================================
Same frontier exploration algorithm as the TurtleBot3 version,
but configured for the TugBot robot (different bridge topics, TF frames, model).

Usage:
  source /opt/ros/humble/setup.bash
  ros2 launch tugbot_mapping.launch.py
  ros2 launch tugbot_mapping.launch.py world:=/path/to/world.sdf
  ros2 launch tugbot_mapping.launch.py rviz:=false explore:=false
"""

import os
import sys

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
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
    default_world = os.path.join(base_dir, 'worlds', 'simple_room_tugbot.sdf')
    slam_params = os.path.join(base_dir, 'config', 'tugbot_slam_params.yaml')
    nav2_params = os.path.join(base_dir, 'config', 'tugbot_nav2_params.yaml')
    frontier_script = os.path.join(base_dir, 'scripts', 'frontier_explorer.py')
    rviz_config = os.path.join(base_dir, 'config', 'slam_nav2.rviz')

    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    nav2_launch_dir = os.path.join(nav2_bringup_dir, 'launch')

    # -- Launch Arguments --
    declare_world = DeclareLaunchArgument(
        'world', default_value=default_world,
        description='Path to Ignition SDF world file (must contain TugBot)')

    declare_rviz = DeclareLaunchArgument(
        'rviz', default_value='true',
        description='Launch RViz2 for visualization')

    declare_explore = DeclareLaunchArgument(
        'explore', default_value='true',
        description='Launch frontier explorer for autonomous exploration')

    declare_speed = DeclareLaunchArgument(
        'speed', default_value='0.18',
        description='Explorer forward speed in m/s')

    declare_duration = DeclareLaunchArgument(
        'duration', default_value='0',
        description='Explorer timeout in seconds (0=unlimited)')

    # -- 1. Ignition Gazebo --
    # TugBot model is included in the world SDF (from Ignition Fuel)
    gazebo_sim = ExecuteProcess(
        cmd=['ign', 'gazebo', '-r', LaunchConfiguration('world')],
        output='screen',
    )

    # -- 2. ros_gz_bridge --
    # TugBot uses different Ignition topic paths than TurtleBot3.
    # The scan topic includes the world name (world_demo).
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/model/tugbot/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist',
            '/model/tugbot/odometry@nav_msgs/msg/Odometry[ignition.msgs.Odometry',
            '/world/world_demo/model/tugbot/link/scan_front/sensor/scan_front/scan'
            '@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan',
            '/model/tugbot/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V',
            '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock',
        ],
        remappings=[
            ('/model/tugbot/cmd_vel', '/cmd_vel'),
            ('/model/tugbot/odometry', '/odom'),
            ('/model/tugbot/tf', '/tf'),
            ('/world/world_demo/model/tugbot/link/scan_front/sensor/scan_front/scan',
             '/scan'),
        ],
        output='screen',
    )

    # -- 3. Static TF: base_link -> TugBot scan_front frame --
    # The TugBot LiDAR is offset 0.221m forward and 0.1404m up from base_link
    scan_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=[
            '0.221', '0', '0.1404', '0', '0', '0',
            'base_link', 'tugbot/scan_front/scan_front',
        ],
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    # -- 4. SLAM Toolbox (online async) --
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

    # -- 5. Nav2 Navigation Stack --
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

    # -- 6. Frontier Explorer (SAME script as TurtleBot3 version) --
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

    # -- 7. RViz2 --
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
        declare_speed,
        declare_duration,
        # Nodes (in startup order)
        gazebo_sim,
        bridge,
        scan_tf,
        slam_toolbox,          # +5s
        nav2_navigation,       # +10s
        rviz_node,             # +12s
        frontier_explorer,     # +15s
    ])
