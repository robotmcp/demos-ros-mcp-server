from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
    ThisLaunchFileDir,
)
from launch_ros.actions import Node

from launch import LaunchDescription


def generate_launch_description():
    """Ignition Gazebo + ros_gz_bridge + rosbridge + rosapi for quadcopter demo."""

    world_arg = DeclareLaunchArgument(
        "world", default_value="quadcopter_minimal.sdf",
        description="SDF world file in this example directory"
    )
    world_file = PathJoinSubstitution([ThisLaunchFileDir(), LaunchConfiguration("world")])

    gazebo_sim = ExecuteProcess(
        cmd=['ign', 'gazebo', '-r', world_file],
        output='screen'
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/X3/gazebo/command/twist@geometry_msgs/msg/Twist]ignition.msgs.Twist',
            '/X3/enable@std_msgs/msg/Bool]ignition.msgs.Boolean',
            '/model/x3/odometry@nav_msgs/msg/Odometry[ignition.msgs.Odometry',
            '/model/x3/pose@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V',
            '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock',
        ],
        remappings=[
            ('/X3/gazebo/command/twist', '/quadcopter/cmd_vel'),
            ('/X3/enable',               '/quadcopter/enable'),
            ('/model/x3/odometry',       '/quadcopter/odom'),
            ('/model/x3/pose',           '/tf'),
        ],
        output='screen'
    )

    port_arg = DeclareLaunchArgument(
        "port", default_value="9090",
        description="Port for rosbridge websocket server"
    )

    rosbridge_node = Node(
        package="rosbridge_server",
        executable="rosbridge_websocket",
        name="rosbridge_websocket",
        output="screen",
        parameters=[{'port': LaunchConfiguration("port")}]
    )

    rosapi_node = Node(
        package="rosapi",
        executable="rosapi_node",
        name="rosapi",
        output="screen"
    )

    return LaunchDescription([
        world_arg,
        port_arg,
        gazebo_sim,
        bridge,
        rosbridge_node,
        rosapi_node,
    ])
