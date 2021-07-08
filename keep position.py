from moteus_fdcan_adapter import Controller
from moteus_fdcan_adapter import MoteusReg
import time
import math
from kinematics_3D import Kinematics

def main():
    c = Controller(controller_ID = 1)
    pos  = 0
    while True:
        pos=pos+0.0003
        c.set_position(position = 0, max_torque=3, kp_scale=1, kd_scale=0.8)


if __name__ == '__main__':
    main()