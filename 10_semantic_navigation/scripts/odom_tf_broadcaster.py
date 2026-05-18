#!/usr/bin/env python3
"""Publish odom -> base_link TF from the bridged Odometry message."""

import argparse

import rclpy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.parameter import Parameter
from tf2_ros import TransformBroadcaster


class OdomTfBroadcaster(Node):
    """Convert /odom pose into the navigation TF edge expected by SLAM/Nav2."""

    def __init__(self, odom_topic: str, odom_frame: str, base_frame: str):
        super().__init__(
            'odom_tf_broadcaster',
            parameter_overrides=[Parameter('use_sim_time', Parameter.Type.BOOL, True)],
        )
        self.odom_frame = odom_frame
        self.base_frame = base_frame
        self.tf_broadcaster = TransformBroadcaster(self)
        self.odom_sub = self.create_subscription(Odometry, odom_topic, self.odom_callback, 50)
        self.get_logger().info(
            f'Publishing TF from {odom_topic}: {self.odom_frame} -> {self.base_frame}')

    def odom_callback(self, msg: Odometry) -> None:
        transform = TransformStamped()
        transform.header.stamp = msg.header.stamp
        transform.header.frame_id = msg.header.frame_id or self.odom_frame
        transform.child_frame_id = msg.child_frame_id or self.base_frame
        transform.transform.translation.x = msg.pose.pose.position.x
        transform.transform.translation.y = msg.pose.pose.position.y
        transform.transform.translation.z = msg.pose.pose.position.z
        transform.transform.rotation = msg.pose.pose.orientation
        self.tf_broadcaster.sendTransform(transform)


def main() -> None:
    parser = argparse.ArgumentParser(description='Publish odom -> base_link TF from Odometry')
    parser.add_argument('--odom-topic', default='/odom')
    parser.add_argument('--odom-frame', default='odom')
    parser.add_argument('--base-frame', default='base_link')
    args = parser.parse_args()

    rclpy.init()
    node = OdomTfBroadcaster(args.odom_topic, args.odom_frame, args.base_frame)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
