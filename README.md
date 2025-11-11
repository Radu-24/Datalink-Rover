# Datalink Rover

Datalink Rover represents a sophisticated advancement in autonomous tracked vehicle design, integrating cutting-edge hardware and software solutions. This project is engineered for versatility, encompassing capabilities such as autonomous navigation, manual control, and precision docking. Its modular architecture is designed to support advanced telemetry, real-time video streaming, and future enhancements, including the integration of a robotic arm.

## Key Features
- **Tracked Mobility**: Implements durable plastic tracks with adjustable, tank-style suspension to optimize traction and stability across diverse terrains.
- **360° Camera System**: Employs a high-resolution rotating camera mounted on a servo or stepper motor, ensuring seamless and controlled rotational movement.
- **FPV Camera**: Features a fixed front-facing camera for immersive first-person navigation.
- **Obstacle Detection and Avoidance**: Utilizes ultrasonic sensors with a broad field of view (120°–160°) to ensure reliable environmental awareness.
- **Driving Modes**:
  - *Autonomous Mode*: Enables the vehicle to dynamically follow the remote control while avoiding static and dynamic obstacles.
  - *Manual Override*: Grants full user control, with real-time safety features enabled.
  - *Docking Mode*: Automatically aligns and connects to a charging station with precision guidance.
- **Remote Control Interface**: Includes an F1-inspired wheel design featuring:
  - Dual joysticks for vehicle and camera control.
  - Button-based telemetry and camera feed toggling.
  - Comprehensive real-time telemetry display.
- **Telemetry Features**:
  - A primary display for the 360° camera feed, complemented by FPV in a picture-in-picture (PIP) layout.
  - Advanced sensor visualization mimicking automotive reversing systems, with animated proximity alerts.
  - Battery level monitoring for both the vehicle and the remote control.

## Hardware Specifications
- **Microcontrollers**:
  - Raspberry Pi: Serves as the central processing unit for AI tasks and high-level operations.
  - Arduino: Manages low-level motor control and sensor input.
- **Sensors**:
  - Ultrasonic sensors designed for efficient obstacle detection.
- **Motors**:
  - DC or brushless motors, selected for their precision and proportional speed control.
  - Servo or stepper motors for controlled 360° camera rotation.
- **Power Supply**:
  - Single or dual LiPo batteries with integrated telemetry systems to monitor power status.
- **Chassis Design**:
  - Combines an aluminium base with modular 3D-printed components, providing sufficient space for future expansions, such as robotic arms.

## Software Framework
- **Programming Languages**:
  - C++: Primary language for control systems and hardware integration.
  - Python: Planned for AI and advanced telemetry processing.
- **UWB Integration**:
  - Facilitates precise tracking of the remote and docking station, even through physical obstructions.
- **AI Integration**:
  - (Planned for Version 2) Implements localized AI for object detection, navigation, and task execution on the Raspberry Pi.

## Initial Setup
1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/Datalink-Rover.git
   ```
2. Install dependencies:
   - For Python: Install required libraries listed in `requirements.txt`.
   - For Arduino: Upload control scripts available in the `/arduino` directory.
3. Assemble hardware:
   - Construct the chassis and mount all components.
   - Connect the power supply and verify individual subsystems.
4. Execute software:
   - Launch the main Raspberry Pi script to enable telemetry and remote communication.

## Roadmap for Future Enhancements
- Development of a robotic arm for object manipulation tasks.
- Deployment of AI-driven capabilities for advanced object recognition and task automation.
- Expansion of autonomous functionalities to handle more dynamic and complex environments.

## License
This project is distributed under the MIT License. Refer to the `LICENSE` file for additional details.

---
We welcome contributions from the community! Please submit issues or pull requests to support the ongoing development of PathFinder360.


