#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Get package directories
    go2_description_dir = get_package_share_directory('go2_description')
    
    # Declare launch arguments
    world_arg = DeclareLaunchArgument(
        'world',
        default_value='empty.sdf',
        description='Gazebo world file'
    )
    
    verbose_arg = DeclareLaunchArgument(
        'verbose',
        default_value='false',
        description='Enable verbose output'
    )
    
    paused_arg = DeclareLaunchArgument(
        'paused',
        default_value='false',
        description='Start simulation paused'
    )
    
    # Get URDF file path
    urdf_file = os.path.join(go2_description_dir, 'urdf', 'go2.urdf')
    
    # Read URDF file
    with open(urdf_file, 'r') as infp:
        robot_desc = infp.read()
    
    # Robot state publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_desc,
            'use_sim_time': True
        }]
    )
    
    # Ignition Gazebo
    gz_sim = ExecuteProcess(
        cmd=[
            'ign', 'gazebo',
            '-v', '4',
            '-r',
            LaunchConfiguration('world'),
            '--headless-rendering'
        ],
        output='screen'
    )
    
    # Spawn entity (robot) into Gazebo
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-name', 'go2',
            '-topic', 'robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.3'
        ]
    )
    
    # Bridge for tf
    tf_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        output='screen',
        arguments=[
            '/tf@tf2_msgs/TFMessage[ignition.msgs.Pose_V',
            '/tf_static@tf2_msgs/TFMessage[ignition.msgs.Pose_V'
        ]
    )
    
    return LaunchDescription([
        world_arg,
        verbose_arg,
        paused_arg,
        robot_state_publisher,
        gz_sim,
        spawn_entity,
        tf_bridge
    ])
