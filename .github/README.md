# Hazardous MDV

## Assignment

- Student: Minh-Triet Nguyen-Ta \<<104993913@student.swin.edu.au>\>
- School: Swinburne University of Technology @ Hawthorn
- Unit: SWE30011 IoT Programming
- Date: 2025, April 09 - April 25

## Project idea

Create an IoT-based system that measure the amount of hazardous gases in the air, detect leakage and ventilate into safe containment. Such system is to be installed at industrial sites such as such as factories, waste water treatment facilities, mines, and power plants.

## Project Implementation

- Physical layer
  - Actuators: Red LED, Buzzer Module, 80mm Silent Hydrodynamic Bearing Case Fan
  - Sensors: MQ-2, MQ-4, MQ-7, DS18B20
  - Controller: Duinotech UNO r3 Main Board with Wi-Fi
    - Arduino C++ (OneWire, TimerOne)
    - Source code: [physical-layer](../physical-layer)
- Edge server
  - Hardware: Simulated Raspberry Pi on Dell Laptop
  - Software: Raspberry Pi OS on VirtualBox
  - Database: SQLite
  - ETL Pipeline:
    - Python (pyserial, pysqlite)
    - Source code: [edge-etl-pipeline](../edge-etl-pipeline)
  - Web Application
