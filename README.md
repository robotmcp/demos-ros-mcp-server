# ROS MCP Server Demos
This repository is a collection of demos and tutorials on connecting AI LLMs to Robots using https://github.com/robotmcp/ros-mcp-server

# In this Repository
Each sub-folder in this repository can be treated as a standalone project with its own readme and pyproject.toml file. Below is a list of demos along with a brief description of each.


### 1: TugBot Simulation in Gazebo

This example demonstrates how to control a **Tugbot mobile robot** inside a warehouse environment using **Ignition Gazebo (Fortress)**.

Using natural language and the `ROS-MCP server`, you can dictatate movement commands (navigation), inspect sensor data (Lidar), and check the robot's position.

[View Example 1](./1_Gazebo_Tugbot/README.md)

[Usage and Installation Video](https://youtu.be/rnea0zybCBo)

--- 

### 2. Unitree Go2 Simulation using CHAMP inside Gazebo

This example demonstrates how to control a **Unitree Go2 Quadruped Robot** inside a physics simulation using **Ignition Gazebo (Fortress)**.

It leverages the **CHAMP** quadruple controller to manage complex gait and posture. Using natural language, you can control the robot's walking velocity, execute turns, and manage its stance, as well as inspect sensors like Lidar and IMU.

[View Example 2](./2_UnitreeGo2_simulation/README.md)


[Usage and Installation Video](https://youtu.be/6EQpNAicpiI)

---

### 3. PX4 Drone Control (Gazebo Sim & Real Robot)

This example demonstrates how to control a **PX4-based drone** using the `ROS-MCP server` with custom ROS 2 Actions via **MAVROS**. It includes both a **Gazebo simulation** and a **real robot** setup. Using natural language, you can command takeoff, fly trajectory patterns, orbit, and return to launch.

[View Example 3 - Gazebo Sim](./3_Drone_PX4/gazebo_sim/README.md) | [View Example 3 - Real Robot](./3_Drone_PX4/real_robot/README.md)

[Sim Demo Video](https://www.youtube.com/watch?v=qVNO6Emfp_w) | [Real Robot Demo Video](https://www.youtube.com/watch?v=TRhr7QfWoTI)

---

### 4. TurtleBot3 Simulation in Ignition Gazebo

This example demonstrates how to simulate a **TurtleBot3** robot in **Ignition Gazebo (Fortress)** with ROS 2. It supports multiple robot models (Burger, Waffle, Waffle Pi) and several pre-configured worlds. Using natural language and the `ROS-MCP server`, you can control the robot's movement, read sensor data (Lidar, IMU, Odometry), and inspect system state.

[View Example 4](./4_turtlebot_ignition/README.md)

[Usage and Installation Video](https://youtu.be/CXA4HDUVAnM)

---
