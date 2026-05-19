"""Launch the standalone living-room semantic mapping demo."""

import os
import socket
import subprocess
import sys

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _arg(name: str, default_value: str, description: str) -> DeclareLaunchArgument:
    return DeclareLaunchArgument(name, default_value=default_value, description=description)


def _is_port_available(port: int) -> bool:
    """Return True when the local TCP port can be bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(('0.0.0.0', port))
            return True
        except OSError:
            return False


def _create_rosbridge_node(context):
    requested_port = int(LaunchConfiguration('port').perform(context))
    auto_fallback = LaunchConfiguration('auto_fallback_port').perform(context).lower() in (
        '1', 'true', 'yes', 'on'
    )
    fallback_tries = int(LaunchConfiguration('port_fallback_tries').perform(context))

    selected_port = requested_port
    if auto_fallback and not _is_port_available(requested_port):
        for candidate in range(requested_port + 1, requested_port + fallback_tries + 1):
            if _is_port_available(candidate):
                selected_port = candidate
                break

    actions = []
    if selected_port != requested_port:
        actions.append(LogInfo(
            msg=(
                f'rosbridge requested port {requested_port} is busy, '
                f'using fallback port {selected_port}.'
            )
        ))
    elif not _is_port_available(requested_port):
        actions.append(LogInfo(
            msg=(
                f'rosbridge port {requested_port} is busy and no fallback port was found. '
                'rosbridge may fail to start.'
            )
        ))

    actions.append(Node(
        package='rosbridge_server',
        executable='rosbridge_websocket',
        name='rosbridge_websocket',
        output='screen',
        parameters=[{'port': selected_port}],
    ))
    return actions


def _find_conflicting_processes() -> list[str]:
    """Find already-running sim/bridge processes that can publish duplicate /clock."""
    try:
        output = subprocess.check_output(
            ['ps', '-eo', 'pid=,args='],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        return []

    conflicts = []
    current_pid = os.getpid()
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            pid_text, command = line.split(maxsplit=1)
            pid = int(pid_text)
        except ValueError:
            continue
        if pid == current_pid:
            continue
        if 'ros_gz_bridge/parameter_bridge' in command and '/clock@rosgraph_msgs/msg/Clock' in command:
            conflicts.append(line)
        elif 'ign gazebo' in command and 'living_room_world.sdf' in command:
            conflicts.append(line)
        elif 'ign gazebo' in command and 'house_world.sdf' in command:
            conflicts.append(line)

    return conflicts


def _preflight_single_clock(context):
    allow_existing = LaunchConfiguration('allow_existing_sim').perform(context).lower() in (
        '1', 'true', 'yes', 'on'
    )
    if allow_existing:
        return []

    conflicts = _find_conflicting_processes()
    if not conflicts:
        return []

    preview = '\n'.join(conflicts[:5])
    if len(conflicts) > 5:
        preview += f'\n... and {len(conflicts) - 5} more'

    raise RuntimeError(
        'Refusing to start semantic mapping because another Gazebo/clock bridge '
        f'is already running:\n{preview}\n'
        'Stop the old launch first, or pass allow_existing_sim:=true to override.'
    )


def generate_launch_description():
    pkg_dir = os.path.dirname(os.path.realpath(__file__))
    config_dir = os.path.join(pkg_dir, 'config')
    scripts_dir = os.path.join(pkg_dir, 'scripts')

    default_world = os.path.join(pkg_dir, 'living_room_world.sdf')
    default_store = os.path.join(pkg_dir, 'data', 'objects.json')
    default_vector_store = os.path.join(pkg_dir, 'data', 'semantic_memory.sqlite3')
    default_image_dir = os.path.join(pkg_dir, 'data', 'semantic_images')
    default_landmarks = os.path.join(config_dir, 'semantic_landmarks.json')
    slam_params = os.path.join(config_dir, 'vla_slam_params.yaml')
    nav2_params = os.path.join(config_dir, 'vla_nav2_params.yaml')
    rviz_config = os.path.join(config_dir, 'vla_semantic_nav.rviz')

    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    nav2_launch_dir = os.path.join(nav2_bringup_dir, 'launch')

    declarations = [
        _arg('world', default_world, 'Path to the custom living-room SDF.'),
        _arg('rviz', 'true', 'Launch RViz2 with the semantic mapping display.'),
        _arg('explore', 'true', 'Launch the biased frontier explorer.'),
        _arg('duration', '0', 'Explorer timeout in seconds; 0 means unlimited.'),
        _arg('min_frontier_size', '0.2', 'Minimum frontier cluster size in meters.'),
        _arg('frontier_wall_clearance', '0.18', 'Ignore frontiers too close to occupied cells.'),
        _arg('frontier_goal_timeout', '90.0', 'Seconds before a Nav2 frontier goal is blacklisted.'),
        _arg('semantic_store', default_store, 'Path to the semantic object memory JSON file.'),
        _arg('semantic_vector_store', default_vector_store, 'Path to the semantic SQLite database.'),
        _arg('semantic_image_dir', default_image_dir, 'Directory for semantic capture JPEG snapshots.'),
        _arg('semantic_observer', 'true', 'Run the OpenAI semantic camera observer.'),
        _arg('semantic_vision_model', 'gpt-4.1-mini', 'OpenAI vision model for semantic labeling.'),
        _arg('semantic_embedding_model', 'text-embedding-3-small', 'OpenAI embedding model.'),
        _arg('semantic_openai_api_base', '', 'Optional OpenAI-compatible API base URL.'),
        _arg('semantic_openai_timeout', '45.0', 'Seconds before an OpenAI request times out.'),
        _arg('semantic_observer_min_confidence', '0.35', 'Minimum object confidence to store.'),
        _arg('semantic_capture_angles', '4', 'Number of yaw angles to capture at each frontier.'),
        _arg('semantic_capture_radius', '1.0', 'Meters around a frontier considered captured.'),
        _arg('semantic_area_captured_min_views', '3', 'Minimum nearby yaw buckets for captured areas.'),
        _arg('semantic_image_detail', 'low', 'OpenAI image detail: low, high, or auto.'),
        _arg('semantic_capture_timeout', '150.0', 'Max seconds to wait for a semantic sweep.'),
        _arg('semantic_store_image_only_captures', 'true', 'Save frontier JPEG captures without OpenAI.'),
        _arg('semantic_landmarks', default_landmarks, 'Known living-room landmarks for fallback labeling.'),
        _arg('semantic_landmark_fallback', 'false', 'Use known landmarks when OpenAI vision is unavailable.'),
        _arg('port', '9090', 'Port for rosbridge_websocket.'),
        _arg('auto_fallback_port', 'true', 'Use the next available port when `port` is busy.'),
        _arg('port_fallback_tries', '20', 'Sequential fallback ports to check.'),
        _arg('allow_existing_sim', 'false', 'Allow startup when another sim/clock bridge is running.'),
    ]

    single_clock_preflight = OpaqueFunction(function=_preflight_single_clock)

    gazebo_sim = ExecuteProcess(
        cmd=['ign', 'gazebo', '-r', '-v', '3', LaunchConfiguration('world')],
        output='screen',
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry',
            '/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan',
            '/camera/image@sensor_msgs/msg/Image[ignition.msgs.Image',
            '/camera/camera_info@sensor_msgs/msg/CameraInfo[ignition.msgs.CameraInfo',
            '/imu@sensor_msgs/msg/Imu[ignition.msgs.IMU',
            '/joint_states@sensor_msgs/msg/JointState[ignition.msgs.Model',
            '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock',
        ],
        output='screen',
    )

    odom_tf = ExecuteProcess(
        cmd=[
            sys.executable,
            os.path.join(scripts_dir, 'odom_tf_broadcaster.py'),
            '--odom-topic', '/odom',
            '--odom-frame', 'odom',
            '--base-frame', 'base_link',
        ],
        output='screen',
    )

    scan_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='vla_lidar_static_tf',
        arguments=[
            '--x', '0',
            '--y', '0',
            '--z', '0.15',
            '--roll', '0',
            '--pitch', '0',
            '--yaw', '0',
            '--frame-id', 'base_link',
            '--child-frame-id', 'vla_bot/base_link/gpu_lidar',
        ],
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

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

    rosbridge_node = OpaqueFunction(function=_create_rosbridge_node)
    rosapi_node = Node(
        package='rosapi',
        executable='rosapi_node',
        name='rosapi',
        output='screen',
    )

    semantic_memory = TimerAction(
        period=8.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    sys.executable,
                    os.path.join(scripts_dir, 'semantic_memory_node.py'),
                    '--store',
                    LaunchConfiguration('semantic_store'),
                    '--vector-store',
                    LaunchConfiguration('semantic_vector_store'),
                    '--embedding-model',
                    LaunchConfiguration('semantic_embedding_model'),
                ],
                output='screen',
            ),
        ],
    )

    semantic_nav = TimerAction(
        period=12.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    sys.executable,
                    os.path.join(scripts_dir, 'semantic_nav_node.py'),
                    '--store',
                    LaunchConfiguration('semantic_store'),
                    '--vector-store',
                    LaunchConfiguration('semantic_vector_store'),
                    '--vision-model',
                    LaunchConfiguration('semantic_vision_model'),
                    '--openai-timeout',
                    LaunchConfiguration('semantic_openai_timeout'),
                ],
                output='screen',
            ),
        ],
    )

    semantic_observer = TimerAction(
        period=14.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    sys.executable,
                    os.path.join(scripts_dir, 'semantic_camera_observer.py'),
                    '--vector-store',
                    LaunchConfiguration('semantic_vector_store'),
                    '--image-dir',
                    LaunchConfiguration('semantic_image_dir'),
                    '--vision-model',
                    LaunchConfiguration('semantic_vision_model'),
                    '--embedding-model',
                    LaunchConfiguration('semantic_embedding_model'),
                    '--api-base',
                    LaunchConfiguration('semantic_openai_api_base'),
                    '--openai-timeout',
                    LaunchConfiguration('semantic_openai_timeout'),
                    '--capture-angles',
                    LaunchConfiguration('semantic_capture_angles'),
                    '--capture-radius',
                    LaunchConfiguration('semantic_capture_radius'),
                    '--area-captured-min-views',
                    LaunchConfiguration('semantic_area_captured_min_views'),
                    '--min-confidence',
                    LaunchConfiguration('semantic_observer_min_confidence'),
                    '--capture-timeout',
                    LaunchConfiguration('semantic_capture_timeout'),
                    '--image-detail',
                    LaunchConfiguration('semantic_image_detail'),
                    '--store-image-only-captures',
                    LaunchConfiguration('semantic_store_image_only_captures'),
                    '--landmarks',
                    LaunchConfiguration('semantic_landmarks'),
                    '--landmark-fallback',
                    LaunchConfiguration('semantic_landmark_fallback'),
                ],
                output='screen',
                condition=IfCondition(LaunchConfiguration('semantic_observer')),
            ),
        ],
    )

    frontier_explorer = TimerAction(
        period=15.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    sys.executable,
                    os.path.join(scripts_dir, 'biased_frontier_explorer.py'),
                    '--duration',
                    LaunchConfiguration('duration'),
                    '--min-frontier-size',
                    LaunchConfiguration('min_frontier_size'),
                    '--goal-timeout',
                    LaunchConfiguration('frontier_goal_timeout'),
                    '--wall-clearance',
                    LaunchConfiguration('frontier_wall_clearance'),
                    '--semantic-capture',
                    LaunchConfiguration('semantic_observer'),
                    '--semantic-capture-timeout',
                    LaunchConfiguration('semantic_capture_timeout'),
                ],
                output='screen',
                condition=IfCondition(LaunchConfiguration('explore')),
            ),
        ],
    )

    rviz_node = TimerAction(
        period=12.0,
        actions=[
            Node(
                package='rviz2',
                executable='rviz2',
                name='rviz2',
                arguments=['-d', rviz_config] if os.path.exists(rviz_config) else [],
                parameters=[{'use_sim_time': True}],
                output='screen',
                condition=IfCondition(LaunchConfiguration('rviz')),
            ),
        ],
    )

    return LaunchDescription([
        *declarations,
        single_clock_preflight,
        gazebo_sim,
        bridge,
        odom_tf,
        scan_tf,
        slam_toolbox,
        nav2_navigation,
        rosbridge_node,
        rosapi_node,
        semantic_memory,
        semantic_nav,
        semantic_observer,
        rviz_node,
        frontier_explorer,
    ])
