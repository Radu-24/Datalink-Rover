import numpy as np
from sensors.lidar import Lidar
from sensors.proximity import ProximitySensor
from sensors.uwb_ble import UWBBeacon
from sensors.ir import IRSensor
from sensors.rear_docking import RearDockingSystem

class SensorSuite:
    def __init__(self, rover):
        self.lidar = Lidar(rover)
        self.prox = ProximitySensor(rover)
        self.uwb = UWBBeacon(rover)
        self.ir = IRSensor(rover)
        self.rear = RearDockingSystem(rover)
        
    def update(self, obstacles, dock):
        self.lidar.update(obstacles)
        self.prox.update(obstacles)
        self.uwb.update(obstacles, dock)
        self.ir.update(dock, obstacles)
        self.rear.update(obstacles, dock)
        
    def get_normalized_array(self):
        l_data = self.lidar.get_data()
        p_data = self.prox.get_data()
        u_data = self.uwb.get_data()
        i_data = self.ir.get_data()
        r_data = self.rear.get_data()
        
        return np.concatenate([l_data, p_data, u_data, i_data, r_data])