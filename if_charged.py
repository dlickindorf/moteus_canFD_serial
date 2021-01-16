from moteus_fdcan_adapter import Controller
from moteus_fdcan_adapter import MoteusReg
import time
import math
from kinematics_3D import Kinematics


def main():
    controller_knee = Controller(controller_ID = 1)
    controller_hip = Controller(controller_ID = 2)
    controller_abad = Controller(controller_ID=3)

    response_data_knee = controller_knee.get_data()
    response_data_hip = controller_hip.get_data()
    response_data_abad = controller_abad.get_data()
    voltage =(response_data_knee[MoteusReg.MOTEUS_REG_V]+response_data_hip[MoteusReg.MOTEUS_REG_V]+response_data_abad[MoteusReg.MOTEUS_REG_V])/6
    percentage =  (voltage - 3.2*8)/(8*(4.2-3.2))
    print(percentage)

if __name__ == '__main__':
    main()