#!/usr/bin/env python3
"""
Autonomous Frontier-Based Explorer for TurtleBot3 Burger
=========================================================
Combines frontier detection (from SLAM map) with direct cmd_vel obstacle
avoidance. No Nav2 stack needed for exploration — just slam_toolbox + this script.

How it works:
  1. Subscribes to /map (from slam_toolbox) and detects frontiers
  2. Picks the best frontier (closest, large enough)
  3. Drives toward it using a simple heading controller
  4. Uses LiDAR for obstacle avoidance
  5. When frontier is reached or blocked, picks the next frontier
  6. Stops when no frontiers remain (map fully explored)

Usage:
  python3 scripts/frontier_explorer.py
  python3 scripts/frontier_explorer.py --speed 0.2 --duration 600
"""

import argparse
import math
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from geometry_msgs.msg import Twist
from nav_msgs.msg import OccupancyGrid, Odometry
from sensor_msgs.msg import LaserScan

# Occupancy grid cell values
FREE = 0
UNKNOWN = -1

# Navigation constants — tuned for TurtleBot3 burger (smaller, slower)
OBSTACLE_STOP = 0.4       # meters — stop and turn (burger is small)
OBSTACLE_SLOW = 1.0       # meters — slow down
TURN_SPEED = 0.5          # rad/s — slower turns for better SLAM scan matching
FRONTIER_REACHED = 0.8    # meters — consider frontier reached
HEADING_TOLERANCE = 0.2   # radians — tighter heading for smoother paths

# Log file
LOG_DIR = Path(__file__).parent.parent
LOG_FILE = LOG_DIR / 'frontier_explorer_debug.log'


