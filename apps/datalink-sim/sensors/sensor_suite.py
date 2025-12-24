import numpy as np
from sensors.lidar import Lidar
from sensors.proximity import ProximitySensor
from sensors.uwb_ble import UWBBeacon
from sensors.ir import IRSensor

class SensorSuite:
    def __init__(self, rover):
        self.lidar = Lidar(rover)
        self.prox = ProximitySensor(rover)
        self.uwb = UWBBeacon(rover)
        self.ir = IRSensor(rover)
        
    def update(self, obstacles, dock):
        self.lidar.update(obstacles)
        self.prox.update(obstacles)
        self.uwb.update(obstacles, dock)
        
        # Pass obstacles to IR for Occlusion check
        self.ir.update(dock, obstacles)
        
    def get_normalized_array(self):
        l_data = self.lidar.get_data()
        p_data = self.prox.get_data()
        u_data = self.uwb.get_data()
        i_data = self.ir.get_data()
        
        return np.concatenate([l_data, p_data, u_data, i_data])