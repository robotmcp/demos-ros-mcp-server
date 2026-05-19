---
name: ros-object-navigation
description: Navigate a ROS 2 / Gazebo robot to objects remembered in a semantic memory database. Use when the user asks Codex to go to, get near, inspect, view, or drive to a named object such as a microwave, potted plant, box, ball, couch, refrigerator, or other semantic-memory object in the ROS-MCP VLA Gazebo demo. Applies to tasks involving semantic_memory.sqlite3, /semantic_nav/go_to_object, /goal_pose, Nav2 /navigate_to_pose status, costmap/doorway blocking, and camera verification after navigation.
---

# ROS Object Navigation

Use this workflow to move a ROS 2 / Gazebo robot toward a named object from semantic memory with the fewest reliable calls.

## Fast Path

1. Query semantic memory for the object and aliases.

```bash
sqlite3 -header -table semantic_memory.sqlite3 \
  "SELECT id,label,aliases_json,confidence,x,y,yaw,pose_json,description FROM objects WHERE label_normalized='<object>' OR aliases_json LIKE '%<object>%' ORDER BY confidence DESC LIMIT 5;"
```

2. Prefer the high-level semantic navigation topic first.

Use `/semantic_nav/go_to_object` with `std_msgs/msg/String` and the user-facing object name, for example `microwave` or `potted plant`.

3. Verify movement quickly.

Check `/navigate_to_pose` status and `/odom`. If odom does not change and no new Nav2 goal appears, do not keep waiting. Fall back to a direct reachable pose.

4. Capture the camera only after the robot has stopped or is near the target.

Use `/camera/image` with `expects_image=true`, then analyze the saved image if needed.

## Direct Pose Fallback

Semantic DB coordinates may represent an object pose, an observation pose, or a scene/view pose depending on the writer. Treat exact object coordinates as hints, not guaranteed reachable goals.

If semantic-nav does not create a useful goal:

1. Read `pose_json` for the best matching object.
2. Try the stored pose only if it looks like a reachable observation pose.
3. If the exact pose aborts, compute a standoff pose roughly 0.75-1.25 m away from the target along the opposite of the stored yaw direction:

```text
standoff_x = x - distance * cos(yaw)
standoff_y = y - distance * sin(yaw)
orientation = stored orientation, or face toward the object
```

4. Publish the standoff as `geometry_msgs/msg/PoseStamped` on `/goal_pose` in `map` frame.

For the known microwave example in this demo, semantic memory stored approximately:

```text
microwave: x=6.397, y=6.016, yaw=1.457
```

The exact pose aborted. A closer useful standoff attempt was around:

```text
x=6.283, y=5.022
```

This may still be blocked if the doorway or costmap is red/occupied.

## Doorway And Costmap Caveat

If Nav2 accepts a goal but the robot stalls, spins in place, or barely changes odom, suspect costmap or doorway blockage. Do not repeatedly send farther goals into the blocked area.

Useful checks:

- `/global_costmap/costmap`
- `/local_costmap/costmap`
- `/plan`
- `/odom`
- `/camera/image`

If the costmap is complete red near the doorway, report that navigation is blocked and prefer stopping rather than forcing motion.

## Stop Handling

If a navigation goal is stuck:

1. Cancel the active `/navigate_to_pose` goal if the goal id is available.
2. If cancel is slow or status still reports executing, publish a hold/current pose goal to `/goal_pose`.
3. Publish zero `geometry_msgs/msg/Twist` on `/cmd_vel` only as a final stop signal; Nav2 may overwrite it while an action is active.
4. Verify `/odom` twist is zero before saying the robot is stopped.

## Minimal Command Pattern

For future object requests, use this sequence:

1. DB lookup for object name and pose.
2. Publish object name to `/semantic_nav/go_to_object`.
3. Check Nav2 status plus one odom sample.
4. If no movement, publish one standoff `/goal_pose`.
5. Wait for success/abort or obvious stall.
6. Capture camera image.
7. Stop or hold if stuck.