class FrontierExplorer(Node):
    """Frontier-based exploration with direct obstacle avoidance."""

    def __init__(self, args):
        super().__init__('frontier_explorer',
                         parameter_overrides=[
                             Parameter('use_sim_time', Parameter.Type.BOOL, True)
                         ])

        self.linear_speed = args.speed
        self.duration = args.duration
        self.min_frontier_size = args.min_frontier_size
        self.start_time = None

        # Debug log file
        self._log_file = open(LOG_FILE, 'w')
        self._log_tick = 0
        self._log('INIT', f'speed={args.speed} duration={args.duration} '
                  f'min_frontier={args.min_frontier_size}')
        self.get_logger().info(f'Debug log: {LOG_FILE}')

        # Robot state
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_yaw = 0.0
        self.has_odom = False

        # Scan state
        self.scan_ranges = []
        self.scan_angle_min = 0.0
        self.scan_angle_inc = 0.0
        self.scan_range_max = 3.5
        self.has_scan = False

        # Map state
        self.map_data = None
        self.map_info = None

        # Exploration state
        self.current_target = None
        self.targets_visited = []
        self.blacklisted = []
        self.goals_reached = 0
        self.state = 'SEEK_FRONTIER'
        self.turn_direction = 1.0
        self.state_timer = 0
        self.start_time = None
        self.no_frontier_count = 0

        # Publishers / Subscribers
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.odom_sub = self.create_subscription(
            Odometry, '/odom', self.odom_callback, 10)

        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE, depth=5)
        self.scan_sub = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, sensor_qos)

        map_qos = QoSProfile(
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE, depth=1)
        self.map_sub = self.create_subscription(
            OccupancyGrid, '/map', self.map_callback, map_qos)

        # Control loop at 10 Hz
        self.timer = self.create_timer(0.1, self.control_loop)

        self.get_logger().info('Frontier explorer started. Waiting for sensors...')

    # -- Debug Logging --

    def _log(self, category, message):
        elapsed = time.time() - self.start_time if self.start_time else 0.0
        ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        line = f'[{ts}] [{elapsed:8.2f}s] [{category:>16s}] {message}'
        self._log_file.write(line + '\n')
        self._log_file.flush()

    # -- Callbacks --

    def odom_callback(self, msg: Odometry):
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        siny = 2.0 * (q.w * q.z + q.x * q.y)
        cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.robot_yaw = math.atan2(siny, cosy)
        if not self.has_odom:
            self.has_odom = True
            self._log('ODOM_ONLINE', f'pos=({self.robot_x:.2f}, {self.robot_y:.2f})')
            self.get_logger().info(
                f'Odom online: ({self.robot_x:.2f}, {self.robot_y:.2f})')

    def scan_callback(self, msg: LaserScan):
        self.scan_ranges = list(msg.ranges)
        self.scan_angle_min = msg.angle_min
        self.scan_angle_inc = msg.angle_increment
        self.scan_range_max = msg.range_max
        if not self.has_scan:
            self.has_scan = True
            self._log('LIDAR_ONLINE', f'rays={len(self.scan_ranges)} '
                      f'range_max={msg.range_max:.1f}')
            self.get_logger().info(
                f'LiDAR online: {len(self.scan_ranges)} rays, '
                f'max range {msg.range_max:.1f}m')

    def map_callback(self, msg: OccupancyGrid):
        self.map_data = np.array(msg.data, dtype=np.int8).reshape(
            (msg.info.height, msg.info.width))
        self.map_info = msg.info

    # -- Helpers --

    def sector_min(self, lo_deg, hi_deg):
        if not self.scan_ranges:
            return float('inf')
        best = float('inf')
        for i, r in enumerate(self.scan_ranges):
            a = math.degrees(self.scan_angle_min + i * self.scan_angle_inc)
            if lo_deg <= a <= hi_deg and 0.05 < r < self.scan_range_max:
                best = min(best, r)
        return best

    def publish_cmd(self, linear, angular):
        msg = Twist()
        msg.linear.x = float(linear)
        msg.angular.z = float(angular)
        self.cmd_pub.publish(msg)

    def stop_robot(self):
        for _ in range(3):
            self.publish_cmd(0.0, 0.0)

    def angle_to_target(self, tx, ty):
        dx = tx - self.robot_x
        dy = ty - self.robot_y
        target_angle = math.atan2(dy, dx)
        diff = target_angle - self.robot_yaw
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        return diff

    def dist_to_target(self, tx, ty):
        return math.hypot(tx - self.robot_x, ty - self.robot_y)

    # -- Frontier Detection --

    def find_best_frontier(self):
        if self.map_data is None:
            return None

        height, width = self.map_data.shape
        resolution = self.map_info.resolution
        origin_x = self.map_info.origin.position.x
        origin_y = self.map_info.origin.position.y

        free_mask = self.map_data == FREE
        occupied_mask = self.map_data > 50
        padded = np.pad(self.map_data, 1, mode='constant', constant_values=50)
        unknown_neighbor = (
            (padded[0:-2, 1:-1] == UNKNOWN) |
            (padded[2:,   1:-1] == UNKNOWN) |
            (padded[1:-1, 0:-2] == UNKNOWN) |
            (padded[1:-1, 2:]   == UNKNOWN)
        )

        dilate_r = max(1, int(0.15 / resolution))
        near_wall = occupied_mask.copy()
        for _ in range(dilate_r):
            p = np.pad(near_wall, 1, mode='constant', constant_values=False)
            near_wall = (p[1:-1, 1:-1] | p[0:-2, 1:-1] | p[2:, 1:-1] |
                         p[1:-1, 0:-2] | p[1:-1, 2:])

        frontier_mask = free_mask & unknown_neighbor & ~near_wall
        frontier_ys, frontier_xs = np.where(frontier_mask)

        if len(frontier_ys) == 0:
            return None

        # Cluster frontier cells (BFS connected components)
        visited = set()
        clusters = []
        min_cells = max(1, int(self.min_frontier_size / resolution))

        for i in range(len(frontier_ys)):
            cell = (int(frontier_ys[i]), int(frontier_xs[i]))
            if cell in visited:
                continue
            cluster_cells = []
            queue = deque([cell])
            visited.add(cell)
            while queue:
                cy, cx = queue.popleft()
                wx = origin_x + (cx + 0.5) * resolution
                wy = origin_y + (cy + 0.5) * resolution
                cluster_cells.append((wx, wy))
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dy == 0 and dx == 0:
                            continue
                        ny, nx = cy + dy, cx + dx
                        if (0 <= ny < height and 0 <= nx < width
                                and (ny, nx) not in visited
                                and frontier_mask[ny, nx]):
                            visited.add((ny, nx))
                            queue.append((ny, nx))
            if len(cluster_cells) >= min_cells:
                clusters.append(cluster_cells)

        if not clusters:
            return None

        # Score each cluster
        candidates = []
        for cluster in clusters:
            best_cell = max(cluster, key=lambda p: self.dist_to_target(p[0], p[1]))
            fx, fy = best_cell
            dist = self.dist_to_target(fx, fy)

            if dist < FRONTIER_REACHED:
                continue
            if any(math.hypot(fx - bx, fy - by) < 0.5
                   for bx, by in self.blacklisted):
                continue
            if any(math.hypot(fx - vx, fy - vy) < 1.0
                   for vx, vy in self.targets_visited):
                continue

            candidates.append((dist, len(cluster), fx, fy))

        if not candidates:
            return None

        candidates.sort(key=lambda c: (-c[1], c[0]))
        _, size, bx, by = candidates[0]
        self.get_logger().info(
            f'Frontier: ({bx:.2f}, {by:.2f}), dist={candidates[0][0]:.2f}m, '
            f'size={size}, {len(candidates)} candidates')
        return (bx, by)

    # -- Control Loop --

    def control_loop(self):
        self._log_tick += 1

        if not self.has_scan or not self.has_odom:
            return

        if self.map_data is None:
            return

        if self.start_time is None:
            self.start_time = time.time()
            self.get_logger().info(
                f'Map received ({self.map_info.width}x{self.map_info.height}). '
                f'Starting exploration!')

        elapsed = time.time() - self.start_time
        if self.duration > 0 and elapsed > self.duration:
            self.finish()
            return

        front = self.sector_min(-15, 15)
        front_left = self.sector_min(15, 45)
        front_right = self.sector_min(-45, -15)
        left = self.sector_min(45, 90)
        right = self.sector_min(-90, -45)

        # -- State machine --

        if self.state == 'SEEK_FRONTIER':
            self.stop_robot()
            target = self.find_best_frontier()
            if target is None:
                self.no_frontier_count += 1
                if self.no_frontier_count >= 300:
                    self.get_logger().info('No more frontiers — exploration complete!')
                    self.finish()
                    return
                if self.no_frontier_count % 20 == 1:
                    self.get_logger().info(
                        f'No frontiers found ({self.no_frontier_count}/300). Spinning...')
                    if self.no_frontier_count % 40 == 1:
                        self.blacklisted.clear()
                self.publish_cmd(0.0, 0.3)
                return
            self.no_frontier_count = 0
            self.current_target = target
            self.state = 'DRIVE_TO'
            self.goals_reached += 1
            self.get_logger().info(
                f'[Goal #{self.goals_reached}] Driving to '
                f'({target[0]:.2f}, {target[1]:.2f})')

        elif self.state == 'DRIVE_TO':
            tx, ty = self.current_target
            dist = self.dist_to_target(tx, ty)
            heading_error = self.angle_to_target(tx, ty)

            if dist < FRONTIER_REACHED:
                self.get_logger().info(
                    f'Frontier reached at ({self.robot_x:.2f}, {self.robot_y:.2f})')
                self.targets_visited.append(self.current_target)
                self.state = 'SEEK_FRONTIER'
                return

            if front < OBSTACLE_STOP:
                self.stop_robot()
                self.state_timer += 1
                if self.state_timer > 30:
                    self.get_logger().warn('Stuck — blacklisting target')
                    self.blacklisted.append(self.current_target)
                    if len(self.blacklisted) > 30:
                        self.blacklisted.pop(0)
                    self.state = 'REVERSING'
                    self.state_timer = 25
                    self.turn_direction = 1.0 if front_left >= front_right else -1.0
                    return

                if front < 0.25:
                    self.state = 'REVERSING'
                    self.state_timer = 20
                    return

                self.turn_direction = 1.0 if front_left >= front_right else -1.0
                self.state = 'TURNING'
                self.state_timer = 20
                return
            else:
                self.state_timer = 0

            if abs(heading_error) > HEADING_TOLERANCE:
                speed = 0.02 if abs(heading_error) > 1.0 else self.linear_speed * 0.3
                self.publish_cmd(speed, TURN_SPEED * (1.0 if heading_error > 0 else -1.0))
            elif front < OBSTACLE_SLOW:
                speed = self.linear_speed * (front / OBSTACLE_SLOW)
                steer = 0.0
                if front_left < OBSTACLE_SLOW and front_left < front_right:
                    steer = -0.3
                elif front_right < OBSTACLE_SLOW and front_right < front_left:
                    steer = 0.3
                self.publish_cmd(max(speed, 0.05), steer)
            else:
                steer = heading_error * 0.5
                if right < 0.8 and left > right * 2:
                    steer += 0.15
                elif left < 0.8 and right > left * 2:
                    steer -= 0.15
                self.publish_cmd(self.linear_speed, steer)

            # Periodically re-evaluate frontier
            if int(elapsed * 10) % 50 == 0:
                new_target = self.find_best_frontier()
                if new_target and new_target != self.current_target:
                    new_dist = self.dist_to_target(*new_target)
                    if new_dist < dist * 0.5:
                        self.get_logger().info(
                            f'Replanning: closer frontier at '
                            f'({new_target[0]:.2f}, {new_target[1]:.2f})')
                        self.current_target = new_target

        elif self.state == 'TURNING':
            self.state_timer -= 1
            if self.state_timer <= 0:
                self.state = 'DRIVE_TO' if self.current_target else 'SEEK_FRONTIER'
            else:
                self.publish_cmd(0.0, TURN_SPEED * self.turn_direction)

        elif self.state == 'REVERSING':
            self.state_timer -= 1
            if self.state_timer <= 0:
                self.turn_direction = 1.0 if front_left >= front_right else -1.0
                self.state = 'TURNING'
                self.state_timer = 30
            else:
                self.publish_cmd(-0.10, 0.0)

    def finish(self):
        self.stop_robot()
        self.timer.cancel()
        elapsed = time.time() - (self.start_time or time.time())

        self._log_file.close()

        self.get_logger().info(
            f'\n{"=" * 60}\n'
            f'EXPLORATION COMPLETE\n'
            f'{"=" * 60}\n'
            f'Duration: {elapsed:.1f}s\n'
            f'Frontiers explored: {len(self.targets_visited)}\n'
            f'Goals sent: {self.goals_reached}\n'
            f'Blacklisted: {len(self.blacklisted)}\n'
            f'Debug log: {LOG_FILE}\n'
            f'{"=" * 60}\n'
            f'Save the map:\n'
            f'  ros2 run nav2_map_server map_saver_cli -f my_map '
            f'--ros-args -p use_sim_time:=true\n'
            f'{"=" * 60}')
        raise SystemExit(0)


def main():
    parser = argparse.ArgumentParser(description='Frontier-based exploration')
    parser.add_argument('--speed', type=float, default=0.18,
                        help='Forward speed m/s (default: 0.18)')
    parser.add_argument('--duration', type=float, default=0,
                        help='Max duration in seconds, 0=unlimited')
    parser.add_argument('--min-frontier-size', type=float, default=0.3,
                        help='Min frontier size in meters (default: 0.3)')
    args = parser.parse_args()

    rclpy.init()
    node = FrontierExplorer(args)

    import signal
    signal.signal(signal.SIGINT, lambda *_: setattr(node, 'duration', -1))

    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    finally:
        node.stop_robot()
        if not node._log_file.closed:
            node._log('SHUTDOWN', 'Process terminating')
            node._log_file.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
