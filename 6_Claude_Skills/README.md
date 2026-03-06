# Example 6: Claude Skills for ROS-MCP Server

This example demonstrates how to use **Claude Code Skills** with the **ROS-MCP Server** to create reusable, structured workflows for controlling ROS 2 robots. It is split into two parts:

- **Part 1** — Using a standalone ROS-MCP Skill with Claude Code
- **Part 2** — Using hierarchical Sub-Skills within the ROS-MCP Skill (e.g., Gazebo simulation sub-skill)

## Video Tutorials

| Part | Video |
|------|-------|
| Part 1: ROS-MCP Skill | [YouTube - Part 1](https://youtu.be/WX8H3orJglo) |
| Part 2: Sub-Skills (Gazebo) | [YouTube - Part 2](https://youtu.be/__hTRRwC0P0) |

## Why Skills?

### The Problem

When using the ROS-MCP Server with Claude Code, the LLM has access to all MCP tools (topics, services, actions, parameters, etc.) but lacks **domain-specific context**. Every session, you end up re-explaining:

- Which topics your robot uses
- How to launch simulations
- What message types to use
- The correct startup sequence
- Troubleshooting steps for common issues

This wastes tokens, time, and leads to inconsistent behavior across sessions.

### The Solution: Skills

**Claude Code Skills** are `.md` files that contain workflow instructions, commands, and reference material. When a skill is activated, its content is loaded into the LLM's context as the **primary reference** — the LLM then follows the instructions defined in the skill rather than guessing.

### Skills vs MCP — What's the Difference?

| | Skills | MCP |
|---|---|---|
| **Format** | Markdown documents containing instructions | Python/JS functions exposed as tools |
| **Context loading** | Skill descriptions are loaded into memory as the primary reference | Tool descriptions are loaded into context during use |
| **LLM behavior** | LLM **follows the instructions** provided in the skill | LLM is the **orchestrator** and decides which tools to call and how |

**Key insight**: Skills and MCP are **complementary**. Skills provide the *what* and *when* (workflows, sequences, domain knowledge), while MCP provides the *how* (tools to execute actions). Together, they give the LLM both the toolbox and the instruction manual.

### Benefits of ROS-MCP + Skills

- **Define workflows** — Step-by-step procedures for common tasks (launch simulation, connect, verify, control)
- **Automate manual tasks** — No more repeating setup instructions each session
- **Reduce token usage** — Reference files are loaded only when needed, not the entire knowledge base
- **Build custom workflows** — Create sub-skills for specific simulators, robots, or environments
- **Hierarchical organization** — Sub-skills for Gazebo, NVIDIA Isaac Sim, specific robot models, etc.

## Skill Structure

The ROS-MCP Skill is installed at `~/.claude/skills/` and has the following structure:

```
ros-mcp-skill/
├── SKILL.md                          # Main skill entry point
├── reference/
│   ├── installation.md               # Setup & install instructions
│   ├── openclaw-setup.sh             # OpenClaw gateway fix script
│   ├── ROS_MCP_REFERENCE_PROMPT.md   # Complete tool reference
│   ├── tools.md                      # Tool reference & examples
│   ├── troubleshooting.md            # Common issues & fixes
│   └── workflows.md                  # Reusable workflow patterns
└── sub-skills/
    └── gazebo/                       # Gazebo simulation sub-skill
        ├── SKILL.md                  # Gazebo-specific instructions
        ├── reference/
        │   ├── ros-gz-bridge.md      # Bridge configuration
        │   ├── setup.md              # Gazebo setup guide
        │   └── troubleshooting.md    # Gazebo-specific issues
        └── sub-skills/
            └── tugbot/               # TugBot demo sub-skill
                ├── SKILL.md          # TugBot-specific instructions
                └── reference/
                    ├── setup.md      # TugBot setup
                    ├── topics.md     # TugBot topics & bridge config
                    └── workflows.md  # TugBot control workflows
```

Each `SKILL.md` file contains:
- A **YAML frontmatter** with the skill name and trigger description
- **Architecture diagrams** showing the communication flow
- **Quick reference tables** linking to detailed reference files
- **Setup procedures**, control commands, and troubleshooting guides

## Part 1: Using the ROS-MCP Skill

### What It Does

The main `ros-mcp-skill` provides Claude Code with complete knowledge of the ROS-MCP Server: how to connect to robots, discover topics/services/actions, send commands, read sensor data, and troubleshoot common issues.

### Installation

1. Copy the `ros-mcp-skill/` directory into your Claude Code skills folder:

```bash
mkdir -p ~/.claude/skills
cp -r ros-mcp-skill ~/.claude/skills/
```

2. Ensure the ROS-MCP Server is configured as an MCP server in Claude Code:

```bash
# If installed via pip
claude mcp add-json "ros-mcp-server" '{"command":"ros-mcp","args":[]}'
```

3. Start rosbridge on your robot or simulation machine:

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

### How It Works

When you invoke the skill (e.g., by asking Claude to control a robot), Claude Code:

1. Loads the `SKILL.md` and its reference files into context
2. Follows the defined **connection workflow**: connect → discover → explore → interact
3. Uses the correct message types, topic names, and tool sequences
4. Applies best practices (discover before acting, safe velocities, verify data flow)

### Example Usage

Once the skill is installed and the ROS-MCP Server is running, simply ask Claude Code:

> "Connect to my robot and list all available topics"

> "Move the turtlesim turtle forward and then draw a square"

> "Read the LIDAR scan data and tell me if there are obstacles nearby"

Claude will follow the skill's workflow instructions, using the MCP tools in the correct sequence.

## Part 2: Sub-Skills (Gazebo Example)

### What Are Sub-Skills?

Sub-skills are **nested skills** that provide specialized knowledge for a specific domain. They inherit the parent skill's context and add domain-specific instructions.

The ROS-MCP Skill includes a **Gazebo sub-skill** as a reference implementation, which in turn contains a **TugBot sub-skill** for a specific robot demo.

### Hierarchy

```
ros-mcp-skill (main)
  └── gazebo (sub-skill)          — How to run Gazebo simulations with ROS-MCP
        └── tugbot (sub-skill)    — Specific TugBot warehouse demo
```

### Gazebo Sub-Skill

The Gazebo sub-skill teaches Claude how to:

- Launch Gazebo simulations
- Set up the **ros-gz-bridge** (translates Gazebo transport ↔ ROS 2 topics)
- Start **rosbridge** for MCP communication
- Handle the two-bridge architecture:

```
AI Client → ros-mcp-server → rosbridge → ros-gz-bridge → Gazebo Simulation
```

### TugBot Sub-Skill

The TugBot sub-skill is a complete end-to-end example:

- Launches Ignition Gazebo Fortress with a warehouse world
- Configures bridges for `/cmd_vel`, `/odom`, `/scan`, `/tf`, `/clock`
- Provides velocity control commands, sensor reading patterns, and demo workflows (e.g., drive a square)

### Creating Your Own Sub-Skills

The Gazebo sub-skill is just one example. You can create sub-skills for any simulator or robot platform. For example:

**NVIDIA Isaac Sim sub-skill** — Could include:
- Isaac Sim launch procedures
- ROS 2 bridge configuration for Isaac Sim
- Specific robot models available in Isaac Sim
- Isaac Sim-specific troubleshooting

**Custom robot sub-skill** — Could include:
- Robot-specific topic names and message types
- Calibration and startup procedures
- Safety limits and emergency stop workflows

To create a new sub-skill:

1. Create a directory under `sub-skills/` in the parent skill:
   ```
   ros-mcp-skill/sub-skills/your-simulator/
   ├── SKILL.md
   ├── reference/
   │   └── (your reference files)
   └── sub-skills/       # Optional: further nesting
   ```

2. Write a `SKILL.md` with YAML frontmatter:
   ```yaml
   ---
   name: your-skill-name
   description: >
     When to trigger this skill and what it does.
   ---
   ```

3. Add reference files for setup, troubleshooting, topic mappings, etc.

4. Register it in the parent skill's `SKILL.md` sub-skills table.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Claude Code + Skills                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ ros-mcp-skill│  │ gazebo       │  │ tugbot               │  │
│  │ (SKILL.md)   │→ │ (sub-skill)  │→ │ (sub-sub-skill)      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│         Workflows, references, domain knowledge                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │ Uses MCP tools
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ROS-MCP Server                               │
│              (connect, publish, subscribe, call_service, ...)    │
└─────────────────────────────┬───────────────────────────────────┘
                              │ WebSocket (port 9090)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    rosbridge_server                               │
└─────────────────────────────┬───────────────────────────────────┘
                              │ ROS 2 DDS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Robot / Simulation (Gazebo, Isaac Sim, etc.)         │
└─────────────────────────────────────────────────────────────────┘
```

## Tested On

- **OS:** Ubuntu 22.04 LTS
- **ROS Distro:** ROS 2 Humble
- **Simulator:** Ignition Gazebo Fortress (for Gazebo sub-skill demo)
- **Claude Code:** With ROS-MCP Server MCP integration

## Prerequisites

- [ROS 2](https://docs.ros.org/en/humble/Installation.html) (Humble/Iron/Jazzy)
- [rosbridge_server](https://github.com/RobotWebTools/rosbridge_suite) (`sudo apt install ros-$ROS_DISTRO-rosbridge-server`)
- [ros-mcp-server](https://github.com/robotmcp/ros-mcp-server) (`pip install ros-mcp-server`)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI

For the Gazebo sub-skill demo:
- Ignition Gazebo Fortress (`sudo apt install ros-$ROS_DISTRO-ros-gz`)
- `rosapi` package (`sudo apt install ros-$ROS_DISTRO-rosapi`)

## File Structure

```
6_Claude_Skills/
├── README.md                                    # This file
├── Claude Skills (ROS-MCP) Presentation.pdf     # Presentation slides
└── ros-mcp-skill/                               # The skill to install
    ├── .claude/settings.local.json              # Claude Code permissions
    ├── SKILL.md                                 # Main skill definition
    ├── reference/                               # Reference documents
    └── sub-skills/
        └── gazebo/                              # Gazebo sub-skill
            ├── .claude/settings.local.json
            ├── SKILL.md
            ├── reference/
            └── sub-skills/
                └── tugbot/                      # TugBot sub-skill
                    ├── SKILL.md
                    └── reference/
```

## License

This project is licensed under the BSD 3-Clause License — see the [LICENSE](../LICENSE) file in the repository root for details.
