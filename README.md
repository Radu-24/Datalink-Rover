# DataLink Rover

DataLink Rover is a multi-component robotics platform built around Raspberry Pi devices, a custom Windows control application, and a self-contained wireless network.  
The project includes a remote controller unit, a rover (car) unit, a docking station, and a Windows application for real-time monitoring and network configuration.

---

# Project Overview

The system consists of three primary Raspberry Pi components:

- **rpiremote** – the central controller, hosting the access point and coordinating communication  
- **rpicar** – the rover unit, responsible for movement, sensors, cameras, and telemetry  
- **rpidock** – the docking station unit, a static reference point for alignment and charging logic  

Additionally, there is a Windows application:

- **Pi Monitor** – a desktop tool for viewing rover data and automatically configuring Ethernet for direct communication with the network

These components work together to form a self-contained command, control, and telemetry system.

---

# System Architecture

## Remote – rpiremote

### Purpose
The remote is the core of the DataLink Rover network.  
It acts as the Wi-Fi access point, communication hub, and telemetry gateway.

### Responsibilities
- Hosts the wireless AP (such as “datalinkrover”)  
- Communicates with both rover and dock  
- Provides SSH access to all Pi units  
- Acts as the entry point for the Windows control application  

### Typical Hardware
- Raspberry Pi 5  
- USB-C to Ethernet adapter  
- Raspberry Pi OS Lite  
- SSH enabled

---

## Rover – rpicar

### Purpose
The rover is the mobile unit responsible for movement, sensors, and camera systems.

### Responsibilities
- Motor control and drive train logic  
- Obstacle detection and sensor processing  
- FPV camera streaming and 360° camera rotation  
- Reporting telemetry (CPU, temperature, sensors, battery, etc.)  
- Navigation and autonomous guidance (future)

### Typical Hardware
- Raspberry Pi 4 or 5  
- Motor driver or ESCs  
- LiPo power system  
- FPV camera module  
- Optional rotating top-mounted camera  
- Ultrasonic sensors or LiDAR  
- Optional UWB positioning module

---

## Docking Station – rpidock

### Purpose
A stationary Raspberry Pi that acts as a reference point for docking, guidance, and charging alignment.

### Responsibilities
- Provides a known fixed location on the network  
- Assists rover alignment (IR/UWB planned)  
- Supports docking workflow  
- Handles charging logic (future)

### Typical Hardware
- Raspberry Pi Zero 2 W  
- IR/UWB module (for alignment assistance)  
- Charging interface (future)

---

# Windows Application – Pi Monitor

The Pi Monitor is a Windows desktop application used for controlling Ethernet configuration and monitoring telemetry.

### Current Features
- Displays randomized telemetry for UI testing  
- Smooth animated CPU/GPU dials  
- Temperature and storage bars  
- Start Rover Link button which:  
  - Automatically configures Ethernet static IP  
  - Sets required interface metrics  
  - Prepares the PC for a direct link to the Raspberry Pi network  
- Admin elevation workflow  
- PyInstaller-built single-file executable  
- Custom app icon  
- Start Menu installation support

### Planned Features
- Real telemetry from all Raspberry Pi devices  
- Rover camera feed display  
- Online/offline detection  
- Sensor data integration  
- Docking status  
- Settings and preferences panel  
- Rover control interface  
- Map or environmental positioning overview  

---

# Repository Structure (Simplified)

```
Datalink-Rover/
  apps/
    pi-monitor/
      main.py
      netconfig.py
      ui/
        bars.py
        dials.py
      icon.ico
  remote/
    (project files for rpiremote)
  car/
    (project files for rpicar)
  dock/
    (project files for rpidock)
  docs/
    (documentation)
```

Temporary build folders, virtual environments, and generated executables are excluded using `.gitignore`.

---

# Build and Installation

## Pi Monitor
The Windows application is built with PyInstaller:

```
pyinstaller --noconfirm --onefile --windowed --icon=icon.ico main.py
```

The resulting executable is placed in:

```
dist/DataLinkRover_PiMonitor.exe
```

It can optionally be installed to:

```
C:\Program Files\DataLink Rover\Pi Monitor\
```

A Start Menu shortcut may be created manually.

---

# Rover Simulation – DataLink Sim

DataLink Sim is a standalone Python simulation environment designed to train Reinforcement Learning (RL) agents for autonomous docking and navigation without risking physical hardware.

### Purpose
To provide a rapid, safe, and accurate training ground for the rover's AI. It replicates the physics, kinematics, and sensor suite of the real rover, allowing the AI to learn "Return-To-Home" (RTH) logic via trial and error.

### Key Features
- **Physics Engine:** Simulates 2D rover dynamics, friction, collisions, and charging pin contact logic.
- **Sensor Suite:** Replicates real-world sensors including LiDAR, Ultrasonic (Proximity), Infrared (IR) alignment beams, and UWB distance.
- **AI Training Mode:** A dedicated high-speed loop that locks user input and creates instant-reset scenarios for efficient neural network training.
- **Procedural Generation:** Generates random maps with variable difficulty (Easy, Medium, Hard) to ensure robust AI learning.
- **Safety Assist:** Includes a "ParkPilot" system for Manual mode that automatically slows or stops the rover to prevent collisions.

**Controls:** `WASD` for movement, `SPACE` for brake.

---

# Future Work

- Full telemetry pipeline  
- Integration of real rover sensors and camera feeds  
- Rover control panel (manual and autonomous modes)  
- Docking station alignment logic  
- Local AI modules for object recognition and navigation  
- Custom web or mobile interface  

---

# License

All rights reserved.  
No part of this project may be copied, modified, distributed, or used without explicit permission from the author.


