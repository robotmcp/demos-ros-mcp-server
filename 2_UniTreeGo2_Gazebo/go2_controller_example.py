#!/usr/bin/env python3
"""
Example script to control Go2 robot in Gazebo simulation.
Demonstrates joint trajectory control and basic gait patterns.
"""

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import math
import time

class Go2Controller(Node):
    def __init__(self):
        super().__init__('go2_controller')
        
        # Publisher for joint trajectory
        self.publisher = self.create_publisher(
            JointTrajectory,
            '/joint_trajectory_controller/joint_trajectory',
            10
        )
        
        # Joint names for all 12 joints (3 per leg, 4 legs)
        self.joint_names = [
            # Front Left
            'FL_hip_joint', 'FL_thigh_joint', 'FL_calf_joint',
            # Front Right
            'FR_hip_joint', 'FR_thigh_joint', 'FR_calf_joint',
            # Rear Left
            'RL_hip_joint', 'RL_thigh_joint', 'RL_calf_joint',
            # Rear Right
            'RR_hip_joint', 'RR_thigh_joint', 'RR_calf_joint'
        ]
        
        self.get_logger().info('Go2 Controller initialized')
    
    def send_trajectory(self, positions, duration=1.0):
        """
        Send a joint trajectory command to the robot.
        
        Args:
            positions: List of 12 joint positions (rad)
            duration: Time to reach target positions (seconds)
        """
        trajectory = JointTrajectory()
        trajectory.header.stamp = self.get_clock().now().to_msg()
        trajectory.joint_names = self.joint_names
        
        point = JointTrajectoryPoint()
        point.positions = positions
        point.velocities = [0.0] * len(self.joint_names)
        point.accelerations = [0.0] * len(self.joint_names)
        point.time_from_start.sec = int(duration)
        point.time_from_start.nanosec = int((duration % 1.0) * 1e9)
        
        trajectory.points = [point]
        self.publisher.publish(trajectory)
        self.get_logger().info(f'Sent trajectory: {positions}')
    
    def home_position(self):
        """Move robot to default standing position."""
        # Neutral position: all joints at 0
        positions = [0.0] * 12
        self.send_trajectory(positions, duration=2.0)
        self.get_logger().info('Moving to home position')
    
    def squat(self):
        """Make robot perform a squat motion."""
        # Thigh joints: bend down
        positions = [
            0.0, -0.5, -0.5,  # FL
            0.0, -0.5, -0.5,  # FR
            0.0, -0.5, -0.5,  # RL
            0.0, -0.5, -0.5   # RR
        ]
        self.send_trajectory(positions, duration=1.0)
        self.get_logger().info('Performing squat')
        time.sleep(1.5)
        
        # Return to home
        self.home_position()
    
    def wave_front_left_leg(self):
        """Make front-left leg wave."""
        # Lift front-left leg
        positions = [
            0.5, -0.3, -0.8,  # FL - raised
            0.0, 0.0, 0.0,    # FR
            0.0, 0.0, 0.0,    # RL
            0.0, 0.0, 0.0     # RR
        ]
        self.send_trajectory(positions, duration=1.0)
        self.get_logger().info('Waving front-left leg')
        time.sleep(1.5)
        
        # Return to home
        self.home_position()
    
    def trot_gait_cycle(self):
        """Simulate a trotting gait (diagonal legs move together)."""
        self.get_logger().info('Starting trot gait')
        
        # Phase 1: Diagonal 1 (FL & RR) lift
        positions = [
            0.0, -0.3, -0.8,  # FL - raised
            0.0, 0.0, 0.0,    # FR - ground
            0.0, 0.0, 0.0,    # RL - ground
            0.0, -0.3, -0.8   # RR - raised
        ]
        self.send_trajectory(positions, duration=0.5)
        time.sleep(0.6)
        
        # Phase 2: Diagonal 2 (FR & RL) lift
        positions = [
            0.0, 0.0, 0.0,    # FL - ground
            0.0, -0.3, -0.8,  # FR - raised
            0.0, -0.3, -0.8,  # RL - raised
            0.0, 0.0, 0.0     # RR - ground
        ]
        self.send_trajectory(positions, duration=0.5)
        time.sleep(0.6)
        
        # Return to home
        self.home_position()
    
    def walk_forward_simulation(self):
        """Simulate forward walking motion (simplified)."""
        self.get_logger().info('Simulating forward walk')
        
        # This is a simplified version - real quadruped gait is more complex
        for step in range(3):
            self.get_logger().info(f'Step {step + 1}/3')
            
            # Step pattern: diagonal trot
            if step % 2 == 0:
                # Lift FL & RR, move body
                positions = [
                    0.2, -0.2, -0.8,  # FL - raised
                    -0.1, 0.1, 0.0,   # FR - extending
                    -0.1, 0.1, 0.0,   # RL - extending
                    0.2, -0.2, -0.8   # RR - raised
                ]
            else:
                # Lift FR & RL, move body
                positions = [
                    -0.1, 0.1, 0.0,   # FL - extending
                    0.2, -0.2, -0.8,  # FR - raised
                    0.2, -0.2, -0.8,  # RL - raised
                    -0.1, 0.1, 0.0    # RR - extending
                ]
            
            self.send_trajectory(positions, duration=0.8)
            time.sleep(1.0)
        
        # Return to home
        self.home_position()


def main(args=None):
    rclpy.init(args=args)
    controller = Go2Controller()
    
    # Interactive menu
    print("\n=== Go2 Robot Controller ===")
    print("1. Home position")
    print("2. Squat")
    print("3. Wave front-left leg")
    print("4. Trot gait")
    print("5. Walk forward (simplified)")
    print("q. Exit")
    
    try:
        while True:
            choice = input("\nEnter command (1-5, q to quit): ").strip().lower()
            
            if choice == '1':
                controller.home_position()
            elif choice == '2':
                controller.squat()
            elif choice == '3':
                controller.wave_front_left_leg()
            elif choice == '4':
                controller.trot_gait_cycle()
            elif choice == '5':
                controller.walk_forward_simulation()
            elif choice == 'q':
                print("Exiting...")
                break
            else:
                print("Invalid command")
            
            # Small delay between commands
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        controller.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
