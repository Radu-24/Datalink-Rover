# DataLink Rover Simulation (Gym-Style)

A modular, top-down 2D rover simulation environment built with Pygame. Designed as a Reinforcement Learning (RL) environment for autonomous docking tasks.

## Features
- **Procedural Generation:** Random rooms, obstacles, and dock placement with connectivity checks.
- **Gym API:** `reset()`, `step()`, `get_observation()` interface ready for RL agents.
- **Sensor Suite:** - 360° LiDAR
  - ParkPilot Proximity Sensors (Visualized as colored arcs)
  - UWB/BLE Radio Beacon (Range + Bearing with noise)
  - IR Alignment Sensor (Short range)
- **Visuals:** Vector-based UI, HUD, and debugging tools.

## Setup
1. Install Python 3.10+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt